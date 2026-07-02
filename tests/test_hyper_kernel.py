"""Tests for HyperAgents kernel integration (genome + scheduler + Rust runtime)."""
import pytest
from pathlib import Path

WASM_DIR = Path(__file__).parent.parent / "wasm_agents"

from hyper.genome import AgentGenome, GenomeRegistry, _next_id
from hyper.kernel_bridge import KernelBridge
from hyper.scheduler import HyperScheduler, TaskResult


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


def test_registry_next_generation():
    reg = GenomeRegistry()
    for _ in range(3):
        g = _make_genome()
        g.fitness = 1.0
        reg.register(g)
    children = reg.next_generation(n=4)
    assert len(children) == 4
    for child in children:
        assert child.generation >= 1


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
