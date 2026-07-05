# Architecture Decisions

Lightweight ADRs (Architecture Decision Record: Status / Context /
Decision / Consequences), same convention used across `GH05T3`,
`GH05T3-Sovereign`, `sovereign-core`, and `Honcho`'s `docs/architecture/`.

Written from actually reading and, where possible, running the real code
in this repo — this is a fork of `facebookresearch/HyperAgents`, and the
README describes the upstream self-referential-agent concept without
mentioning any of this fork's own substantial additions. These entries
document the fork-specific reality, not the upstream project.

| # | Decision | Status |
|---|---|---|
| [0001](0001-fork-scope-vs-readme.md) | What this fork actually adds beyond upstream, vs. what the README describes | Reference only |
| [0002](0002-direct-model-server-not-gateway.md) | Talks directly to a local Qwen2.5 model server, not through sovereign-core's gateway | Reference only, real port-collision risk noted |
| [0003](0003-sovereign-core-rs-wasm-kernel-bridge.md) | Real, working Rust+WASM kernel bridge via `sovereign_core_rs` | Reference only |
| [0004](0004-untracked-git-lfs-risk.md) | Real Git LFS pointer files with no LFS tracking configured | Needs attention |

## How to add a new one

Copy the format of any existing entry, number it sequentially, and add a
row to the table above. Prefer documenting a real decision (or a real
bug/gap, found by reading and testing the code) over speculating about
one in advance.
