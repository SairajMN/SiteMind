# SiteMind — API Specification (MVP)

Base URL: `{API_BASE}/api`  
Content-Type: `application/json`  
Envelope: all JSON responses use:

```json
{
  "data": { },
  "error": null
}
```

On error:

```json
{
  "data": null,
  "error": {
    "code": "INVALID_URL",
    "message": "Human-readable message",
    "details": {}
  }
}
```

**Confidence: 90** — Consistent envelope simplifies Stitch frontend client code.

---

## Error codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_URL` | 400 | Malformed or disallowed URL |
| `SCOPE_VIOLATION` | 400 | URL outside scope policy |
| `NOT_FOUND` | 404 | Resource missing |
| `JOB_NOT_READY` | 409 | Action requires completed crawl |
| `INSUFFICIENT_EVIDENCE` | 422 | Q&A below retrieval threshold |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected failure |

---

## Sites and jobs

### `POST /api/sites`

Creates site, crawl job, and DAG run; enqueues worker.

**Request**

```json
{
  "url": "https://example.com",
  "goal": "Analyze website structure and workflows",
  "scope_policy": "same_domain",
  "crawl_depth": 3,
  "page_budget": 60,
  "include_screenshots": true,
  "include_network_traces": true
}
```

**Response `201`**

```json
{
  "data": {
    "site_id": "550e8400-e29b-41d4-a716-446655440000",
    "crawl_job_id": "660e8400-e29b-41d4-a716-446655440001",
    "dag_run_id": "770e8400-e29b-41d4-a716-446655440002",
    "status": "queued"
  },
  "error": null
}
```

---

### `GET /api/jobs/{job_id}`

**Response `200`**

```json
{
  "data": {
    "job_id": "uuid",
    "site_id": "uuid",
    "status": "running",
    "progress": {
      "pages_discovered": 24,
      "pages_processed": 18,
      "chunks_indexed": 52,
      "forms_found": 3,
      "endpoints_found": 8,
      "workflows_found": 1
    },
    "started_at": "2026-06-02T12:00:00Z",
    "finished_at": null,
    "error_summary": null
  },
  "error": null
}
```

`status`: `queued` | `running` | `completed` | `failed` | `blocked`

---

### `GET /api/jobs/{job_id}/events` (SSE)

`Content-Type: text/event-stream`  
Used by Stitch dashboard for live progress.

**Event format**

```
event: job.progress
data: {"job_id":"uuid","pages_discovered":10,"chunks_indexed":20}

event: dag.node.completed
data: {"dag_run_id":"uuid","node_key":"dom","status":"succeeded","duration_ms":1200}

event: artifact.created
data: {"site_id":"uuid","artifact_type":"form","count":1}
```

| Event | Payload highlights |
|-------|-------------------|
| `job.status` | `status`, `error_summary` |
| `job.progress` | counts object |
| `dag.node.started` | `node_key`, `node_type` |
| `dag.node.completed` | `node_key`, `status`, `duration_ms`, `artifacts_created` |
| `artifact.created` | `artifact_type`, `count` |
| `evaluation.updated` | `evaluation_id` |

Reconnect: client sends `Last-Event-ID` header; server replays from Redis stream if available.

---

## Site resources

### `GET /api/sites/{site_id}`

Site summary + latest job status.

---

### `GET /api/sites/{site_id}/pages`

Query: `limit`, `offset`, `depth`, `has_form`, `has_auth_hint`

```json
{
  "data": {
    "items": [
      {
        "id": "uuid",
        "url": "https://example.com/about",
        "title": "About",
        "depth": 1,
        "status_code": 200,
        "has_form": false,
        "has_auth_hint": false,
        "confidence": 0.95
      }
    ],
    "total": 24
  },
  "error": null
}
```

---

### `GET /api/sites/{site_id}/forms`

Nested `fields` array per form.

---

### `GET /api/sites/{site_id}/endpoints`

Includes `observation_type`: `observed` | `inferred`, `confidence`, `request_url`, `method`.

---

### `GET /api/sites/{site_id}/workflows`

Includes `steps[]` with `step_index`, `action_type`, `selector`, `page_id`, `endpoint_id`, `confidence`.

---

### `GET /api/sites/{site_id}/chunks`

Retrieval corpus browse for Knowledge Base screen.

Query: `artifact_type`, `q`, `min_confidence`, `limit`, `offset`

---

## Q&A

### `POST /api/sites/{site_id}/ask`

**Request**

```json
{
  "question": "How does login work?",
  "filters": {
    "artifact_types": ["auth", "form", "page"]
  },
  "top_k": 8
}
```

**Response `200`**

```json
{
  "data": {
    "answer_id": "uuid",
    "answer": "Login is presented on /login via email and password fields…",
    "confidence": 0.82,
    "citations": [
      {
        "chunk_id": "uuid",
        "source_url": "https://example.com/login",
        "artifact_type": "auth",
        "snippet": "Sign in with your email",
        "score": 0.91
      }
    ],
    "critic_status": "passed"
  },
  "error": null
}
```

`critic_status`: `passed` | `failed` | `recovered` | `refused`

**Response `422`** when evidence below threshold (`INSUFFICIENT_EVIDENCE`).

---

## API generation

### `POST /api/sites/{site_id}/generate-api`

**Request**

```json
{
  "workflow_id": "uuid"
}
```

**Response `201`**

```json
{
  "data": {
    "generated_api_id": "uuid",
    "workflow_id": "uuid",
    "spec_json": {
      "openapi": "3.0.3",
      "info": { "title": "Inferred workflow API", "version": "0.1.0" },
      "paths": {}
    },
    "warnings": ["Path /api/checkout inferred from form action; not directly observed"]
  },
  "error": null
}
```

---

## DAG

### `GET /api/dag-runs/{dag_run_id}`

**Response `200`**

```json
{
  "data": {
    "dag_run_id": "uuid",
    "status": "running",
    "planner_version": "1.0.0",
    "nodes": [
      {
        "id": "uuid",
        "node_key": "crawl",
        "node_type": "crawl",
        "status": "succeeded",
        "attempt_count": 1,
        "duration_ms": 45000,
        "lane": 0,
        "error_json": null
      },
      {
        "id": "uuid",
        "node_key": "dom",
        "node_type": "extractor",
        "status": "running",
        "attempt_count": 1,
        "duration_ms": null,
        "lane": 1,
        "error_json": null
      }
    ],
    "edges": [
      { "from_node_id": "uuid", "to_node_id": "uuid", "edge_type": "depends_on" }
    ]
  },
  "error": null
}
```

`lane` groups parallel branches for React Flow layout (Stitch DAG screen).

---

## Evaluation

### `GET /api/sites/{site_id}/evaluations`

Query: `crawl_job_id` (optional)

```json
{
  "data": {
    "evaluations": [
      {
        "id": "uuid",
        "created_at": "2026-06-02T13:00:00Z",
        "metrics": [
          { "metric_name": "recall_at_5", "metric_value": 0.72, "metric_unit": "ratio" },
          { "metric_name": "grounding_score", "metric_value": 0.88, "metric_unit": "ratio" },
          { "metric_name": "node_failure_rate", "metric_value": 0.08, "metric_unit": "ratio" }
        ]
      }
    ]
  },
  "error": null
}
```

---

## Health

### `GET /health`

```json
{ "status": "ok", "postgres": "ok", "redis": "ok", "qdrant": "ok" }
```

---

## Authentication (MVP)

No auth on API for hackathon MVP. Deploy behind private network or add API key header in Phase 7.

**Confidence: 88** — SSE and pagination suffice for Stitch UI; auth deferred intentionally.
