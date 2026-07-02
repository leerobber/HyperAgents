"""HyperScheduler — orchestrates genome evolution and task dispatch via the kernel."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from sovereign_core_rs import KernelBlock, SemanticWord

from hyper.genome import AgentGenome, GenomeRegistry
from hyper.kernel_bridge import KernelBridge

try:
    from sovereign_gpu import GpuGraph
    _HAS_GPU = True
except ImportError:
    GpuGraph = None  # type: ignore[assignment,misc]
    _HAS_GPU = False

try:
    from dgm_rs import DgmRuntime as _DgmRuntime
    _HAS_DGM = True
except ImportError:
    _DgmRuntime = None  # type: ignore[assignment,misc,type-arg]
    _HAS_DGM = False

# Graph intents routed to GPU when genome.gpu_enabled + gpu_prefer_graph
_GPU_GRAPH_INTENTS: frozenset[int] = frozenset({41, 43, 44, 45})


@dataclass
class TaskResult:
    genome_id: int
    agent_id: int
    task_id: int
    duration_ms: float
    output_words: list[int]
    fitness_delta: float


class HyperScheduler:
    """
    Manages genomes and dispatches tasks through the sovereign-core-rs kernel.

    Flow:
        1. GenomeRegistry holds candidate genomes.
        2. Scheduler spawns one kernel agent per genome.
        3. Each genome gets a KernelBlock dispatched (→ WASM agent).
        4. Output SemanticWords are scored by a fitness function.
        5. Fitness scores update genomes; next generation is bred.

    GPU path (optional):
        If a GpuGraph is provided and the genome has gpu_enabled=True and
        gpu_prefer_graph=True, graph intents (41/43/44/45) are routed to
        the GPU engine instead of the WASM/Rust path.
    """

    def __init__(
        self,
        registry: GenomeRegistry,
        bridge: KernelBridge,
        fitness_fn: Optional[Callable[[list[int]], float]] = None,
        gpu_graph: Optional["GpuGraph"] = None,  # type: ignore[type-arg]
    ) -> None:
        self.registry = registry
        self.bridge = bridge
        self._fitness_fn = fitness_fn or _default_fitness
        self._genome_agents: dict[int, int] = {}  # genome_id → kernel agent_id
        self._task_counter = 0
        self.gpu: Optional["GpuGraph"] = gpu_graph  # type: ignore[type-arg]
        # DgmRuntime for lazy GpuGraph construction; populated via load_dgm_graph()
        self._dgm: Optional["_DgmRuntime"] = None  # type: ignore[type-arg]

    def load_dgm_graph(self, dgm: "_DgmRuntime") -> None:  # type: ignore[type-arg]
        """Build (or replace) the GpuGraph from a DgmRuntime's current graph state."""
        if not _HAS_GPU:
            return
        n, edges = dgm.to_gpu_edges()
        self.gpu = GpuGraph(n, edges)
        self._dgm = dgm

    def start(self) -> None:
        self.bridge.start()
        for genome in self.registry.all():
            self._spawn_for_genome(genome)

    def _spawn_for_genome(self, genome: AgentGenome) -> int:
        agent_id = self.bridge.spawn_agent(genome.genome_id)
        self._genome_agents[genome.genome_id] = agent_id
        return agent_id

    def run_task(
        self,
        genome_id: int,
        intent: int = 2,  # PLAN
        priority: int = 128,
        confidence: float = 1.0,
        payload_ref: int = 0,
    ) -> TaskResult:
        genome = self.registry.get(genome_id)
        if genome is None:
            raise KeyError(f"genome {genome_id} not in registry")

        self._task_counter += 1
        task_id = self._task_counter

        # GPU graph path — bypass WASM/Rust when conditions met
        if (
            self.gpu is not None
            and genome.gpu_enabled
            and genome.gpu_prefer_graph
            and intent in _GPU_GRAPH_INTENTS
        ):
            return self._run_gpu_graph_task(
                genome=genome,
                intent=intent,
                payload_ref=payload_ref,
                creds_token=genome.to_creds_token(),
                task_id=task_id,
            )

        # ── Existing WASM / Rust path ─────────────────────────────────────────
        agent_id = self._genome_agents.get(genome_id)
        if agent_id is None:
            agent_id = self._spawn_for_genome(genome)

        word = self.bridge.make_word(
            type_=1,
            intent=intent,
            priority=priority,
            confidence=confidence,
            payload_ref=payload_ref,
        )

        t0 = time.perf_counter()
        result_blocks = self.bridge.dispatch_block(
            agent_id=agent_id,
            genome_id=genome_id,
            creds_token=genome.to_creds_token(),
            task_id=task_id,
            words=[word],
            wasm_agent_name=genome.wasm_agent,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        output_words = []
        for block in result_blocks:
            if self.bridge.rust_backend:
                output_words.extend(block.words)
            else:
                output_words.extend(block)

        fitness_delta = self._fitness_fn(output_words)
        genome.fitness += fitness_delta

        return TaskResult(
            genome_id=genome_id,
            agent_id=agent_id,
            task_id=task_id,
            duration_ms=elapsed_ms,
            output_words=output_words,
            fitness_delta=fitness_delta,
        )

    # ── GPU helpers ───────────────────────────────────────────────────────────

    def _run_gpu_graph_task(
        self,
        genome: AgentGenome,
        intent: int,
        payload_ref: int,
        creds_token: int,
        task_id: int,
    ) -> TaskResult:
        t0 = time.perf_counter()

        if intent == 41:    # BFS
            out = self.gpu.bfs(payload_ref)
        elif intent == 43:  # DFS
            out = self.gpu.dfs(payload_ref)
        elif intent == 44:  # SHORTEST PATHS
            out = [n for n, _ in self.gpu.shortest_paths(payload_ref)]
        elif intent == 45:  # TOPO SORT
            out = self.gpu.topo_sort() or []
        else:
            out = []

        elapsed_ms = (time.perf_counter() - t0) * 1000
        fitness_delta = float(len(out))
        genome.fitness += fitness_delta

        block = _wrap_gpu_result(out, genome.genome_id, creds_token, task_id)
        return TaskResult(
            genome_id=genome.genome_id,
            agent_id=0,
            task_id=task_id,
            duration_ms=elapsed_ms,
            output_words=block.words,
            fitness_delta=fitness_delta,
        )

    # ── Evolution ─────────────────────────────────────────────────────────────

    def evolve(self, n_children: int = 5, mutation_rate: float = 0.1) -> list[AgentGenome]:
        """Breed next generation, register them, spawn kernel agents."""
        children = self.registry.next_generation(n=n_children, mutation_rate=mutation_rate)
        for child in children:
            self.registry.register(child)
            self._spawn_for_genome(child)
        return children

    def leaderboard(self) -> list[tuple[int, float]]:
        """Return (genome_id, fitness) sorted by fitness descending."""
        return [(g.genome_id, g.fitness) for g in self.registry.elite(len(self.registry._genomes))]


# ── Module-level GPU result wrapper ──────────────────────────────────────────

def _wrap_gpu_result(
    out_nodes: list[int],
    genome_id: int,
    creds_token: int,
    task_id: int,
) -> KernelBlock:
    word = SemanticWord(
        type_=6,        # RESULT
        intent=50,      # GRAPH_RESULT (GPU)
        channel=0,
        priority=128,
        confidence=60000,
        payload_ref=len(out_nodes) & 0xFFFF,
    ).encode()
    return KernelBlock(
        agent_id=0,
        genome_id=genome_id,
        creds_token=creds_token,
        task_id=task_id,
        words=[word],
        metrics_ref=0,
    )


def _default_fitness(output_words: list[int]) -> float:
    """Score based on count of non-zero output words."""
    return float(len([w for w in output_words if w != 0]))
