# 0001: What this fork actually adds beyond upstream, vs. what the README describes

**Status:** Reference only

## Context

This repo is a fork of `facebookresearch/HyperAgents`
(`upstream` remote). The README describes only the upstream
self-referential-agent-loop concept (observe → reason → propose →
test → keep/discard → repeat) and doesn't mention any of this fork's
own work.

## What's actually different from upstream

`git diff --stat upstream/main main`: 43 files changed, 2,618 insertions.
Not a passive/dormant fork — real, substantial fork-specific engineering:

- `agent/llm.py` rewritten to route all model calls to a local Qwen2.5
  server instead of Claude/GPT/Gemini — see
  [0002](0002-direct-model-server-not-gateway.md).
- A new `hyper/` package: `genome.py` (242 lines, `AgentGenome`),
  `scheduler.py` (395 lines, `HyperScheduler` with real GPU-planner and
  GNN-embed dispatch paths), `cluster_kernel.py` (142 lines),
  `kernel_bridge.py` (103 lines) — see
  [0003](0003-sovereign-core-rs-wasm-kernel-bridge.md).
- Real compiled WASM binaries in `wasm_agents/` (`biz_agent.wasm`,
  `content_agent.wasm`, `planner_agent.wasm`, `search_agent.wasm`).
- Real tests: `tests/test_hyper_kernel.py` (434 lines),
  `tests/test_ecc_tools_cleanup.py` (314 lines).
- A `pyproject.toml` this fork added (upstream didn't have one) declaring
  `hyperagents` as a package with an optional `rust` extra pinned to
  `sovereign-core-rs>=0.1.0`.
- Commit history shows a real architectural pivot, not just additions:
  `b01332d` ("Rewire all LLM calls to local Qwen2.5-32B-AWQ") →
  `0496526` ("sovereign-core-rs integration — genome evolution on
  Rust+WASM kernel") → `b7bfc83` ("strip all Python sovereign-core from
  KernelBridge") — i.e., an earlier version of `KernelBridge` apparently
  depended on Python sovereign-core directly, and was deliberately
  refactored to depend only on the Rust `sovereign_core_rs` extension
  instead. `kernel_bridge.py`'s current docstring states this explicitly:
  "This file has NO knowledge of Python sovereign-core. Do not import
  src.kernel, src.isa, or src.semantics here."

## Consequences

The README should describe this fork's real additions (the genome/
scheduler/kernel-bridge system, the WASM agents, the local-model
routing) if it's meant to represent what's actually in this repo, not
just the inherited upstream concept. Not changed here — flagged as a
real gap, matching the pattern already established across the other
repos in this ecosystem (READMEs describing something different from
what the code actually does).
