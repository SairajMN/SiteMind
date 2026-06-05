# SiteMind MVP Specification

Production-ready MVP documentation for engineering handoff. The repo is greenfield; these docs are the implementation source of truth.

## Documents

| Document | Contents |
|----------|----------|
| [product.md](./product.md) | Product, personas, scope, UX (Stitch-sourced), evaluation, risks, roadmap |
| [architecture.md](./architecture.md) | System design, DAG engine, retrieval, workflows, LLM router, deployment |
| [api.md](./api.md) | REST + SSE contracts, schemas, error model |
| [data-model.md](./data-model.md) | PostgreSQL tables, Qdrant collections, indexes, ER diagram |
| [design/stitch.md](./design/stitch.md) | **Frontend source of truth** — Google Stitch project, screen map, export workflow |

## Design source (frontend)

All UI layout, typography, color, and screen composition follow the Google Stitch project:

**[SiteMind Stitch Project](https://stitch.withgoogle.com/projects/17227002468425644233)** · Project ID: `17227002468425644233`

Do not invent parallel visual language in code; map Stitch screens to Next.js routes and extract tokens from Stitch exports.

## Stack constraints (non-negotiable)

- Python backend only: FastAPI, Playwright, asyncio custom DAG
- No LangChain, no LangGraph
- PostgreSQL, Redis, Qdrant, uv
- LLM: Groq, OpenRouter (free-tier models), Inception Lab mercury-2 via `httpx` only
- Deploy: Render (API + worker), Vercel (frontend)

## Implementation phases

See [product.md § Delivery phases](./product.md#delivery-phases).
