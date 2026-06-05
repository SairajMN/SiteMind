export type ApiError = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type ApiEnvelope<T> = {
  data: T | null;
  error: ApiError | null;
};

export type CreateSiteRequest = {
  url: string;
  goal?: string;
  scope_policy?: "same_domain" | "subpaths" | "unrestricted";
  crawl_depth?: number;
  page_budget?: number;
  include_screenshots?: boolean;
  include_network_traces?: boolean;
};

export type CreateSiteResponse = {
  site_id: string;
  crawl_job_id: string;
  dag_run_id: string;
  status: string;
};

export type JobStatus = "queued" | "running" | "completed" | "failed" | "blocked";

export type JobProgress = {
  pages_discovered: number;
  pages_processed: number;
  chunks_indexed: number;
  forms_found: number;
  endpoints_found: number;
  workflows_found: number;
};

export type JobResponse = {
  job_id: string;
  site_id: string;
  status: JobStatus;
  progress: JobProgress;
  started_at: string | null;
  finished_at: string | null;
  error_summary: string | null;
};

// --- Pages ---
export type PageSummary = {
  id: string;
  url: string;
  canonical_url?: string;
  title?: string;
  depth: number;
  path?: string;
  status_code?: number;
  has_form: boolean;
  has_auth_hint: boolean;
  created_at: string;
};

export type PageListResponse = {
  pages: PageSummary[];
  total: number;
};

// --- Forms ---
export type FormFieldSummary = {
  id: string;
  name?: string;
  label?: string;
  field_type?: string;
  required: boolean;
  placeholder?: string;
};

export type FormSummary = {
  id: string;
  page_id: string;
  form_index: number;
  action_url?: string;
  method?: string;
  form_name?: string;
  confidence?: number;
  fields: FormFieldSummary[];
  created_at: string;
};

export type FormListResponse = {
  forms: FormSummary[];
  total: number;
};

// --- Endpoints ---
export type EndpointSummary = {
  id: string;
  page_id: string;
  request_url: string;
  method?: string;
  request_type?: string;
  status_code?: number;
  confidence?: number;
  observation_type?: string;
  created_at: string;
};

export type EndpointListResponse = {
  endpoints: EndpointSummary[];
  total: number;
};

// --- Workflows ---
export type WorkflowStepSummary = {
  id: string;
  step_index: number;
  page_id?: string;
  action_type?: string;
  selector?: string;
  endpoint_id?: string;
  description?: string;
  confidence?: number;
};

export type WorkflowSummary = {
  id: string;
  site_id: string;
  name?: string;
  summary?: string;
  confidence?: number;
  steps: WorkflowStepSummary[];
  created_at: string;
};

export type WorkflowListResponse = {
  workflows: WorkflowSummary[];
  total: number;
};

// --- API Specs ---
export type ApiSpecSummary = {
  id: string;
  site_id: string;
  workflow_id?: string;
  spec_json?: Record<string, unknown>;
  openapi_url?: string;
  created_at: string;
};

// --- Evaluations ---
export type MetricSchema = {
  metric_key: string;
  metric_value?: number;
  details_json?: Record<string, unknown>;
};

export type EvaluationSummary = {
  id: string;
  site_id: string;
  crawl_job_id?: string;
  status: string;
  metrics: MetricSchema[];
  created_at: string;
};

export type EvaluationListResponse = {
  evaluations: EvaluationSummary[];
  total: number;
};

// --- DAG ---
export type DagNodeSummary = {
  id: string;
  dag_run_id: string;
  node_key: string;
  node_type?: string;
  status: string;
  attempt_count: number;
  lane?: string;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
  error_json?: Record<string, unknown> | null;
  output_json?: Record<string, unknown> | null;
};

export type DagEdgeSummary = {
  id: string;
  dag_run_id: string;
  from_node_id: string;
  to_node_id: string;
  edge_type?: string;
};

export type DagRunDetail = {
  id: string;
  site_id: string;
  crawl_job_id: string;
  status: string;
  planner_version?: string;
  started_at?: string;
  finished_at?: string;
  nodes: DagNodeSummary[];
  edges: DagEdgeSummary[];
  created_at: string;
};

// --- Q&A ---
export type CitationSchema = {
  source_url?: string;
  artifact_type?: string;
  snippet?: string;
  score?: number;
  confidence?: number;
};

export type AskRequest = {
  question: string;
  artifact_types?: string[];
};

export type AskResponse = {
  answer_id: string;
  site_id: string;
  question: string;
  answer_text?: string;
  confidence?: number;
  critic_status?: string;
  citations: CitationSchema[];
  created_at: string;
};

function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return base.replace(/\/$/, "");
}

function buildUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const apiPath = normalized.startsWith("/api") ? normalized : `/api${normalized}`;
  return `${getApiBase()}${apiPath}`;
}

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = buildUrl(path);
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...init, headers });
  let envelope: ApiEnvelope<T>;

  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiClientError(
      "PARSE_ERROR",
      "Invalid JSON response from API",
      response.status,
    );
  }

  if (envelope.error) {
    throw new ApiClientError(
      envelope.error.code,
      envelope.error.message,
      response.status,
      envelope.error.details,
    );
  }

  if (!response.ok) {
    throw new ApiClientError(
      "HTTP_ERROR",
      `Request failed with status ${response.status}`,
      response.status,
    );
  }

  if (envelope.data === null) {
    throw new ApiClientError("EMPTY_DATA", "Response contained no data", response.status);
  }

  return envelope.data;
}

export function getEventsUrl(jobId: string): string {
  return buildUrl(`/jobs/${jobId}/events`);
}

export async function createSite(body: CreateSiteRequest): Promise<CreateSiteResponse> {
  return apiFetch<CreateSiteResponse>("/sites", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getJob(jobId: string): Promise<JobResponse> {
  return apiFetch<JobResponse>(`/jobs/${jobId}`);
}

export async function getPages(siteId: string): Promise<PageListResponse> {
  return apiFetch<PageListResponse>(`/sites/${siteId}/pages`);
}

export async function getForms(siteId: string): Promise<FormListResponse> {
  return apiFetch<FormListResponse>(`/sites/${siteId}/forms`);
}

export async function getEndpoints(siteId: string): Promise<EndpointListResponse> {
  return apiFetch<EndpointListResponse>(`/sites/${siteId}/endpoints`);
}

export async function getWorkflows(siteId: string): Promise<WorkflowListResponse> {
  return apiFetch<WorkflowListResponse>(`/sites/${siteId}/workflows`);
}

export async function getApiSpecs(siteId: string): Promise<ApiSpecSummary[]> {
  return apiFetch<ApiSpecSummary[]>(`/sites/${siteId}/api-specs`);
}

export async function getEvaluations(siteId: string): Promise<EvaluationListResponse> {
  return apiFetch<EvaluationListResponse>(`/sites/${siteId}/evaluations`);
}

export async function getDagRun(dagRunId: string): Promise<DagRunDetail> {
  return apiFetch<DagRunDetail>(`/dag-runs/${dagRunId}`);
}

export async function askQuestion(siteId: string, body: AskRequest): Promise<AskResponse> {
  return apiFetch<AskResponse>(`/sites/${siteId}/ask`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}