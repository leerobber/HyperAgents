"""ClusterKernel — BlockBus + NodeRuntime multi-node style dispatch."""
from __future__ import annotations

from typing import Optional

from sovereign_core_rs import BlockBus, NodeRuntime, KernelBlock, SemanticWord

try:
    from sovereign_gpu import GpuGraph, UnifiedGpu
    _HAS_GPU = True
except ImportError:
    GpuGraph = None      # type: ignore[assignment,misc]
    UnifiedGpu = None    # type: ignore[assignment,misc]
    _HAS_GPU = False

_GPU_GRAPH_INTENTS: frozenset[int] = frozenset({41, 43, 44, 45})
_GPU_PLAN_INTENTS:  frozenset[int] = frozenset({2})


def _intent_from_block(block: KernelBlock) -> int:
    """Decode intent from the first SemanticWord in a block."""
    if not block.words:
        return -1
    return (block.words[0] >> 48) & 0xFF


class ClusterKernel:
    """
    Wraps a BlockBus + NodeRuntime pair for cluster-style KernelBlock dispatch.

    When gpu_graph is provided, step() routes graph intents (41/43/44/45) to
    the GpuGraph engine instead of NodeRuntime; all other intents fall through
    to the Rust sovereign-core runtime.
    """

    def __init__(
        self,
        gpu_graph: Optional["GpuGraph"] = None,     # type: ignore[type-arg]
        unified: Optional["UnifiedGpu"] = None,      # type: ignore[type-arg]
    ) -> None:
        self.bus = BlockBus()
        self.node = NodeRuntime()
        self.gpu: Optional["GpuGraph"] = gpu_graph  # type: ignore[type-arg]
        # UnifiedGpu for planner intent dispatch
        self._unified: Optional["UnifiedGpu"] = unified  # type: ignore[type-arg]

    def submit_block(self, block: KernelBlock) -> None:
        self.bus.publish(block)

    def step(self, max_steps: int = 1) -> None:
        """Process up to max_steps blocks. GPU handles graph intents when available."""
        if self.gpu is None:
            self.node.step_many(self.bus, max_steps)
            return

        # GPU-aware loop: inspect each block's intent before dispatching
        for _ in range(max_steps):
            if self.bus.is_empty():
                break
            block = self.bus.consume()
            if block is None:
                break

            intent = _intent_from_block(block)
            if intent in _GPU_GRAPH_INTENTS:
                result = self._gpu_dispatch(block, intent)
                if result is not None:
                    self.bus.publish(result)
            elif self._unified is not None and intent in _GPU_PLAN_INTENTS:
                result = self._planner_dispatch(block)
                if result is not None:
                    self.bus.publish(result)
            else:
                # Re-publish so NodeRuntime picks it up, then step once
                self.bus.publish(block)
                self.node.step_once(self.bus)

    def _gpu_dispatch(self, block: KernelBlock, intent: int) -> Optional[KernelBlock]:
        """Run a graph algorithm on the GPU and wrap the result as a KernelBlock."""
        # payload_ref encodes the start node for BFS/DFS/shortest
        payload_ref = block.words[0] & 0xFFFF if block.words else 0

        if intent == 41:    # BFS
            out = self.gpu.bfs(payload_ref)
        elif intent == 43:  # DFS
            out = self.gpu.dfs(payload_ref)
        elif intent == 44:  # SHORTEST PATHS
            out = [n for n, _ in self.gpu.shortest_paths(payload_ref)]
        elif intent == 45:  # TOPO SORT
            out = self.gpu.topo_sort() or []
        else:
            return None

        word = SemanticWord(
            type_=6,        # RESULT
            intent=50,      # GRAPH_RESULT (GPU)
            channel=0,
            priority=128,
            confidence=60000,
            payload_ref=len(out) & 0xFFFF,
        ).encode()
        return KernelBlock(
            agent_id=block.agent_id,
            genome_id=block.genome_id,
            creds_token=block.creds_token,
            task_id=block.task_id,
            words=[word],
            metrics_ref=0,
        )

    def _planner_dispatch(self, block: KernelBlock) -> Optional[KernelBlock]:
        plan_bytes = bytes(block.words[0].to_bytes(8, "little")) if block.words else b""
        out_bytes  = self._unified.plan(plan_bytes)  # type: ignore[union-attr]
        word = SemanticWord(
            type_=6, intent=51, channel=0, priority=128,
            confidence=60000, payload_ref=len(out_bytes) & 0xFFFF,
        ).encode()
        return KernelBlock(
            agent_id=block.agent_id, genome_id=block.genome_id,
            creds_token=block.creds_token, task_id=block.task_id,
            words=[word], metrics_ref=0,
        )

    def drain_results(self, max_blocks: int | None = None) -> list[KernelBlock]:
        results: list[KernelBlock] = []
        count = 0
        while not self.bus.is_empty():
            if max_blocks is not None and count >= max_blocks:
                break
            blk = self.bus.consume()
            if blk is None:
                break
            results.append(blk)
            count += 1
        return results

    def status(self) -> dict:
        return {
            "bus_size": self.bus.size(),
            "agent_count": self.node.agent_count(),
            "gpu": self.gpu is not None,
        }
