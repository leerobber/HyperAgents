"""HyperAgents → sovereign-core-rs Rust Runtime bridge.

Wraps the Rust sovereign_core_rs extension exclusively.
Uses KernelBlock + WasmHost for block-level dispatch.

This file has NO knowledge of Python sovereign-core.
Do not import src.kernel, src.isa, or src.semantics here.
"""
from __future__ import annotations

from pathlib import Path

from sovereign_core_rs import Runtime, KernelBlock, SemanticWord, WasmHost

_WASM_DIR = Path(__file__).parent.parent / "wasm_agents"


class KernelBridge:
    """Rust sovereign_core_rs Runtime wrapper for HyperAgents."""

    def __init__(self, wasm_dir: Path | None = None) -> None:
        self._wasm_dir = Path(wasm_dir) if wasm_dir else _WASM_DIR
        self._runtime: Runtime | None = None
        self._host: WasmHost | None = None
        self._wasm_agents: dict[str, object] = {}

    def start(self) -> None:
        self._runtime = Runtime()
        self._host = WasmHost()
        self._load_wasm_agents()

    def _load_wasm_agents(self) -> None:
        if not self._wasm_dir.exists():
            return
        for wasm_file in self._wasm_dir.glob("*.wasm"):
            with open(wasm_file, "rb") as f:
                data = f.read()
            self._wasm_agents[wasm_file.stem] = self._host.load_agent(data, wasm_file.stem)

    # ── agent lifecycle ──────────────────────────────────────────────────────

    def spawn_agent(self, genome_id: int) -> int:
        return self._runtime.spawn_agent(genome_id)

    def agent_count(self) -> int:
        return self._runtime.agent_count()

    # ── block dispatch ───────────────────────────────────────────────────────

    def dispatch_block(
        self,
        agent_id: int,
        genome_id: int,
        creds_token: int,
        task_id: int,
        words: list[int],
        wasm_agent_name: str = "planner_agent",
        metrics_ref: int = 0,
    ) -> list[KernelBlock]:
        block = KernelBlock(
            agent_id=agent_id,
            genome_id=genome_id,
            creds_token=creds_token,
            task_id=task_id,
            words=words,
            metrics_ref=metrics_ref,
        )
        wasm = self._wasm_agents.get(wasm_agent_name)
        if wasm:
            return self._host.call_agent(wasm, block)
        return self._runtime.dispatch_block(block)

    # ── word encoding ────────────────────────────────────────────────────────

    def make_word(
        self,
        type_: int = 1,
        intent: int = 2,
        channel: int = 0,
        priority: int = 128,
        confidence: float = 1.0,
        payload_ref: int = 0,
    ) -> int:
        return SemanticWord(
            type_=type_,
            intent=intent,
            channel=channel,
            priority=priority,
            confidence=int(confidence * 65535),
            payload_ref=payload_ref,
        ).encode()

    def decode_word(self, word_int: int) -> SemanticWord:
        return SemanticWord.decode(word_int)

    # ── observability ────────────────────────────────────────────────────────

    def status(self) -> dict:
        return dict(self._runtime.status())

    @property
    def rust_backend(self) -> bool:
        return True
