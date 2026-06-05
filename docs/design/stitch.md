# SiteMind Frontend — Google Stitch Design Handoff

## Source project

| Field | Value |
|-------|--------|
| **Stitch URL** | https://stitch.withgoogle.com/projects/17227002468425644233 |
| **Project ID** | `17227002468425644233` |
| **Role** | Single source of truth for layout, visual hierarchy, spacing, and screen composition |

Engineering implements the Next.js app **from this project**, not from ad-hoc mockups in code comments.

**Current repo status:** A Stitch-inspired dark scaffold lives in `frontend/` (`src/styles/stitch-tokens.css`). Replace with a HolyStitch/stitch-mcp export when you have Stitch API access; keep `lib/api-client.ts` and `hooks/useJobEvents.ts`.

---

## Screen-to-route mapping

Map each Stitch screen to an App Router route. Update this table after exporting screen names from Stitch (Project → Screens).

| Stitch screen (expected) | Next.js route | PRD nav label |
|--------------------------|---------------|---------------|
| Landing / Start Analysis | `/` | — |
| Dashboard / Overview | `/sites/[siteId]` | Overview |
| DAG View | `/sites/[siteId]/dag` | DAG |
| Knowledge Base | `/sites/[siteId]/knowledge` | Knowledge Base |
| Workflow Explorer | `/sites/[siteId]/workflows` | Workflows |
| API Specs | `/sites/[siteId]/api-specs` | API Specs |
| Q&A | `/sites/[siteId]/qa` | Q&A |
| Evaluation | `/sites/[siteId]/evaluation` | Evaluation |
| Settings | `/settings` | Settings |

**Shared chrome (from Stitch):** top navigation, left detail rail on analysis views, status chips, confidence badges, citation/evidence drawer.

---

## Export workflow (recommended)

Stitch outputs HTML/CSS; SiteMind uses **Next.js + TypeScript + Tailwind + shadcn/ui**. Use one of these paths:

### Option A — HolyStitch compiler (fastest, zero conversion tokens)

1. Install [HolyStitch](https://github.com/BaselAshraf81/holystitch) MCP in Cursor.
2. Configure Stitch API credentials per HolyStitch README.
3. Run in agent mode:

   ```text
   Convert my Stitch project 17227002468425644233 into a Next.js app at frontend/
   ```

4. HolyStitch fetches screens, extracts Tailwind theme (colors, fonts, dark mode), deduplicates components, writes `frontend/`.
5. Wire `frontend/lib/api-client.ts` and SSE hooks; replace static demo data with API calls.

### Option B — stitch-mcp CLI (preview + agent context)

1. Install [stitch-mcp](https://github.com/davideast/stitch-mcp).
2. `stitch-mcp init` then `stitch-mcp serve -p 17227002468425644233` to preview locally.
3. Use `stitch-mcp site` or screen fetch tools to pull HTML per screen into `frontend/`.
4. Manually componentize: `class` → `className`, split into `components/`, add `'use client'` where needed.

### Option C — Manual export from Stitch UI

1. Open each screen in [Stitch](https://stitch.withgoogle.com/projects/17227002468425644233).
2. Export code (HTML/CSS) or Paste to Figma then inspect tokens.
3. Convert HTML → JSX (e.g. htmltojsx); map controls to shadcn primitives (`Button`, `Input`, `Badge`, `Sheet` for drawers).
4. Centralize tokens in `frontend/styles/stitch-tokens.css` (CSS variables from Stitch theme).

---

## Token extraction checklist

After export, commit these artifacts under `frontend/`:

| Artifact | Path | Purpose |
|----------|------|---------|
| Color palette | `styles/stitch-tokens.css` | Background, surface, border, accent, semantic (success/warn/error) |
| Typography | `tailwind.config.ts` `fontFamily`, `fontSize` | Match Stitch headings/body |
| Spacing/radius | Tailwind `theme.extend` | Cards, rails, drawers |
| Dark mode | `class="dark"` on `<html>` | Stitch project is dark-first |
| Component mapping | `docs/design/component-map.md` (optional) | Stitch block → shadcn component |

---

## shadcn mapping (default)

| Stitch pattern | shadcn / library |
|----------------|------------------|
| Primary CTA button | `Button` variant default |
| Secondary / ghost | `Button` variant outline/ghost |
| URL / search input | `Input` |
| Status pill | `Badge` |
| Side evidence panel | `Sheet` or custom `EvidenceDrawer` |
| Modal preview | `Dialog` |
| DAG canvas | `@xyflow/react` (layout from Stitch frame; graph logic separate) |
| Metric charts | `recharts` inside Stitch card frames |

---

## Live data integration (post-export)

Stitch screens are static. Connect:

| UI region | API / stream |
|-----------|----------------|
| Job progress | `GET /api/jobs/{job_id}/events` (SSE) |
| Dashboard counts | `GET /api/jobs/{job_id}`, `GET /api/sites/{site_id}/pages` |
| DAG graph | `GET /api/dag-runs/{dag_run_id}` |
| Knowledge list | `GET /api/sites/{site_id}/chunks` |
| Q&A | `POST /api/sites/{site_id}/ask` |
| Evaluation | `GET /api/sites/{site_id}/evaluations` |

Preserve Stitch loading skeletons; bind to SSE `job.progress` and `artifact.created`.

---

## Acceptance criteria (design fidelity)

- [ ] All nine routes render layouts consistent with Stitch screenshots
- [ ] Dark theme tokens match Stitch export (no default shadcn light theme in production)
- [ ] Top nav labels match PRD: Overview, DAG, Knowledge Base, Workflows, API Specs, Q&A, Evaluation, Settings
- [ ] Confidence badges and status chips visible on every artifact list (per Stitch)
- [ ] Citation drawer opens from Q&A and Knowledge Base without layout shift

---

## Confidence

**Score: 78** — Workflow is sound; exact screen names and token values require access to the Stitch project owner account. Re-export after any Stitch design change and diff `frontend/styles/stitch-tokens.css`.
