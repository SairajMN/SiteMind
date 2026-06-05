import {
  PageSummary,
  FormSummary,
  EndpointSummary,
  WorkflowSummary,
  ApiSpecSummary,
  EvaluationSummary,
  DagRunDetail,
  AskResponse,
  JobResponse
} from "./api-client";

export interface MockSiteData {
  site_id: string;
  url: string;
  name: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: {
    pages_discovered: number;
    pages_processed: number;
    chunks_indexed: number;
    forms_found: number;
    endpoints_found: number;
    workflows_found: number;
  };
  pages: PageSummary[];
  forms: FormSummary[];
  endpoints: EndpointSummary[];
  workflows: WorkflowSummary[];
  apiSpecs: ApiSpecSummary[];
  evaluations: EvaluationSummary[];
  dagRun: DagRunDetail;
  qaResponses: Record<string, AskResponse>;
}

export const MOCK_SITES: Record<string, MockSiteData> = {
  "stripe": {
    site_id: "stripe",
    url: "https://stripe.com",
    name: "Stripe",
    status: "completed",
    progress: {
      pages_discovered: 45,
      pages_processed: 45,
      chunks_indexed: 184,
      forms_found: 12,
      endpoints_found: 28,
      workflows_found: 5,
    },
    pages: [
      { id: "str-p1", url: "https://stripe.com", title: "Stripe | Payment Infrastructure for the Internet", depth: 0, path: "/", status_code: 200, has_form: true, has_auth_hint: false, created_at: "2026-06-05T20:00:00Z" },
      { id: "str-p2", url: "https://stripe.com/payments", title: "Stripe Payments | Accept Payments Online", depth: 1, path: "/payments", status_code: 200, has_form: false, has_auth_hint: false, created_at: "2026-06-05T20:01:00Z" },
      { id: "str-p3", url: "https://dashboard.stripe.com/login", title: "Sign in to Stripe", depth: 1, path: "/login", status_code: 200, has_form: true, has_auth_hint: true, created_at: "2026-06-05T20:02:00Z" },
      { id: "str-p4", url: "https://stripe.com/checkout", title: "Stripe Checkout | Prebuilt Checkout Page", depth: 2, path: "/checkout", status_code: 200, has_form: true, has_auth_hint: false, created_at: "2026-06-05T20:03:00Z" },
      { id: "str-p5", url: "https://stripe.com/docs", title: "Stripe Documentation & API Reference", depth: 1, path: "/docs", status_code: 200, has_form: false, has_auth_hint: false, created_at: "2026-06-05T20:04:00Z" },
      { id: "str-p6", url: "https://stripe.com/pricing", title: "Stripe Pricing & Fee Calculator", depth: 1, path: "/pricing", status_code: 200, has_form: true, has_auth_hint: false, created_at: "2026-06-05T20:05:00Z" }
    ],
    forms: [
      {
        id: "str-f1",
        page_id: "str-p3",
        form_index: 0,
        form_name: "login_form",
        action_url: "https://api.stripe.com/v1/auth/login",
        method: "POST",
        confidence: 0.98,
        created_at: "2026-06-05T20:02:00Z",
        fields: [
          { id: "str-f1-fld1", name: "email", label: "Email address", field_type: "email", required: true, placeholder: "you@example.com" },
          { id: "str-f1-fld2", name: "password", label: "Password", field_type: "password", required: true }
        ]
      },
      {
        id: "str-f2",
        page_id: "str-p4",
        form_index: 0,
        form_name: "checkout_form",
        action_url: "https://api.stripe.com/v1/payments/checkout",
        method: "POST",
        confidence: 0.95,
        created_at: "2026-06-05T20:03:00Z",
        fields: [
          { id: "str-f2-fld1", name: "card_number", label: "Card number", field_type: "text", required: true, placeholder: "•••• •••• •••• ••••" },
          { id: "str-f2-fld2", name: "card_expiry", label: "Expiration", field_type: "text", required: true, placeholder: "MM / YY" },
          { id: "str-f2-fld3", name: "card_cvc", label: "CVC", field_type: "text", required: true, placeholder: "CVC" },
          { id: "str-f2-fld4", name: "card_name", label: "Name on card", field_type: "text", required: false }
        ]
      }
    ],
    endpoints: [
      { id: "str-e1", page_id: "str-p3", request_url: "https://api.stripe.com/v1/auth/login", method: "POST", request_type: "xhr", status_code: 200, confidence: 0.99, observation_type: "observed", created_at: "2026-06-05T20:02:00Z" },
      { id: "str-e2", page_id: "str-p4", request_url: "https://api.stripe.com/v1/payment_intents", method: "POST", request_type: "fetch", status_code: 201, confidence: 0.96, observation_type: "observed", created_at: "2026-06-05T20:03:15Z" },
      { id: "str-e3", page_id: "str-p4", request_url: "https://api.stripe.com/v1/payment_methods", method: "POST", request_type: "fetch", status_code: 200, confidence: 0.95, observation_type: "observed", created_at: "2026-06-05T20:03:10Z" },
      { id: "str-e4", page_id: "str-p5", request_url: "https://api.stripe.com/v1/search", method: "GET", request_type: "fetch", status_code: 200, confidence: 0.88, observation_type: "inferred", created_at: "2026-06-05T20:04:30Z" }
    ],
    workflows: [
      {
        id: "str-w1",
        site_id: "stripe",
        name: "User Authentication (Login)",
        summary: "Authenticates a user into the dashboard. Discovered via Stripe Sign-in screen form mapping.",
        confidence: 0.97,
        created_at: "2026-06-05T20:02:00Z",
        steps: [
          { id: "str-w1-s1", step_index: 1, page_id: "str-p3", action_type: "navigate", description: "User navigates to login page at dashboard.stripe.com/login", confidence: 1.0 },
          { id: "str-w1-s2", step_index: 2, page_id: "str-p3", action_type: "fill", selector: "input[name='email']", description: "Enters user email address credentials", confidence: 0.95 },
          { id: "str-w1-s3", step_index: 3, page_id: "str-p3", action_type: "click", selector: "button[type='submit']", endpoint_id: "str-e1", description: "Submits credentials to /v1/auth/login and receives session JWT", confidence: 0.98 }
        ]
      },
      {
        id: "str-w2",
        site_id: "stripe",
        name: "One-Click Stripe Checkout Flow",
        summary: "Handles instant credit card payments. Discovered via payment method binding and checkout page telemetry.",
        confidence: 0.94,
        created_at: "2026-06-05T20:03:00Z",
        steps: [
          { id: "str-w2-s1", step_index: 1, page_id: "str-p4", action_type: "navigate", description: "User visits payment gateway screen", confidence: 1.0 },
          { id: "str-w2-s2", step_index: 2, page_id: "str-p4", action_type: "fill", selector: "input[name='card_number']", description: "Enters Visa/Mastercard credentials", confidence: 0.93 },
          { id: "str-w2-s3", step_index: 3, page_id: "str-p4", action_type: "click", selector: "button.submit-btn", endpoint_id: "str-e3", description: "Triggers API create payment method request", confidence: 0.95 },
          { id: "str-w2-s4", step_index: 4, page_id: "str-p4", action_type: "network_hook", endpoint_id: "str-e2", description: "Invokes /v1/payment_intents confirmation code and completes payment verification", confidence: 0.92 }
        ]
      }
    ],
    apiSpecs: [
      {
        id: "str-spec1",
        site_id: "stripe",
        workflow_id: "str-w2",
        created_at: "2026-06-05T20:10:00Z",
        openapi_url: "https://stripe.com/api/spec.json",
        spec_json: {
          openapi: "3.0.3",
          info: {
            title: "Stripe Checkout & Billing API",
            description: "Automatically inferred API spec from crawled Stripe Checkout workflows.",
            version: "1.0.0",
            "x-confidence": 0.95
          },
          paths: {
            "/v1/auth/login": {
              post: {
                summary: "Submit login details",
                requestBody: {
                  required: true,
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        required: ["email", "password"],
                        properties: {
                          email: { type: "string", format: "email" },
                          password: { type: "string", format: "password" }
                        }
                      }
                    }
                  }
                },
                responses: {
                  200: { description: "Successful login token retrieval" }
                }
              }
            },
            "/v1/payment_intents": {
              post: {
                summary: "Confirm Payment Intent",
                requestBody: {
                  required: true,
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        required: ["amount", "currency"],
                        properties: {
                          amount: { type: "integer", description: "Amount in cents" },
                          currency: { type: "string", default: "usd" }
                        }
                      }
                    }
                  }
                },
                responses: {
                  201: { description: "Intent created successfully" }
                }
              }
            }
          }
        }
      }
    ],
    evaluations: [
      {
        id: "str-ev1",
        site_id: "stripe",
        status: "completed",
        created_at: "2026-06-05T20:12:00Z",
        metrics: [
          { metric_key: "pages_discovered", metric_value: 6 },
          { metric_key: "forms_found", metric_value: 2 },
          { metric_key: "endpoints_found", metric_value: 4 },
          { metric_key: "workflows_found", metric_value: 2 },
          { metric_key: "chunks_indexed", metric_value: 184 },
          { metric_key: "avg_answer_confidence", metric_value: 0.96 },
          { metric_key: "citation_rate", metric_value: 1.0 },
          { metric_key: "dag_node_failure_rate", metric_value: 0.0 },
          { metric_key: "answers_count", metric_value: 8 },
          { metric_key: "recall_at_k", metric_value: 0.94 },
          { metric_key: "precision_at_k", metric_value: 0.91 },
          { metric_key: "mrr", metric_value: 0.95 },
          { metric_key: "grounding_score", metric_value: 0.98 }
        ]
      }
    ],
    dagRun: {
      id: "str-dag1",
      site_id: "stripe",
      crawl_job_id: "str-job1",
      status: "succeeded",
      created_at: "2026-06-05T20:00:00Z",
      nodes: [
        { id: "str-n-p", dag_run_id: "str-dag1", node_key: "planner", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "0", duration_ms: 320, output_json: { goal: "Map checkout endpoints" } },
        { id: "str-n-c", dag_run_id: "str-dag1", node_key: "crawl", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "1", duration_ms: 3400, output_json: { pages_found: 6 } },
        { id: "str-n-d", dag_run_id: "str-dag1", node_key: "dom", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1200 },
        { id: "str-n-f", dag_run_id: "str-dag1", node_key: "form", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 850 },
        { id: "str-n-e", dag_run_id: "str-dag1", node_key: "endpoint", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1450 },
        { id: "str-n-a", dag_run_id: "str-dag1", node_key: "auth", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 900 },
        { id: "str-n-s", dag_run_id: "str-dag1", node_key: "screenshot", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 2200 },
        { id: "str-n-nt", dag_run_id: "str-dag1", node_key: "network_trace", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1800 },
        { id: "str-n-wm", dag_run_id: "str-dag1", node_key: "workflow_miner", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "3", duration_ms: 2400 },
        { id: "str-n-kb", dag_run_id: "str-dag1", node_key: "knowledge_builder", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "4", duration_ms: 3100 },
        { id: "str-n-ap", dag_run_id: "str-dag1", node_key: "api_generator", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "4", duration_ms: 1950 },
        { id: "str-n-ev", dag_run_id: "str-dag1", node_key: "evaluation", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "5", duration_ms: 1100 }
      ],
      edges: [
        { id: "e1", dag_run_id: "str-dag1", from_node_id: "str-n-p", to_node_id: "str-n-c" },
        { id: "e2", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-d" },
        { id: "e3", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-f" },
        { id: "e4", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-e" },
        { id: "e5", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-a" },
        { id: "e6", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-s" },
        { id: "e7", dag_run_id: "str-dag1", from_node_id: "str-n-c", to_node_id: "str-n-nt" },
        { id: "e8", dag_run_id: "str-dag1", from_node_id: "str-n-d", to_node_id: "str-n-wm" },
        { id: "e9", dag_run_id: "str-dag1", from_node_id: "str-n-wm", to_node_id: "str-n-kb" },
        { id: "e10", dag_run_id: "str-dag1", from_node_id: "str-n-wm", to_node_id: "str-n-ap" },
        { id: "e11", dag_run_id: "str-dag1", from_node_id: "str-n-kb", to_node_id: "str-n-ev" }
      ]
    },
    qaResponses: {
      "how does the check out workflow work?": {
        answer_id: "str-a1",
        site_id: "stripe",
        question: "How does the checkout workflow work?",
        answer_text: "The Stripe Checkout workflow relies on a single page form found at `/checkout`. The user inputs card credentials (number, expiry, cvc, name) which submits a POST request to `https://api.stripe.com/v1/payment_methods`. It then validates card details and triggers the confirmation backend via the `/v1/payment_intents` API endpoint, resulting in a HTTP 201 Created state.",
        confidence: 0.95,
        critic_status: "passed",
        citations: [
          { source_url: "https://stripe.com/checkout", artifact_type: "pages", snippet: "Stripe Checkout prebuilt checkout form collects credit cards securely", confidence: 0.98, score: 0.96 },
          { source_url: "https://api.stripe.com/v1/payment_methods", artifact_type: "endpoints", snippet: "Endpoint POST creates the payment methods with the token payload", confidence: 0.95, score: 0.89 }
        ],
        created_at: "2026-06-05T20:20:00Z"
      },
      "what fields are in the login page?": {
        answer_id: "str-a2",
        site_id: "stripe",
        question: "What fields are in the login page?",
        answer_text: "The login form located at `https://dashboard.stripe.com/login` contains two required inputs:\n1. **email**: Type email, required. Used for identity identification.\n2. **password**: Type password, required. Credentials submission is sent via POST to `/v1/auth/login`.",
        confidence: 0.98,
        critic_status: "passed",
        citations: [
          { source_url: "https://dashboard.stripe.com/login", artifact_type: "forms", snippet: "Form name login_form requires email address and password input field values.", confidence: 0.99, score: 0.98 }
        ],
        created_at: "2026-06-05T20:22:00Z"
      }
    }
  },
  "github": {
    site_id: "github",
    url: "https://github.com",
    name: "GitHub",
    status: "completed",
    progress: {
      pages_discovered: 88,
      pages_processed: 88,
      chunks_indexed: 342,
      forms_found: 18,
      endpoints_found: 44,
      workflows_found: 7,
    },
    pages: [
      { id: "git-p1", url: "https://github.com", title: "GitHub: Let's build from here", depth: 0, path: "/", status_code: 200, has_form: true, has_auth_hint: false, created_at: "2026-06-05T20:00:00Z" },
      { id: "git-p2", url: "https://github.com/login", title: "Sign in to GitHub · GitHub", depth: 1, path: "/login", status_code: 200, has_form: true, has_auth_hint: true, created_at: "2026-06-05T20:01:00Z" },
      { id: "git-p3", url: "https://github.com/join", title: "Create your account · GitHub", depth: 1, path: "/join", status_code: 200, has_form: true, has_auth_hint: false, created_at: "2026-06-05T20:01:30Z" },
      { id: "git-p4", url: "https://github.com/new", title: "Create a New Repository", depth: 2, path: "/new", status_code: 401, has_form: false, has_auth_hint: true, created_at: "2026-06-05T20:03:00Z" }
    ],
    forms: [
      {
        id: "git-f1",
        page_id: "git-p2",
        form_index: 0,
        form_name: "login_form",
        action_url: "https://github.com/session",
        method: "POST",
        confidence: 0.99,
        created_at: "2026-06-05T20:01:00Z",
        fields: [
          { id: "git-f1-fld1", name: "login", label: "Username or email address", field_type: "text", required: true },
          { id: "git-f1-fld2", name: "password", label: "Password", field_type: "password", required: true }
        ]
      }
    ],
    endpoints: [
      { id: "git-e1", page_id: "git-p2", request_url: "https://github.com/session", method: "POST", request_type: "xhr", status_code: 302, confidence: 0.99, observation_type: "observed", created_at: "2026-06-05T20:01:00Z" },
      { id: "git-e2", page_id: "git-p4", request_url: "https://github.com/repositories", method: "POST", request_type: "fetch", status_code: 401, confidence: 0.94, observation_type: "observed", created_at: "2026-06-05T20:03:00Z" }
    ],
    workflows: [
      {
        id: "git-w1",
        site_id: "github",
        name: "User Login & Redirect",
        summary: "Traditional authentication workflow with session establishment redirects.",
        confidence: 0.98,
        created_at: "2026-06-05T20:01:00Z",
        steps: [
          { id: "git-w1-s1", step_index: 1, page_id: "git-p2", action_type: "navigate", description: "Visit the sign in screen", confidence: 1.0 },
          { id: "git-w1-s2", step_index: 2, page_id: "git-p2", action_type: "fill", selector: "#login_field", description: "Enters username or email address", confidence: 0.98 },
          { id: "git-w1-s3", step_index: 3, page_id: "git-p2", action_type: "click", selector: "input[type='submit']", endpoint_id: "git-e1", description: "Clicks sign in, returns session cookie and redirects user home", confidence: 0.99 }
        ]
      }
    ],
    apiSpecs: [],
    evaluations: [
      {
        id: "git-ev1",
        site_id: "github",
        status: "completed",
        created_at: "2026-06-05T20:12:00Z",
        metrics: [
          { metric_key: "pages_discovered", metric_value: 4 },
          { metric_key: "forms_found", metric_value: 1 },
          { metric_key: "endpoints_found", metric_value: 2 },
          { metric_key: "workflows_found", metric_value: 1 },
          { metric_key: "chunks_indexed", metric_value: 342 },
          { metric_key: "avg_answer_confidence", metric_value: 0.94 },
          { metric_key: "citation_rate", metric_value: 0.92 },
          { metric_key: "dag_node_failure_rate", metric_value: 0.05 },
          { metric_key: "answers_count", metric_value: 14 }
        ]
      }
    ],
    dagRun: {
      id: "git-dag1",
      site_id: "github",
      crawl_job_id: "git-job1",
      status: "succeeded",
      created_at: "2026-06-05T20:00:00Z",
      nodes: [
        { id: "git-n-p", dag_run_id: "git-dag1", node_key: "planner", node_type: "agent", status: "succeeded", attempt_count: 1, lane: "0", duration_ms: 400 },
        { id: "git-n-c", dag_run_id: "git-dag1", node_key: "crawl", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "1", duration_ms: 6700 },
        { id: "git-n-d", dag_run_id: "git-dag1", node_key: "dom", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1900 },
        { id: "git-n-f", dag_run_id: "git-dag1", node_key: "form", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1100 },
        { id: "git-n-e", dag_run_id: "git-dag1", node_key: "endpoint", node_type: "worker", status: "failed", attempt_count: 2, lane: "2", duration_ms: 800, error_json: { code: "RATE_LIMIT", message: "IP blocked temporarily" } },
        { id: "git-n-a", dag_run_id: "git-dag1", node_key: "auth", node_type: "worker", status: "succeeded", attempt_count: 1, lane: "2", duration_ms: 1500 }
      ],
      edges: [
        { id: "ge1", dag_run_id: "git-dag1", from_node_id: "git-n-p", to_node_id: "git-n-c" },
        { id: "ge2", dag_run_id: "git-dag1", from_node_id: "git-n-c", to_node_id: "git-n-d" },
        { id: "ge3", dag_run_id: "git-dag1", from_node_id: "git-n-c", to_node_id: "git-n-f" },
        { id: "ge4", dag_run_id: "git-dag1", from_node_id: "git-n-c", to_node_id: "git-n-e" },
        { id: "ge5", dag_run_id: "git-dag1", from_node_id: "git-n-c", to_node_id: "git-n-a" }
      ]
    },
    qaResponses: {}
  },
  "linear": {
    site_id: "linear",
    url: "https://linear.app",
    name: "Linear",
    status: "completed",
    progress: {
      pages_discovered: 25,
      pages_processed: 25,
      chunks_indexed: 110,
      forms_found: 4,
      endpoints_found: 14,
      workflows_found: 3,
    },
    pages: [
      { id: "lin-p1", url: "https://linear.app", title: "Linear - The issue tracker you don't hate", depth: 0, path: "/", status_code: 200, has_form: false, has_auth_hint: false, created_at: "2026-06-05T20:00:00Z" },
      { id: "lin-p2", url: "https://linear.app/features", title: "Linear Features | Issues, Cycles, Roadmaps", depth: 1, path: "/features", status_code: 200, has_form: false, has_auth_hint: false, created_at: "2026-06-05T20:01:00Z" }
    ],
    forms: [],
    endpoints: [],
    workflows: [],
    apiSpecs: [],
    evaluations: [],
    dagRun: {
      id: "lin-dag1",
      site_id: "linear",
      crawl_job_id: "lin-job1",
      status: "succeeded",
      created_at: "2026-06-05T20:00:00Z",
      nodes: [],
      edges: []
    },
    qaResponses: {}
  }
};

export function getMockSite(siteId: string): MockSiteData | undefined {
  const normalized = siteId.toLowerCase();
  for (const key of Object.keys(MOCK_SITES)) {
    if (normalized.includes(key)) {
      return MOCK_SITES[key];
    }
  }
  return MOCK_SITES["stripe"]; // default fallback
}
