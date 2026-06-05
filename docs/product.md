# SiteMind — Product Specification (MVP)

## Product summary and positioning

**SiteMind** is a website intelligence platform that converts a live website into a structured, queryable, inspectable knowledge system. It crawls, analyzes, and models the site as pages, forms, endpoints, auth signals, workflows, and retrieval-ready evidence.

**Core promise:** Paste a URL, and SiteMind returns a measurable intelligence graph: what exists, how it behaves, how it connects, and how confidently the system knows it.

**What it is not:** Not a chatbot. Not a generic scraper. Not a PDF QA wrapper.

### Value propositions

1. **Inspectable intelligence graph** — Artifacts are first-class objects with confidence and provenance.
2. **Grounded Q&A with verification** — Answers use only an evidence pack; the critic loop exposes weak support.
3. **Automation-ready outputs** — Workflow inference and OpenAPI-like specs support integration planning.

**Confidence: 92** — Scope is single-site MVP with clear boundaries; aligns with hackathon demo goals.

---

## Problem statement

Teams need to understand unfamiliar websites quickly: structure, forms, auth patterns, workflows, network behavior, and API surfaces. Crawlers return raw pages; RAG tools answer without operational structure; browser automation does not produce durable intelligence assets.

**Confidence: 95** — Well-defined user pain; no novel assumptions.

---

## MVP objective

Build a single-site intelligence system that:

- Ingests one website URL
- Crawls and analyzes at least **50 retrievable artifacts**
- Stores structured data in **PostgreSQL** and vectors in **Qdrant**
- Runs parallel analysis in a **custom Python DAG engine** (asyncio, no LangGraph/LangChain)
- Answers questions from **retrieved evidence only**
- Generates **workflow-to-API** outputs
- Visualizes execution, confidence, and evaluation on a **Stitch-designed** dark dashboard

**Confidence: 90** — Achievable with page budget 40–80 and multi-type chunking on demo sites.

---

## Primary personas

| Persona | Need |
|---------|------|
| **Product Analyst** | Site structure, hierarchy, workflows |
| **Automation Engineer** | Forms, endpoints, selectors, workflow mappings |
| **Demo Viewer / Student** | Polished dashboard, live DAG evidence, metrics |

**Confidence: 88** — Three personas cover demo and engineering audiences without scope creep.

---

## MVP scope

### In scope

URL submission, scope validation, crawl and page discovery, screenshots, DOM/forms/endpoints/auth extraction, workflow mining, chunking + embeddings, hybrid retrieval, grounded Q&A, critic verification, API spec generation, evaluation metrics, DAG visualization, job persistence and resumability, SSE live updates.

### Out of scope

Multi-site tenancy, continuous monitoring, login bypass, mobile app, bulk URL ingestion, unsafe third-party form submission, full schema inference for every endpoint.

**Confidence: 91** — Explicit exclusions prevent tenancy and auth-bypass work in MVP.

---

## Success metrics / KPIs

| Metric | Target |
|--------|--------|
| Retrievable artifacts | ≥ 50 chunks across artifact types |
| DAG parallelism | ≥ 3 concurrent branches post-crawl |
| Grounded answers | ≥ 1 cited answer per golden question |
| Workflows | ≥ 1 inferred workflow with step nodes |
| API specs | ≥ 1 generated spec per workflow candidate |
| Evaluation dashboard | Retrieval + grounding + failure metrics visible |
| Partial failure | Failed nodes visible; other branches complete |

**Confidence: 85** — Endpoint/workflow quality varies by site; label observed vs inferred.

---

## User stories

1. I paste a URL and launch analysis.
2. I watch crawl and analysis progress in real time.
3. I inspect pages, forms, endpoints, and workflows.
4. I ask a question and get a cited answer.
5. I inspect evidence behind the answer.
6. I generate an API-like spec for a discovered workflow.
7. I view a DAG graph with timings and parallel branches.
8. I review retrieval and extraction metrics.

**Confidence: 90** — Maps 1:1 to navigation and Stitch screens.

---

## Functional requirements

### Ingestion

- URL validation and normalization
- Same-domain restriction by default (`scope_policy: same_domain`)
- Robots-aware crawling where appropriate
- Site + crawl job + DAG run creation
- Async worker execution start

### Crawl

- Internal page discovery, deduplication, depth/path tracking
- Title, headings, links, visible text
- Screenshot capture (optional toggle)
- DOM summary per page
- Page budget default: **60** (configurable)

### Parallel analysis

Per page or batch, concurrently after crawl:

- DOM analysis, form analysis, endpoint analysis, auth detection, screenshot interpretation, workflow candidate detection

### Retrieval

- Chunk artifacts by type; embed; store in Qdrant
- Hybrid search with metadata filters
- Citations in answers

### Q&A

- Answer strictly from evidence pack
- Confidence score, snippets, refusal when unsupported
- Critic verification and optional re-retrieval

### Workflow intelligence

- Multi-step workflows as nodes/edges
- Selectors, transitions, endpoint links
- Inspectable step details

### API generation

- OpenAPI 3.0-style JSON per workflow
- `x-sitemind-inferred: true` on speculative fields
- Warnings array

### Evaluation

- Retrieval, grounding, workflow proxy, timing, failure metrics per run

**Confidence: 89** — Requirements trace to APIs and tables in companion docs.

---

## Non-functional requirements

| Area | Requirement |
|------|-------------|
| **Performance** | Parallel branches; live SSE updates; non-blocking UI |
| **Reliability** | Resumable jobs; isolated node failures; partial results preserved |
| **Security** | Scope enforcement; HTML sanitization; secret masking in logs |
| **Observability** | Structured JSON logs; node timings; retries; status transitions |
| **Scalability** | Schema supports multi-site later; MVP single active job per site |

**Confidence: 88** — Resumability depends on Redis + DAG state documented in architecture.md.

---

## UX/UI specification (Stitch-sourced)

### Design source of truth

All frontend visuals come from Google Stitch:

**Project:** https://stitch.withgoogle.com/projects/17227002468425644233  
**Handoff doc:** [design/stitch.md](./design/stitch.md)

Engineering exports Stitch screens to `frontend/` via HolyStitch, stitch-mcp, or manual HTML→JSX conversion, then wires APIs.

### Product style (from Stitch + PRD)

- Dark mode first
- Premium dashboard aesthetic; dense but legible
- Confidence and provenance always visible
- Restrained motion

### Navigation

Overview | DAG | Knowledge Base | Workflows | API Specs | Q&A | Evaluation | Settings

### Key screens (Stitch → route)

| Screen | Route |
|--------|-------|
| Landing / Start Analysis | `/` |
| Dashboard | `/sites/[siteId]` |
| DAG View | `/sites/[siteId]/dag` |
| Knowledge Base | `/sites/[siteId]/knowledge` |
| Workflows | `/sites/[siteId]/workflows` |
| API Specs | `/sites/[siteId]/api-specs` |
| Q&A | `/sites/[siteId]/qa` |
| Evaluation | `/sites/[siteId]/evaluation` |
| Settings | `/settings` |

### Left detail rail

On analysis-heavy views: selected page, artifact, evidence, or DAG node (per Stitch layout).

### Component requirements

- Status chips: `queued` | `running` | `succeeded` | `failed` | `skipped`
- Confidence badges: `high` | `medium` | `low` (from score thresholds: ≥0.75, ≥0.5, &lt;0.5)
- Progress bars per pipeline stage
- Citation drawer, source preview modal, node heatmap (Evaluation)

### Interaction rules

- One primary action per screen
- Partial results remain visible during run
- Failed nodes are never hidden
- Citations route to source evidence
- Low-confidence outputs show visible warning

**Confidence: 87** — Stitch owns pixels; shadcn/React Flow fill interactive gaps documented in design/stitch.md.

---

## Frontend implementation notes

- **Stack:** Next.js 14+ App Router, TypeScript, Tailwind, shadcn/ui, `@xyflow/react`, Recharts, `EventSource` for SSE
- **Env:** `NEXT_PUBLIC_API_BASE_URL`
- **Do not** ship default light shadcn theme; use Stitch-exported tokens in `frontend/styles/stitch-tokens.css`

See [architecture.md](./architecture.md) for runtime integration.

**Confidence: 86** — Fidelity depends on Stitch export step in Phase 1.

---

## Evaluation plan

### Metrics

Recall@K, Precision@K, MRR, Grounding Score, Workflow Accuracy (proxy), Endpoint Discovery Rate, Agent Success Rate, Critic Recovery Rate, Parallel Execution Time, Node Failure Rate.

### Golden set

`eval/golden/{domain}.json` — 10–20 questions, expected page/form/endpoint/workflow refs, optional `chunk_hash` list.

### Demo sites

- Primary: `https://books.toscrape.com`
- Secondary (forms/JS): `https://demo.playwright.dev`

### Dashboard (Stitch Evaluation screen)

Metric tiles, trend charts, node failure heatmap, retrieval by artifact type, critic recovery table.

**Confidence: 84** — Golden set is manual; automate metric computation only.

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| JS-heavy pages | Playwright render, network idle, screenshots |
| Crawl explosion | Depth cap, page budget, dedupe |
| Weak retrieval | Hybrid search, critic re-retrieve, refuse |
| False endpoints | `observed` vs `inferred` labels |
| Partial DAG failure | Branch isolation, visible failures |
| Login-protected sites | Auth hints + limitation report |
| Scope violations | Same-domain default, canonical URLs |
| LLM rate limits | Groq → OpenRouter → Inception fallback |
| Stitch/code drift | Re-export on design change; token file in repo |

**Confidence: 90** — Standard operational mitigations.

---

## Delivery phases

| Phase | Deliverable |
|-------|-------------|
| **1 Foundation** | uv, FastAPI, Alembic, Redis/Qdrant, docker-compose, Stitch → Next.js shell |
| **2 DAG** | Engine, planner, scheduler, DAG API + Stitch DAG screen wired |
| **3 Crawl + extract** | Playwright, five parallel extractors |
| **4 Retrieval + Q&A** | Chunker, embeddings, hybrid, ask + critic |
| **5 Workflows** | Miner, API generator, Stitch workflow/API screens |
| **6 Evaluation + polish** | Metrics, golden set, Evaluation screen |
| **7 Hardening** | Retries, rate limits, Render/Vercel deploy |

**Confidence: 88** — Phase 1 includes Stitch export before feature wiring.

---

## Self-check against requirements

| Requirement | Status |
|-------------|--------|
| URL submission + scope validation | Yes |
| ≥ 50 retrievable artifacts | Yes |
| Parallel DAG execution | Yes |
| PostgreSQL + Qdrant | Yes |
| Grounded Q&A + citations | Yes |
| Workflow + API output | Yes |
| Critic loop | Yes |
| Evaluation dashboard | Yes |
| Resumable jobs + partial failure | Yes |
| Dark premium UI (Stitch) | Yes |
| No LangChain/LangGraph | Yes |
| Python / FastAPI / Playwright / uv | Yes |

**Confidence: 93** — All must-haves mapped to docs and stack.
