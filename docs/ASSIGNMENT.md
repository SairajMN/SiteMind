# DAG Agent Assignment — SiteMind

SiteMind uses a **custom asyncio DAG engine** (`app/dag/`) for both website crawl/analysis and the **query agent** (`agent/`).

## Problem choice

**Website intelligence:** crawl a URL, extract artifacts in parallel, answer questions with evidence, critic verification, and sandboxed computation.

## Run proofs (logs)

```bash
uv run sitemind-benchmark
# or: uv run python scripts/run_assignment_benchmarks.py
```

Logs: [`logs/assignment/`](../logs/assignment/)

| Part | Log file | What it proves |
|------|----------|----------------|
| **1** Base queries | `1_base_hello.log` … `1_base_K.log` | Verbatim `hello`, `A`, `I`, `J`, `K` within bounds in `agent/agent_config.yaml` |
| **2** Parallel fan-out | `2_parallel_fanout.log` | 3 branches (lane 1); `max_ms≈551` vs `sum_ms≈1153` → wall-clock ≈ **max**, not sum |
| **3** Critic | `3_critic_pass.log`, `3_critic_fail_recovery.log` | Pass + fail (`form_count_matches_evidence`); fail triggers **recovery** node |
| **4** Coder | `4_coder_sandbox.log` | `median_depth` via `SandboxExecutor` + [`agent/prompts/coder.md`](../agent/prompts/coder.md) |
| **5** New skill | `5_investigator_skill.log` | **Investigator** in `agent_config.yaml` — DOM heading/link inventory |

Summary: [`logs/assignment/SUMMARY.json`](../logs/assignment/SUMMARY.json)

## Configuration

- [`agent/agent_config.yaml`](../agent/agent_config.yaml) — skills, base query bounds, assignment queries
- No orchestrator code changes required for Investigator (registered via YAML + handler map)

## YouTube demo checklist

Record screen showing:

1. Run `uv run sitemind-benchmark` → all parts green / `SUMMARY.json` `"all_passed": true`
2. Parallel log: branch timings + max vs sum
3. Critic fail log: `verdict=fail` then recovery corrected answer
4. Coder log: `median_depth` from sandbox
5. Investigator log: headings + outbound links
6. (Optional) Live crawl: `docker compose up`, `uv run sitemind-api`, submit URL, `uv run sitemind-worker`

## Production readiness (honest)

| Area | Status |
|------|--------|
| DAG engine + assignment proofs | Done |
| Worker + Playwright/HTTP crawl | MVP done |
| Rate limits + SSRF URL safety | Done |
| PostgreSQL persistence | Schema + worker (needs `alembic upgrade`) |
| Qdrant embeddings, hybrid RAG | Not implemented |
| Full 50+ artifact demo crawl | Needs live run + budget |
| LLM providers (Groq/OpenRouter/Inception) | Config only |
| Vercel/Render deploy | Spec only |

**Verdict:** Meets the **DAG assignment**; **not** fully production-ready as the complete SiteMind PRD.
