# Getting Started

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (for Postgres, Redis, Qdrant)

## 1. Environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Edit `.env` with your API keys:

- `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `INCEPTION_API_KEY` (at least one for LLM features)
- Optional: `QDRANT_API_KEY` if using Qdrant Cloud

For local crawl testing only:

```bash
ALLOW_LOCALHOST_TARGETS=true
```

## 2. Infrastructure

```bash
docker compose up -d
```

## 3. Database

```bash
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```

## 4. Run API

```bash
uv run sitemind-api
```

API: http://localhost:8000  
Health: http://localhost:8000/api/health

## 5. Run frontend

```bash
cd frontend && npm run dev
```

Open http://localhost:3000

## Security and rate limits

| Control | Default |
|---------|---------|
| POST `/api/sites` | 5 requests / minute / IP |
| POST `/api/sites/{id}/ask` (when enabled) | 10 / minute / IP |
| Other routes | 60 / minute / IP |
| Crawl depth | Capped at `CRAWL_MAX_DEPTH` (5) |
| Page budget | Capped at `CRAWL_MAX_PAGE_BUDGET` (200) |
| SSRF | Private IPs and localhost blocked unless `ALLOW_LOCALHOST_TARGETS=true` |

Exceeded limits return HTTP 429 with `RATE_LIMITED`.

## Stitch UI export (optional upgrade)

The frontend uses Stitch-inspired tokens in `frontend/src/styles/stitch-tokens.css`. To replace with pixel-perfect Stitch screens:

1. Open [Stitch project](https://stitch.withgoogle.com/projects/17227002468425644233)
2. Run HolyStitch or stitch-mcp into `frontend/` (see [design/stitch.md](./design/stitch.md))
3. Keep `lib/api-client.ts` and `hooks/useJobEvents.ts`

## Worker (coming next)

```bash
uv run python -m app.worker
```
