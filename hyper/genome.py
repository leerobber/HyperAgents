"""AgentGenome and GenomeRegistry — genome management for HyperAgents."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# ── AgentGenome ───────────────────────────────────────────────────────────────

@dataclass
class AgentGenome:
    """Full description of an agent's traits, capabilities, and evolution parameters."""

    # Core identity
    genome_id: int
    name: str
    wasm_agent: str                         # e.g. "planner_agent"

    # Legacy traits dict — used by to_creds_token() and simple mutation
    traits: dict[str, float] = field(default_factory=dict)

    # Evolution accounting
    fitness: float = 0.0
    generation: int = 0
    parent_id: Optional[int] = None

    # ── Expanded evolution fields ─────────────────────────────────────────────
    model_id: str = "sovereign-core"
    temperature: float = 0.7
    max_tokens: int = 2048
    reasoning_mode: str = "chain-of-thought"
    depth_limit: int = 5
    reflection_enabled: bool = True
    tool_access: list = field(default_factory=list)
    tool_budget: int = 10
    cooperate_level: float = 0.5
    delegate_level: float = 0.5
    risk_tolerance: float = 0.5
    goal_bias: str = "quality"
    memory_scope: str = "session"
    memory_strategy: str = "recency"

    # ── GPU traits ────────────────────────────────────────────────────────────
    gpu_enabled: bool = False
    gpu_backend: str = "webgpu"             # "cuda" | "vulkan" | "webgpu" | "cpu"
    gpu_kernel: str = "bfs"                 # "bfs" | "dfs" | "topo" | "shortest"
    gpu_workgroup_size: int = 64
    gpu_iterations: int = 1

    # ── Mutation ──────────────────────────────────────────────────────────────

    def mutate(self, rate: float = 0.1) -> "AgentGenome":
        """Return a new genome with Gaussian noise on traits + uniform perturbation on evolution fields."""
        new_traits = {
            k: max(0.0, min(1.0, v + random.gauss(0, rate)))
            for k, v in self.traits.items()
        }
        return AgentGenome(
            genome_id=0,                    # assigned by GenomeRegistry.add_genome
            name=f"{self.name}_m{self.generation + 1}",
            wasm_agent=self.wasm_agent,
            traits=new_traits,
            fitness=0.0,
            generation=self.generation + 1,
            parent_id=self.genome_id,
            model_id=self.model_id,
            temperature=min(max(self.temperature + random.uniform(-0.1, 0.1), 0.0), 1.0),
            max_tokens=max(64, self.max_tokens + random.randint(-256, 256)),
            reasoning_mode=self.reasoning_mode,
            depth_limit=max(1, self.depth_limit + random.randint(-1, 1)),
            reflection_enabled=self.reflection_enabled,
            tool_access=list(self.tool_access),
            tool_budget=max(1, self.tool_budget + random.randint(-1, 1)),
            cooperate_level=min(max(self.cooperate_level + random.uniform(-0.1, 0.1), 0.0), 1.0),
            delegate_level=min(max(self.delegate_level + random.uniform(-0.1, 0.1), 0.0), 1.0),
            risk_tolerance=min(max(self.risk_tolerance + random.uniform(-0.1, 0.1), 0.0), 1.0),
            goal_bias=self.goal_bias,
            memory_scope=self.memory_scope,
            memory_strategy=self.memory_strategy,
            gpu_enabled=self.gpu_enabled,
            gpu_backend=self.gpu_backend,
            gpu_kernel=self.gpu_kernel,
            gpu_workgroup_size=max(32, min(256, self.gpu_workgroup_size + random.randint(-32, 32))),
            gpu_iterations=max(1, self.gpu_iterations + random.randint(-1, 1)),
        )

    def mutate_gpu(self) -> "AgentGenome":
        """Mutate GPU-specific traits only."""
        child = self.mutate(rate=0.0)       # copy everything, no trait noise
        child.gpu_workgroup_size = max(32, min(256, self.gpu_workgroup_size + random.randint(-32, 32)))
        child.gpu_iterations = max(1, self.gpu_iterations + random.randint(-1, 1))
        child.gpu_pipeline = random.choice(["bfs", "dfs", "shortest", "topo"])
        child.gpu_backend = random.choice(["cuda", "vulkan", "webgpu", "cpu"])
        return child

    # ── Crossover (instance method for backward compat) ───────────────────────

    def crossover(self, other: "AgentGenome") -> "AgentGenome":
        """Single-point crossover on shared trait keys + blend of evolution fields."""
        return crossover(self, other)

    # ── creds_token ───────────────────────────────────────────────────────────

    def to_creds_token(self) -> int:
        """Map trait bitmask into a KernelBlock creds_token."""
        bits = 0
        trait_bits = {"plan": 0, "critique": 1, "build": 2, "memory": 3, "search": 4}
        for trait, bit in trait_bits.items():
            if self.traits.get(trait, 0.0) >= 0.5:
                bits |= (1 << bit)
        return bits


# ── Standalone crossover function ─────────────────────────────────────────────

def crossover(g1: AgentGenome, g2: AgentGenome) -> AgentGenome:
    """Produce a child by blending two parent genomes."""
    # Trait crossover: single-point on shared keys
    keys = list(g1.traits.keys())
    if keys:
        split = random.randint(1, max(1, len(keys) - 1))
        new_traits: dict[str, float] = {}
        for i, k in enumerate(keys):
            new_traits[k] = g1.traits[k] if i < split else g2.traits.get(k, g1.traits[k])
    else:
        new_traits = {}

    return AgentGenome(
        genome_id=0,
        name=f"{g1.name}x{g2.name}",
        wasm_agent=random.choice([g1.wasm_agent, g2.wasm_agent]),
        traits=new_traits,
        fitness=0.0,
        generation=max(g1.generation, g2.generation) + 1,
        parent_id=g1.genome_id,
        model_id=random.choice([g1.model_id, g2.model_id]),
        temperature=(g1.temperature + g2.temperature) / 2,
        max_tokens=int((g1.max_tokens + g2.max_tokens) / 2),
        reasoning_mode=random.choice([g1.reasoning_mode, g2.reasoning_mode]),
        depth_limit=int((g1.depth_limit + g2.depth_limit) / 2),
        reflection_enabled=random.choice([g1.reflection_enabled, g2.reflection_enabled]),
        tool_access=list(set(g1.tool_access + g2.tool_access)),
        tool_budget=int((g1.tool_budget + g2.tool_budget) / 2),
        cooperate_level=(g1.cooperate_level + g2.cooperate_level) / 2,
        delegate_level=(g1.delegate_level + g2.delegate_level) / 2,
        risk_tolerance=(g1.risk_tolerance + g2.risk_tolerance) / 2,
        goal_bias=random.choice([g1.goal_bias, g2.goal_bias]),
        memory_scope=random.choice([g1.memory_scope, g2.memory_scope]),
        memory_strategy=random.choice([g1.memory_strategy, g2.memory_strategy]),
        gpu_enabled=g1.gpu_enabled or g2.gpu_enabled,
        gpu_backend=random.choice([g1.gpu_backend, g2.gpu_backend]),
        gpu_kernel=random.choice([g1.gpu_kernel, g2.gpu_kernel]),
        gpu_workgroup_size=int((g1.gpu_workgroup_size + g2.gpu_workgroup_size) / 2),
        gpu_iterations=int((g1.gpu_iterations + g2.gpu_iterations) / 2),
    )


# ── ID counter ────────────────────────────────────────────────────────────────

_id_counter = 0


def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


# ── GenomeRegistry ────────────────────────────────────────────────────────────

class GenomeRegistry:
    """Stores, retrieves, and evolves AgentGenome instances."""

    def __init__(self) -> None:
        self._genomes: dict[int, AgentGenome] = {}

    def register(self, genome: AgentGenome) -> None:
        self._genomes[genome.genome_id] = genome

    def add_genome(self, genome: AgentGenome) -> int:
        """Assign a registry ID to genome (overwrites genome_id=0) and register it."""
        gid = _next_id()
        genome.genome_id = gid
        self._genomes[gid] = genome
        return gid

    def get(self, genome_id: int) -> Optional[AgentGenome]:
        return self._genomes.get(genome_id)

    def all(self) -> list[AgentGenome]:
        return list(self._genomes.values())

    def elite(self, n: int = 5) -> list[AgentGenome]:
        """Return top-n genomes by fitness."""
        return sorted(self._genomes.values(), key=lambda g: g.fitness, reverse=True)[:n]

    # Alias for next_generation spec
    top_genomes = elite

    def next_generation(
        self,
        elite_count: int = 5,
        children_count: int = 20,
        # backward-compat: old callers pass n=N
        n: Optional[int] = None,
        mutation_rate: float = 0.1,
    ) -> list[AgentGenome]:
        """Produce a new generation via crossover + mutation.

        Returns elites + children (new API) or just children (n= legacy API).
        """
        if n is not None:
            children_count = n
            elite_count = max(2, n)

        elites = self.top_genomes(elite_count)
        if len(elites) < 2:
            # Not enough parents — just mutate what we have
            children = [e.mutate(mutation_rate) for e in elites for _ in range(children_count // max(1, len(elites)))]
            for child in children:
                self.add_genome(child)
            if n is not None:
                return children[:children_count]
            return elites + children

        children = []
        for _ in range(children_count):
            p1, p2 = random.sample(elites, 2)
            child = crossover(p1, p2).mutate(mutation_rate)
            self.add_genome(child)
            children.append(child)

        if n is not None:
            return children           # legacy: just return children
        return elites + children      # new API: return full next generation
