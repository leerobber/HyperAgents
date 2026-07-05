# 0002: Talks directly to a local Qwen2.5 model server, not through sovereign-core's gateway

**Status:** Reference only — this is a real, working, deliberate integration pattern, different in kind from Honcho's

## Context

`agent/llm.py` was rewritten (commit `b01332d`) to route all model calls
through `litellm`'s OpenAI-compatible mode at `http://localhost:8001/v1`,
model name `openai/qwen2.5-32b-awq`, configured via `.env`:
`OPENAI_API_BASE=http://localhost:8001/v1`. All of the original model
constants (`CLAUDE_MODEL`, `OPENAI_MODEL`, `GEMINI_MODEL`, etc.) are kept
as backward-compatible aliases pointing at the same local model, so
existing call sites didn't need to change.

## This is a genuinely different integration pattern than Honcho's

Compare to `Honcho`'s `docs/architecture/0002` (fixed this session): that
repo's `SovereignClient` talks to sovereign-core's **gateway** (port
`8080`), which does health routing, auction/credit logic, and KAIROS
orchestration on top of the raw model backends.

This repo bypasses the gateway entirely and talks straight to the
underlying model server sovereign-core's gateway *also* talks to.
Confirmed real and consistent: sovereign-core's own
`gateway/config.py` configures its `rtx5050` backend at exactly
`OLLAMA_RTX_URL=http://localhost:8001` — so this repo's target is real,
not a guess, it's just a different layer of the same stack (the raw
model server, not the gateway sitting in front of it).

## Real port-collision risk, not yet hit but real

Port `8001` is *also* GH05T3's own, completely unrelated
`backend/server.py` (existing FastAPI + Mongo app) per that repo's own
port map. Running GH05T3's `backend/server.py` and sovereign-core's
`rtx5050` Ollama backend on the same host at the same time would put two
unrelated services on the same port — the same class of collision already
documented for `GATEWAY_PORT` 8002 between `GH05T3` and
`GH05T3-Sovereign` (see `sovereign-core`'s
`docs/architecture/0004-http-mesh-federation.md`).

## Consequences

- Bypassing the gateway means this repo's agents don't get
  sovereign-core's health-based backend failover, auction/credit
  accounting, or KAIROS cycle recording for whatever they do — that's a
  real, deliberate tradeoff (simpler, one fixed local model, no gateway
  dependency), not an oversight.
- If GH05T3's `backend/server.py` and sovereign-core's `rtx5050` backend
  are ever expected to run simultaneously on one machine, one of them
  needs to move off port `8001`.
