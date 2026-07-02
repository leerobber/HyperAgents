"""Tests for HyperAgents kernel integration (genome + scheduler + Rust runtime)."""
import random
import pytest
from pathlib import Path

WASM_DIR = Path(__file__).parent.parent / "wasm_agents"

from hyper.genome import AgentGenome, GenomeRegistry, crossover, _next_id
from hyper.kernel_bridge import KernelBridge
from hyper.scheduler import HyperScheduler, TaskResult
from sovereign_core_rs import BlockBus, NodeRuntime, KernelBlock, SemanticWord


# ── AgentGenome ──────────────────────────────────────────────────────────────

def _make_genome(name="test") -> AgentGenome:
    return AgentGenome(
        genome_id=_next_id(),
        name=name,
        traits={"plan": 0.8, "critique": 0.6, "build": 0.9},
        wasm_agent="planner_agent",
    )


def test_genome_mutate_returns_new_instance():
    g = _make_genome()
    child = g.mutate(rate=0.1)
    assert child.genome_id != g.genome_id
    assert child.generation == g.generation + 1
    assert child.parent_id == g.genome_id


def test_genome_mutate_clamps_traits():
    g = _make_genome()
    for _ in range(50):
        child = g.mutate(rate=1.0)
        for v in child.traits.values():
            assert 0.0 <= v <= 1.0


def test_genome_crossover():
    g1 = _make_genome("a")
    g2 = _make_genome("b")
    child = g1.crossover(g2)
    assert child.genome_id not in (g1.genome_id, g2.genome_id)
    for k in g1.traits:
        assert k in child.traits


def test_genome_creds_token():
    g = AgentGenome(
        genome_id=_next_id(),
        name="t",
        traits={"plan": 1.0, "critique": 0.0, "build": 1.0},
        wasm_agent="planner_agent",
    )
    tok = g.to_creds_token()
    assert tok & (1 << 0)  # plan bit set
    assert not (tok & (1 << 1))  # critique bit off
    assert tok & (1 << 2)  # build bit set


# ── GenomeRegistry ───────────────────────────────────────────────────────────

def test_registry_register_and_get():
    reg = GenomeRegistry()
    g = _make_genome()
    reg.register(g)
    assert reg.get(g.genome_id) is g


def test_registry_elite_sorted():
    reg = GenomeRegistry()
    for score in [0.5, 0.9, 0.1, 0.7]:
        g = _make_genome()
        g.fitness = score
        reg.register(g)
    elite = reg.elite(2)
    assert elite[0].fitness >= elite[1].fitness


def test_registry_next_generation_legacy():
    """n= API: returns exactly n children, backward compat."""
    reg = GenomeRegistry()
    for _ in range(3):
        g = _make_genome()
        g.fitness = 1.0
        reg.register(g)
    children = reg.next_generation(n=4)
    assert len(children) == 4
    for child in children:
        assert child.generation >= 1


def test_registry_next_generation_new_api():
    """New API: next_generation(elite_count, children_count) returns elites + children."""
    reg = GenomeRegistry()
    for _ in range(4):
        g = _make_genome()
        g.fitness = random.random()
        reg.register(g)
    result = reg.next_generation(elite_count=2, children_count=3)
    assert len(result) == 5                 # 2 elites + 3 children
    for g in result:
        assert isinstance(g, AgentGenome)


# ── KernelBridge ─────────────────────────────────────────────────────────────

@pytest.fixture()
def bridge():
    b = KernelBridge(wasm_dir=WASM_DIR)
    b.start()
    return b


def test_bridge_starts(bridge):
    assert bridge.agent_count() == 0


def test_bridge_spawn(bridge):
    aid = bridge.spawn_agent(genome_id=1)
    assert isinstance(aid, int)
    assert bridge.agent_count() == 1


def test_bridge_make_word(bridge):
    w = bridge.make_word(type_=1, intent=2, priority=200, confidence=0.9)
    assert isinstance(w, int)
    assert w != 0


def test_bridge_dispatch_planner_wasm(bridge):
    aid = bridge.spawn_agent(genome_id=42)
    word = bridge.make_word(intent=2, confidence=0.8)
    results = bridge.dispatch_block(
        agent_id=aid,
        genome_id=42,
        creds_token=0b1111,
        task_id=1,
        words=[word],
        wasm_agent_name="planner_agent",
    )
    assert len(results) >= 1


def test_bridge_rust_backend(bridge):
    assert bridge.rust_backend is True


# ── HyperScheduler ───────────────────────────────────────────────────────────

@pytest.fixture()
def scheduler():
    reg = GenomeRegistry()
    for _ in range(3):
        g = _make_genome()
        g.fitness = 1.0
        reg.register(g)
    bridge = KernelBridge(wasm_dir=WASM_DIR)
    sched = HyperScheduler(registry=reg, bridge=bridge)
    sched.start()
    return sched, reg


def test_scheduler_agents_spawned(scheduler):
    sched, reg = scheduler
    assert sched.bridge.agent_count() == len(reg.all())


def test_scheduler_run_task_returns_result(scheduler):
    sched, reg = scheduler
    genome_id = reg.all()[0].genome_id
    result = sched.run_task(genome_id)
    assert isinstance(result, TaskResult)
    assert result.genome_id == genome_id
    assert result.duration_ms >= 0


def test_scheduler_fitness_accumulates(scheduler):
    sched, reg = scheduler
    g = reg.all()[0]
    initial = g.fitness
    sched.run_task(g.genome_id)
    assert g.fitness >= initial


def test_scheduler_evolve_adds_children(scheduler):
    sched, reg = scheduler
    before = len(reg.all())
    children = sched.evolve(n_children=2)
    assert len(children) == 2
    assert len(reg.all()) == before + 2


def test_scheduler_leaderboard_ordered(scheduler):
    sched, reg = scheduler
    for g in reg.all():
        sched.run_task(g.genome_id)
    board = sched.leaderboard()
    scores = [s for _, s in board]
    assert scores == sorted(scores, reverse=True)


# ── Evolution operators ───────────────────────────────────────────────────────

def test_genome_has_evolution_fields():
    g = _make_genome()
    assert hasattr(g, "temperature")
    assert hasattr(g, "max_tokens")
    assert hasattr(g, "cooperate_level")
    assert hasattr(g, "gpu_enabled")


def test_genome_mutate_evolution_fields():
    g = _make_genome()
    g.temperature = 0.5
    g.max_tokens = 1024
    child = g.mutate(rate=0.1)
    assert 0.0 <= child.temperature <= 1.0
    assert child.max_tokens >= 64
    assert child.generation == g.generation + 1


def test_standalone_crossover():
    g1 = _make_genome("x")
    g2 = _make_genome("y")
    g1.temperature = 0.2
    g2.temperature = 0.8
    child = crossover(g1, g2)
    assert 0.1 < child.temperature < 0.9   # blended
    assert child.genome_id not in (g1.genome_id, g2.genome_id)


def test_genome_add_genome_assigns_id():
    reg = GenomeRegistry()
    g = _make_genome()
    g2 = g.mutate()
    assert g2.genome_id == 0                # not yet registered
    gid = reg.add_genome(g2)
    assert g2.genome_id == gid
    assert gid != 0


# ── BlockBus + NodeRuntime ────────────────────────────────────────────────────

def test_blockbus_publish_consume():
    bus = BlockBus()
    word = SemanticWord(type_=1, intent=2, channel=0, priority=128,
                        confidence=60000, payload_ref=7).encode()
    block = KernelBlock(agent_id=1, genome_id=1, creds_token=0b1111,
                        task_id=1, words=[word], metrics_ref=0)
    bus.publish(block)
    assert bus.size() == 1
    got = bus.consume()
    assert got is not None
    assert got.agent_id == 1
    assert bus.is_empty()


def test_blockbus_fifo():
    bus = BlockBus()
    for i in range(5):
        word = SemanticWord(type_=1, intent=2, channel=0, priority=128,
                            confidence=60000, payload_ref=i).encode()
        bus.publish(KernelBlock(agent_id=i, genome_id=1, creds_token=0b1111,
                                task_id=i, words=[word], metrics_ref=0))
    ids = [bus.consume().agent_id for _ in range(5)]
    assert ids == list(range(5))


def test_node_runtime_step_once():
    bus = BlockBus()
    node = NodeRuntime()
    node.spawn_agent(genome_id=1)
    word = SemanticWord(type_=1, intent=2, channel=0, priority=128,
                        confidence=60000, payload_ref=0).encode()
    bus.publish(KernelBlock(agent_id=1, genome_id=1, creds_token=0b1111,
                            task_id=1, words=[word], metrics_ref=0))
    node.step_once(bus)
    assert bus.size() >= 1              # at least 1 result block put back


def test_node_runtime_shared_bus():
    """Two NodeRuntimes sharing a bus exchange blocks."""
    bus = BlockBus()
    n1 = NodeRuntime()
    n2 = NodeRuntime()
    n1.spawn_agent(genome_id=10)
    n2.spawn_agent(genome_id=20)

    word = SemanticWord(type_=1, intent=2, channel=0, priority=200,
                        confidence=60000, payload_ref=0).encode()
    bus.publish(KernelBlock(agent_id=1, genome_id=10, creds_token=0b1111,
                            task_id=1, words=[word], metrics_ref=0))

    n1.step_once(bus)   # consumes block, produces result block back on bus
    assert not bus.is_empty()
    n2.step_once(bus)   # consumes result
