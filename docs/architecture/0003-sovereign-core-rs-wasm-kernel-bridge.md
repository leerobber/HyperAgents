# 0003: Real, working Rust+WASM kernel bridge via `sovereign_core_rs`

**Status:** Reference only — verified working, not just present

## Context

`hyper/kernel_bridge.py`'s `KernelBridge` wraps a Python extension module
named `sovereign_core_rs`, imported directly: `from sovereign_core_rs
import Runtime, KernelBlock, SemanticWord, WasmHost`. This is presumably
built (via pyo3, based on the naming) from the separate `sovereign-core-rs`
repo — not otherwise investigated this session before now.

## Verified, not assumed

- `sovereign_core_rs` **is actually installed** on this machine
  (`/home/leer4/.local/lib/python3.12/site-packages/sovereign_core_rs/`)
  — it imports successfully.
- It is **not published on PyPI** (`pip index versions sovereign-core-rs`
  returns "No matching distribution found"). `pyproject.toml`'s
  `rust = ["sovereign-core-rs>=0.1.0"]` optional dependency would fail to
  resolve via a normal `pip install hyperagents[rust]` for anyone without
  the actual `sovereign-core-rs` source built locally first.
- Ran `KernelBridge` directly: `start()`, `spawn_agent(genome_id=1)`,
  `agent_count()`, and `status()` all executed for real and returned
  real, consistent state (`agent_count` went `0 → 1` after spawning,
  `status()` returned `{"agents": 1}`). This is real, working code, not a
  stub or an aspirational integration.
- `_load_wasm_agents()` loads every `*.wasm` file under `wasm_agents/`
  into the Rust `WasmHost` at startup — the 4 real WASM binaries in
  [0001](0001-fork-scope-vs-readme.md) are genuinely used, not just
  checked in.

## Consequences

- This is the clearest evidence in this whole ecosystem of a real,
  working, code-level (not just HTTP-federated) integration between two
  separate repos (`HyperAgents` and `sovereign-core-rs`) — different in
  kind from the "federate over HTTP, don't import code" pattern
  documented in `sovereign-core`'s own
  `docs/architecture/0004-http-mesh-federation.md`. Worth being aware of
  as a precedent if `sovereign-core-rs` changes its Python API — this
  repo would need updating too, and there's no version pin enforcement
  since the package isn't resolvable from a plain `pip install`.
- `hyper/scheduler.py` and `hyper/cluster_kernel.py` (GPU planner
  dispatch, GNN-embed dispatch) weren't independently re-verified beyond
  reading their presence in the diff — only `kernel_bridge.py`'s core
  spawn/status path was actually executed.
