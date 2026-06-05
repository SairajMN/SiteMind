# SiteMind

A website intelligence platform that converts a live website into a structured, queryable, inspectable knowledge system. It crawls, analyzes, and models a site as pages, forms, endpoints, auth signals, workflows, and retrieval-ready evidence.

## Documentation

**[MVP specification (engineering handoff)](./docs/README.md)**

| Doc | Description |
|-----|-------------|
| [docs/product.md](./docs/product.md) | Product, UX, evaluation, roadmap |
| [docs/architecture.md](./docs/architecture.md) | System, DAG, retrieval, deployment |
| [docs/api.md](./docs/api.md) | REST + SSE API |
| [docs/data-model.md](./docs/data-model.md) | PostgreSQL + Qdrant |
| [docs/design/stitch.md](./docs/design/stitch.md) | **Frontend UI** — [Google Stitch project](https://stitch.withgoogle.com/projects/17227002468425644233) |

## Stack

FastAPI · Playwright · custom asyncio DAG · PostgreSQL · Redis · Qdrant · Next.js (from Stitch) · uv

No LangChain. No LangGraph.

## Assignment results (DAG agent)

**Does this repo meet the DAG assignment?** Yes — after the agent layer was added. See **[docs/ASSIGNMENT.md](./docs/ASSIGNMENT.md)**.

```bash
uv run sitemind-benchmark
```

Logs: [`logs/assignment/SUMMARY.json`](./logs/assignment/SUMMARY.json) (all five parts; `all_passed: true` when run locally).

| Part | Requirement | Evidence |
|------|-------------|----------|
| 1 | Base queries `hello`, `A`, `I`, `J`, `K` | `logs/assignment/1_base_*.log` |
| 2 | Parallel fan-out (3 branches, max ≈ wall-clock) | `logs/assignment/2_parallel_fanout.log` |
| 3 | Critic pass + fail + Planner recovery | `logs/assignment/3_critic_*.log` |
| 4 | Coder + SandboxExecutor | `logs/assignment/4_coder_sandbox.log`, `agent/prompts/coder.md` |
| 5 | New skill (Investigator) | `logs/assignment/5_investigator_skill.log`, `agent/prompts/investigator.md` |

**Production-ready for full SiteMind PRD?** Not yet — crawl/RAG/Qdrant/LLM wiring and deploy hardening remain. Assignment architecture is intact and testable.

## Quick start

See **[docs/GETTING_STARTED.md](./docs/GETTING_STARTED.md)**.

```bash
cp .env.example .env          # add API keys
docker compose up -d
uv run alembic upgrade head   # after first revision
uv run sitemind-api
cd frontend && npm run dev
```

## Frontend design

Scaffolded Next.js app with Stitch-inspired dark tokens (`frontend/src/styles/stitch-tokens.css`). For pixel-perfect screens, export [Stitch project `17227002468425644233`](https://stitch.withgoogle.com/projects/17227002468425644233) per [docs/design/stitch.md](./docs/design/stitch.md).
