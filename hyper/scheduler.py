"""HyperScheduler — orchestrates genome evolution and task dispatch via the kernel."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from hyper.genome import AgentGenome, GenomeRegistry
from hyper.kernel_bridge import KernelBridge


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
    """

    def __init__(
        self,
        registry: GenomeRegistry,
        bridge: KernelBridge,
        fitness_fn: Optional[Callable[[list[int]], float]] = None,
    ) -> None:
        self.registry = registry
        self.bridge = bridge
        self._fitness_fn = fitness_fn or _default_fitness
        self._genome_agents: dict[int, int] = {}  # genome_id → kernel agent_id
        self._task_counter = 0

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

        agent_id = self._genome_agents.get(genome_id)
        if agent_id is None:
            agent_id = self._spawn_for_genome(genome)

        self._task_counter += 1
        task_id = self._task_counter

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


def _default_fitness(output_words: list[int]) -> float:
    """Score based on count of non-zero output words."""
    return float(len([w for w in output_words if w != 0]))
