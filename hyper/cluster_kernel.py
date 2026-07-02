"""ClusterKernel — BlockBus + NodeRuntime multi-node style dispatch."""
from __future__ import annotations

from sovereign_core_rs import BlockBus, NodeRuntime, KernelBlock


class ClusterKernel:
    """
    Wraps a BlockBus + NodeRuntime pair for cluster-style KernelBlock dispatch.

    HyperScheduler uses this as an alternative to KernelBridge when
    use_cluster=True — blocks flow through the shared bus rather than
    being dispatched directly to WASM agents.
    """

    def __init__(self) -> None:
        self.bus = BlockBus()
        self.node = NodeRuntime()

    def submit_block(self, block: KernelBlock) -> None:
        self.bus.publish(block)

    def step(self, max_steps: int = 1) -> None:
        self.node.step_many(self.bus, max_steps)

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
        }
