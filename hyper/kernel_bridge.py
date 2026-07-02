"""KernelBridge — connects HyperAgents to sovereign-core-rs Rust runtime."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Try Rust extension first; fall back to pure-Python sovereign-core.
try:
    from sovereign_core_rs import Runtime, KernelBlock, SemanticWord, WasmHost
    _RUST = True
except ImportError:
    _RUST = False
    import sys
    _py_path = os.environ.get("SOVEREIGN_CORE_PATH", "")
    if _py_path and _py_path not in sys.path:
        sys.path.insert(0, _py_path)
    try:
        from src.kernel.runtime import Runtime as _PyRuntime          # type: ignore
        from src.semantics.semantic_word import SemanticWord as _PySW # type: ignore
        from src.isa.opcodes import Opcode                            # type: ignore
        from src.isa.instruction import Instruction                   # type: ignore
    except ImportError:
        _PyRuntime = _PySW = None

_WASM_DIR = Path(__file__).parent.parent / "wasm_agents"


class KernelBridge:
    """Wraps the sovereign-core-rs Runtime and manages WASM agent loading."""

    def __init__(self, wasm_dir: Optional[Path] = None) -> None:
        self._wasm_dir = Path(wasm_dir) if wasm_dir else _WASM_DIR
        self._runtime: Runtime | None = None
        self._host: WasmHost | None = None
        self._wasm_agents: dict[str, object] = {}
        self._use_rust = _RUST

    def start(self) -> None:
        if self._use_rust:
            from sovereign_core_rs import Runtime, WasmHost
            self._runtime = Runtime()
            self._host = WasmHost()
            self._load_wasm_agents()
        else:
            if _PyRuntime is None:
                raise RuntimeError(
                    "Neither sovereign_core_rs wheel nor SOVEREIGN_CORE_PATH is set."
                )
            self._runtime = _PyRuntime()

    def _load_wasm_agents(self) -> None:
        if not self._wasm_dir.exists():
            return
        for wasm_file in self._wasm_dir.glob("*.wasm"):
            with open(wasm_file, "rb") as f:
                data = f.read()
            agent = self._host.load_agent(data, wasm_file.stem)
            self._wasm_agents[wasm_file.stem] = agent

    def spawn_agent(self, genome_id: int) -> int:
        if self._use_rust:
            return self._runtime.spawn_agent(genome_id)
        else:
            return self._runtime.spawn_agent()

    def dispatch_block(
        self,
        agent_id: int,
        genome_id: int,
        creds_token: int,
        task_id: int,
        words: list[int],
        wasm_agent_name: str = "planner_agent",
        metrics_ref: int = 0,
    ) -> list[object]:
        if self._use_rust:
            from sovereign_core_rs import KernelBlock
            block = KernelBlock(
                agent_id=agent_id,
                genome_id=genome_id,
                creds_token=creds_token,
                task_id=task_id,
                words=words,
                metrics_ref=metrics_ref,
            )
            wasm = self._wasm_agents.get(wasm_agent_name)
            if wasm and self._host:
                return self._host.call_agent(wasm, block)
            return self._runtime.dispatch_block(block)
        else:
            # Pure-Python sovereign-core fallback
            from src.isa.instruction import Instruction  # type: ignore
            from src.isa.opcodes import Opcode          # type: ignore
            rt = self._runtime
            for w in words:
                rt.route_message(0, agent_id, w)
            return rt.dispatch_instruction(agent_id, Instruction(opcode=Opcode.PLAN))

    def make_word(
        self,
        type_: int = 1,
        intent: int = 2,
        channel: int = 0,
        priority: int = 128,
        confidence: float = 1.0,
        payload_ref: int = 0,
    ) -> int:
        if self._use_rust:
            from sovereign_core_rs import SemanticWord
            sw = SemanticWord(
                type_=type_,
                intent=intent,
                channel=channel,
                priority=priority,
                confidence=int(confidence * 65535),
                payload_ref=payload_ref,
            )
            return sw.encode()
        else:
            from src.semantics.semantic_word import SemanticWord  # type: ignore
            return SemanticWord.make(
                type=type_, intent=intent, channel=channel,
                priority=priority, confidence=confidence,
                payload_ref=payload_ref,
            ).encode()

    def agent_count(self) -> int:
        if self._use_rust:
            return self._runtime.agent_count()
        return len(self._runtime.agents)

    @property
    def rust_backend(self) -> bool:
        return self._use_rust
