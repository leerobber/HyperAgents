"""AgentGenome and GenomeRegistry — genome management for HyperAgents."""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentGenome:
    """Immutable description of an agent's traits and capabilities."""
    genome_id: int
    name: str
    traits: dict[str, float]          # e.g. {"curiosity": 0.8, "precision": 0.6}
    wasm_agent: str                   # e.g. "planner_agent"
    fitness: float = 0.0
    generation: int = 0
    parent_id: Optional[int] = None

    def mutate(self, rate: float = 0.1) -> "AgentGenome":
        """Return a new genome with Gaussian noise applied to traits."""
        new_traits = {
            k: max(0.0, min(1.0, v + random.gauss(0, rate)))
            for k, v in self.traits.items()
        }
        return AgentGenome(
            genome_id=_next_id(),
            name=f"{self.name}_m{self.generation + 1}",
            traits=new_traits,
            wasm_agent=self.wasm_agent,
            fitness=0.0,
            generation=self.generation + 1,
            parent_id=self.genome_id,
        )

    def crossover(self, other: "AgentGenome") -> "AgentGenome":
        """Single-point crossover on shared trait keys."""
        keys = list(self.traits.keys())
        if not keys:
            return self.mutate()
        split = random.randint(1, len(keys))
        new_traits: dict[str, float] = {}
        for i, k in enumerate(keys):
            new_traits[k] = self.traits[k] if i < split else other.traits.get(k, self.traits[k])
        return AgentGenome(
            genome_id=_next_id(),
            name=f"{self.name}x{other.name}",
            traits=new_traits,
            wasm_agent=self.wasm_agent,
            fitness=0.0,
            generation=max(self.generation, other.generation) + 1,
            parent_id=self.genome_id,
        )

    def to_creds_token(self) -> int:
        """Map trait bitmask into a KernelBlock creds_token."""
        bits = 0
        trait_bits = {
            "plan":     0,
            "critique": 1,
            "build":    2,
            "memory":   3,
            "search":   4,
        }
        for trait, bit in trait_bits.items():
            if self.traits.get(trait, 0.0) >= 0.5:
                bits |= (1 << bit)
        return bits


_id_counter = 0


def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


class GenomeRegistry:
    """Stores and retrieves AgentGenome instances."""

    def __init__(self) -> None:
        self._genomes: dict[int, AgentGenome] = {}

    def register(self, genome: AgentGenome) -> None:
        self._genomes[genome.genome_id] = genome

    def get(self, genome_id: int) -> Optional[AgentGenome]:
        return self._genomes.get(genome_id)

    def all(self) -> list[AgentGenome]:
        return list(self._genomes.values())

    def elite(self, n: int = 5) -> list[AgentGenome]:
        """Return top-n genomes by fitness."""
        return sorted(self._genomes.values(), key=lambda g: g.fitness, reverse=True)[:n]

    def next_generation(self, n: int = 5, mutation_rate: float = 0.1) -> list[AgentGenome]:
        """Produce n children from elite parents via mutation + crossover."""
        parents = self.elite(max(2, n))
        if not parents:
            return []
        children = []
        for _ in range(n):
            if len(parents) >= 2 and random.random() < 0.5:
                p1, p2 = random.sample(parents, 2)
                child = p1.crossover(p2).mutate(mutation_rate)
            else:
                child = random.choice(parents).mutate(mutation_rate)
            children.append(child)
        return children
