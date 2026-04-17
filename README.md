# HyperAgents

> *Agents that rewrite themselves to optimize for any task you give them.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Sovereign Core](https://img.shields.io/badge/Sovereign_Core-connected-00ff88?style=flat-square)](https://github.com/leerobber/sovereign-core)
[![Architecture](https://img.shields.io/badge/Architecture-Self--Referential-7c3aed?style=flat-square)](https://github.com/leerobber/HyperAgents)

---

## What This Is

HyperAgents are **self-referential, self-improving agents** — they can observe their own architecture, reason about how to improve it, apply the improvement, and start over from the improved version.

Give them any computable task. They figure out the best way to do it — and then get better at doing it.

---

## How Self-Reference Works

```
┌─────────────────────────────────────────────────┐
│              HYPERAGENT LOOP                    │
│                                                 │
│  1. Receive task                                │
│  2. Observe own current architecture            │
│  3. Reason: is there a better way to do this?   │
│  4. If yes → propose modification               │
│  5. Test modification empirically               │
│  6. Keep improvement, discard regression        │
│  7. Execute task from improved architecture     │
│  8. Repeat — each cycle starts ahead            │
│                                                 │
│  The agent that finishes task N+1               │
│  is more capable than the one that started N   │
└─────────────────────────────────────────────────┘
```

**Key property:** Self-reference is the loop. The agent is both the subject doing the work and the object being improved. That's what makes it fundamentally different from a standard agent.

---

## Sovereign Core Integration

All inference routes through the **Sovereign Core gateway** — local hardware, no cloud dependency.

```python
# .env
SOVEREIGN_GATEWAY_URL=http://localhost:8000
```

Routing: RTX 5050 (primary) → Radeon 780M (fallback) → Ryzen CPU (last resort)

---

## Quickstart

```bash
git clone https://github.com/leerobber/HyperAgents
cd HyperAgents
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Part of the Sovereign Stack

| Repo | Role |
|------|------|
| [sovereign-core](https://github.com/leerobber/sovereign-core) | Gateway + KAIROS engine |
| [DGM](https://github.com/leerobber/DGM) | Darwin Gödel Machine — self-improving coding agent |
| **HyperAgents** | Self-referential swarm — routes inference through gateway |
| [Honcho](https://github.com/leerobber/Honcho) | Mission control dashboard |
| [contentai-pro](https://github.com/leerobber/contentai-pro) | Multi-agent content engine |

---

## Built By

**Terry Lee** — Douglasville, GA  
Self-taught systems architect. No team. No institution. Just architecture.

*Self-taught. Self-funded. Self-improving — just like the systems I build.*
