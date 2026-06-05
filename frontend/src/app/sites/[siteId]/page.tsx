"use client";

import { use, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  FileText,
  FormInput,
  Layers,
  Network as NetworkIcon,
  Clock,
  Gauge,
  ArrowRight
} from "lucide-react";
import {
  getJob, getPages, getForms, getEndpoints, getEvaluations,
  type JobProgress, type JobResponse,
  type PageSummary, type FormSummary, type EndpointSummary, type EvaluationSummary
} from "@/lib/api-client";
import { StatusChip } from "@/components/StatusChip";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie
} from "recharts";
import { useArtifact } from "@/context/ArtifactContext";

export default function SiteOverviewPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job");

  const [job, setJob] = useState<JobResponse | null>(null);
  const [pages, setPages] = useState<PageSummary[]>([]);
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [endpoints, setEndpoints] = useState<EndpointSummary[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const load = async () => {
      try {
        if (jobId) {
          const data = await getJob(jobId);
          setJob(data);
        }
        const [pagesRes, formsRes, endpointsRes, evalsRes] = await Promise.all([
          getPages(siteId).catch(() => null),
          getForms(siteId).catch(() => null),
          getEndpoints(siteId).catch(() => null),
          getEvaluations(siteId).catch(() => null),
        ]);
        if (pagesRes) setPages(pagesRes.pages);
        if (formsRes) setForms(formsRes.forms);
        if (endpointsRes) setEndpoints(endpointsRes.endpoints);
        if (evalsRes) setEvaluations(evalsRes.evaluations);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load site data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [jobId, siteId]);

  const progress: JobProgress = job?.progress ?? {
    pages_discovered: pages.length,
    pages_processed: pages.length,
    chunks_indexed: 0,
    forms_found: forms.length,
    endpoints_found: endpoints.length,
    workflows_found: 0,
  };
  const status = job?.status ?? (loading ? "running" : "completed");

  const confidenceScore = (() => {
    const latest = evaluations[0];
    if (!latest) return 0;
    const m = latest.metrics.find((x) => x.metric_key === "grounding_score");
    return m?.metric_value ?? 0;
  })();

  const endpointMethodData = [
    { name: "GET", value: endpoints.filter((e) => e.method === "GET").length, color: "var(--stitch-accent-cyan)" },
    { name: "POST", value: endpoints.filter((e) => e.method === "POST").length, color: "var(--stitch-accent-violet)" },
    { name: "PUT", value: endpoints.filter((e) => e.method === "PUT").length, color: "var(--stitch-warning)" },
    { name: "DELETE", value: endpoints.filter((e) => e.method === "DELETE").length, color: "var(--stitch-error)" },
  ].filter((item) => item.value > 0);

  const depthData = (() => {
    const buckets: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0 };
    pages.forEach((p) => { buckets[Math.min(3, p.depth)] = (buckets[Math.min(3, p.depth)] ?? 0) + 1; });
    return [
      { depth: "Root (d0)", pages: buckets[0] },
      { depth: "Depth 1", pages: buckets[1] },
      { depth: "Depth 2", pages: buckets[2] },
      { depth: "Depth 3", pages: buckets[3] },
    ];
  })();

  const { setSelectedArtifact } = useArtifact();

  const pipelineSteps = [
    { name: "Crawl & Screenshot Node", role: "worker", desc: "Fetched DOM files, compiled screenshots, and extracted links." },
    { name: "Form Extraction Agent", role: "worker", desc: "Mapped input selectors and forms on authentication pages." },
    { name: "Endpoint Sniffer Node", role: "worker", desc: "Monitored XHR/Fetch network trace triggers." },
    { name: "Workflow Journey Miner", role: "agent", desc: "Inferred interactive flow paths using credential mapping." },
    { name: "API Spec Builder Node", role: "agent", desc: "Synthesised OpenAPI schemas for endpoints." },
    { name: "Critic Fact Validator", role: "agent", desc: "Audited specs and workflows against crawled logs." },
  ];

  return (
    <div className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 space-y-6">
      {error && (
        <div className="rounded-lg border border-[var(--stitch-error)]/30 bg-[var(--stitch-error)]/5 px-4 py-2.5 text-xs text-[var(--stitch-error)]">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">Intelligence Center</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[var(--stitch-text)] flex items-center gap-2">
            Site Overview
            <span className="text-xs font-mono font-normal text-[var(--stitch-text-muted)] bg-[var(--stitch-surface)] py-0.5 px-2 rounded border border-[var(--stitch-border)]">
              {siteId}
            </span>
          </h1>
          <p className="mt-2 text-xs text-[var(--stitch-text-muted)]">
            Site ID: <code className="text-[var(--stitch-accent-cyan)]">{siteId}</code> · System enqueued and analyzed using a 12-node validation DAG.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusChip status={status} pulse />
          <span className="text-xs text-[var(--stitch-success)] font-medium flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--stitch-success)] animate-pulse" /> Live Pipeline
          </span>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] p-4 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[var(--stitch-text-muted)] flex items-center gap-1.5 font-medium">
            <Clock className="h-3.5 w-3.5 text-[var(--stitch-accent-cyan)]" /> Crawl Pipeline completion progress
          </span>
          <span className="font-mono text-[var(--stitch-text)] font-semibold">
            {progress.pages_discovered > 0 ? Math.round((progress.pages_processed / progress.pages_discovered) * 100) : 0}%
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[var(--stitch-surface)] border border-[var(--stitch-border)]">
          <div className="h-full rounded-full bg-gradient-to-r from-[var(--stitch-accent-cyan)] to-[var(--stitch-accent-violet)] transition-all duration-500"
            style={{ width: `${progress.pages_discovered ? (progress.pages_processed / progress.pages_discovered) * 100 : 0}%` }} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">Pages crawled</CardTitle>
            <FileText className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{progress.pages_processed}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">/ {progress.pages_discovered} discovered</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-text-muted)]">
              <span>{pages.length > 0 ? "Live from API" : "Awaiting data"}</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">Forms detected</CardTitle>
            <FormInput className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{forms.length}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">with constraints</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-accent-cyan)]">
              <span>{forms.reduce((s, f) => s + (f.fields?.length || 0), 0)} input fields mapped</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">Endpoints mapped</CardTitle>
            <NetworkIcon className="h-4.5 w-4.5 text-[var(--stitch-success)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{endpoints.length}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">XHR/Fetch requests</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-text-muted)]">
              <span>Observed and Inferred</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">Model accuracy</CardTitle>
            <Gauge className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{confidenceScore > 0 ? `${(confidenceScore * 100).toFixed(0)}%` : "—"}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">grounding rate</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-text-muted)]">
              <span>{evaluations.length > 0 ? "From latest evaluation" : "No evaluation yet"}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {endpointMethodData.length > 0 && (
        <div className="grid gap-6 md:grid-cols-12">
          <Card className="border-[var(--stitch-border)] md:col-span-4 flex flex-col justify-between">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Endpoint method ratio</CardTitle>
              <CardDescription className="text-xs">Method distribution of detected API endpoints.</CardDescription>
            </CardHeader>
            <CardContent className="h-48 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={endpointMethodData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                    {endpointMethodData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "var(--stitch-bg-elevated)", border: "1px solid var(--stitch-border)", borderRadius: 6, fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
            <div className="border-t border-[var(--stitch-border)] px-4 py-3 flex items-center justify-around text-xs text-[var(--stitch-text-muted)]">
              {endpointMethodData.map((item) => (
                <div key={item.name} className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                  <span>{item.name}: <strong>{item.value}</strong></span>
                </div>
              ))}
            </div>
          </Card>
          <Card className="border-[var(--stitch-border)] md:col-span-8">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Crawl structure discovery</CardTitle>
              <CardDescription className="text-xs">Count of mapped pages categorised by crawl hierarchy level.</CardDescription>
            </CardHeader>
            <CardContent className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={depthData}>
                  <XAxis dataKey="depth" stroke="var(--stitch-text-subtle)" fontSize={10} tickLine={false} />
                  <YAxis stroke="var(--stitch-text-subtle)" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ background: "var(--stitch-bg-elevated)", border: "1px solid var(--stitch-border)", borderRadius: 6, fontSize: 11 }} cursor={{ fill: "rgba(255,255,255,0.02)" }} />
                  <Bar dataKey="pages" fill="var(--stitch-accent-cyan)" radius={[4, 4, 0, 0]}>
                    {depthData.map((entry, index) => (<Cell key={`cell-${index}`} fill={index % 2 === 0 ? "var(--stitch-accent-cyan)" : "var(--stitch-accent-violet)"} />))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-[var(--stitch-border)] lg:col-span-2">
          <CardHeader className="border-b border-[var(--stitch-border)]">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Layers className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" /> Pipeline Node Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {pipelineSteps.map((step) => (
              <div key={step.name} className="flex gap-3 rounded-lg border border-[var(--stitch-border)] bg-[var(--stitch-bg
-elevated)]/60 px-4 py-3 items-start">
                <div className="flex-1 space-y-0.5">
                  <span className="text-xs font-semibold text-[var(--stitch-text)]">{step.name}</span>
                  <p className="text-[11px] text-[var(--stitch-text-muted)]">{step.desc}</p>
                </div>
                <span className="text-[10px] font-mono text-[var(--stitch-text-subtle)]">{step.role}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-[var(--stitch-border)]">
            <CardHeader className="border-b border-[var(--stitch-border)] py-3">
              <CardTitle className="text-sm font-semibold flex items-center justify-between">
                <span>Recent discoveries</span>
                <span className="text-[10px] font-normal text-[var(--stitch-text-subtle)]">Live stream</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-[var(--stitch-border)] text-xs">
                {pages.slice(0, 3).map((page) => (
                  <div
                    key={page.id}
                    className="p-3 hover:bg-[var(--stitch-surface-hover)] transition-colors cursor-pointer flex items-center justify-between"
                    onClick={() => setSelectedArtifact({ type: "page", data: page })}
                  >
                    <div className="space-y-0.5 min-w-0 pr-2">
                      <p className="font-medium truncate text-[var(--stitch-text)]">{page.title || "Untitled"}</p>
                      <p className="font-mono text-[10px] text-[var(--stitch-accent-cyan)] truncate">{page.url}</p>
                    </div>
                    <ArrowRight className="h-3 w-3 text-[var(--stitch-text-subtle)] shrink-0" />
                  </div>
                ))}
                {pages.length === 0 && forms.length === 0 && endpoints.length === 0 && (
                  <div className="p-6 text-center text-[var(--stitch-text-subtle)]">
                    No discoveries yet. Awaiting crawl results.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-[var(--stitch-border)]">
            <CardHeader className="border-b border-[var(--stitch-border)] py-3">
              <CardTitle className="text-sm font-semibold">Observability Diagnostics</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">Grounding Precision</span>
                <span className="font-mono text-[var(--stitch-text-muted)]">—</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">Grounding Recall</span>
                <span className="font-mono text-[var(--stitch-text-muted)]">—</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">MRR (Rankings)</span>
                <span className="font-mono text-[var(--stitch-text-muted)]">—</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--stitch-text-muted)]">DAG Nodes Health</span>
                <span className="font-mono text-[var(--stitch-text-muted)]">—</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
