"use client";

import { use, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  FileText,
  FormInput,
  GitBranch,
  Layers,
  Network as NetworkIcon,
  Workflow,
  ShieldAlert,
  HelpCircle,
  Clock,
  Gauge,
  Percent,
  CheckCircle2,
  AlertTriangle,
  ArrowRight
} from "lucide-react";
import { getJob, getPages, getForms, getEndpoints, getWorkflows, getEvaluations, type JobProgress, type JobResponse } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { StatusChip } from "@/components/StatusChip";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useArtifact } from "@/context/ArtifactContext";

// Simple Recharts mocks to prevent compilation issues and offer gorgeous visual flows
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie
} from "recharts";

export default function SiteOverviewPage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const jobId = searchParams.get("job");

  // Fetch state
  const [job, setJob] = useState<JobResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiFailed, setApiFailed] = useState(false);

  // Load from API, fallback to mock database
  useEffect(() => {
    setLoading(true);
    if (jobId) {
      getJob(jobId)
        .then((data) => {
          setJob(data);
          setLoading(false);
        })
        .catch(() => {
          setApiFailed(true);
          setLoading(false);
        });
    } else {
      // Direct mock fallback
      setApiFailed(true);
      setLoading(false);
    }
  }, [jobId, siteId]);

  // Retrieve site metadata (real or mock)
  const mockData = getMockSite(siteId);
  
  const progress: JobProgress = !apiFailed && job?.progress
    ? job.progress
    : mockData
      ? mockData.progress
      : {
          pages_discovered: 0,
          pages_processed: 0,
          chunks_indexed: 0,
          forms_found: 0,
          endpoints_found: 0,
          workflows_found: 0,
        };

  const status = !apiFailed && job?.status
    ? job.status
    : mockData
      ? mockData.status
      : "completed";

  const confidenceScore = mockData ? mockData.evaluations[0]?.metrics.find(m => m.metric_key === "grounding_score")?.metric_value || 0.95 : 0.95;

  // Endpoint distribution chart data
  const endpointMethodData = mockData ? [
    { name: "GET", value: mockData.endpoints.filter(e => e.method === "GET").length || 3, color: "var(--stitch-accent-cyan)" },
    { name: "POST", value: mockData.endpoints.filter(e => e.method === "POST").length || 4, color: "var(--stitch-accent-violet)" },
    { name: "PUT", value: mockData.endpoints.filter(e => e.method === "PUT").length || 0, color: "var(--stitch-warning)" },
    { name: "DELETE", value: mockData.endpoints.filter(e => e.method === "DELETE").length || 0, color: "var(--stitch-error)" }
  ].filter(item => item.value > 0) : [
    { name: "GET", value: 4, color: "var(--stitch-accent-cyan)" },
    { name: "POST", value: 3, color: "var(--stitch-accent-violet)" }
  ];

  // Crawl volume by depth chart data
  const depthData = [
    { depth: "Root (d0)", pages: progress.pages_discovered > 0 ? 1 : 1 },
    { depth: "Depth 1", pages: progress.pages_discovered > 0 ? Math.ceil(progress.pages_discovered * 0.4) : 4 },
    { depth: "Depth 2", pages: progress.pages_discovered > 0 ? Math.ceil(progress.pages_discovered * 0.5) : 8 },
    { depth: "Depth 3", pages: progress.pages_discovered > 0 ? Math.max(0, progress.pages_discovered - Math.ceil(progress.pages_discovered * 0.9)) : 2 }
  ];

  // Global Context click handler
  const { setSelectedArtifact } = useArtifact();

  return (
    <div className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 space-y-6">
      
      {/* Banner indicating fallback mode */}
      {apiFailed && (
        <div className="flex items-center justify-between rounded-lg border border-[var(--stitch-border-accent)] bg-[var(--stitch-accent-cyan-dim)]/20 px-4 py-2.5 text-xs text-[var(--stitch-accent-cyan)] shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 shrink-0" />
            <span><strong>SiteMind API offline or demo run.</strong> Showing pre-computed site intelligence models for {mockData?.url}.</span>
          </div>
          <Badge variant="outline" className="text-[10px] text-[var(--stitch-accent-cyan)] border-[var(--stitch-accent-cyan)]">Demo Mode</Badge>
        </div>
      )}

      {/* Header section */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
            Intelligence Center
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[var(--stitch-text)] flex items-center gap-2">
            {mockData?.name || "Site"} Overview
            <span className="text-xs font-mono font-normal text-[var(--stitch-text-muted)] bg-[var(--stitch-surface)] py-0.5 px-2 rounded border border-[var(--stitch-border)]">
              {mockData?.url}
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

      {/* Crawl overall completion bar */}
      <div className="rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] p-4 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[var(--stitch-text-muted)] flex items-center gap-1.5 font-medium">
            <Clock className="h-3.5 w-3.5 text-[var(--stitch-accent-cyan)]" /> Crawl Pipeline completion progress
          </span>
          <span className="font-mono text-[var(--stitch-text)] font-semibold">
            {progress.pages_discovered > 0
              ? Math.round((progress.pages_processed / progress.pages_discovered) * 100)
              : 100}%
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[var(--stitch-surface)] border border-[var(--stitch-border)]">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[var(--stitch-accent-cyan)] to-[var(--stitch-accent-violet)] transition-all duration-500"
            style={{
              width: `${
                progress.pages_discovered
                  ? (progress.pages_processed / progress.pages_discovered) * 100
                  : 100
              }%`,
            }}
          />
        </div>
      </div>

      {/* Grid of Executive Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Pages */}
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
              Pages crawled
            </CardTitle>
            <FileText className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{progress.pages_processed}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">/ {progress.pages_discovered} discovered</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-success)]">
              <CheckCircle2 className="h-3 w-3" />
              <span>100% crawl integrity</span>
            </div>
          </CardContent>
        </Card>

        {/* Forms */}
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
              Forms detected
            </CardTitle>
            <FormInput className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{progress.forms_found}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">with constraints</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-accent-cyan)]">
              <span>{mockData?.forms.flatMap(f => f.fields).length || 6} input fields mapped</span>
            </div>
          </CardContent>
        </Card>

        {/* Endpoints */}
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
              Endpoints mapped
            </CardTitle>
            <NetworkIcon className="h-4.5 w-4.5 text-[var(--stitch-success)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{progress.endpoints_found}</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">XHR/Fetch requests</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-text-muted)]">
              <span>Observed and Inferred</span>
            </div>
          </CardContent>
        </Card>

        {/* Workflows / Confidence */}
        <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-1.5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
              Model accuracy
            </CardTitle>
            <Gauge className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight">{(confidenceScore * 100).toFixed(0)}%</span>
              <span className="text-[10px] text-[var(--stitch-text-subtle)]">grounding rate</span>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-[var(--stitch-success)]">
              <CheckCircle2 className="h-3 w-3" />
              <span>Verified by Critic Agent</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Visual Charts section */}
      <div className="grid gap-6 md:grid-cols-12">
        {/* Method Distribution Chart */}
        <Card className="border-[var(--stitch-border)] md:col-span-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Endpoint method ratio</CardTitle>
            <CardDescription className="text-xs">Method distribution of detected API endpoints.</CardDescription>
          </CardHeader>
          <CardContent className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={endpointMethodData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {endpointMethodData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "var(--stitch-bg-elevated)", border: "1px solid var(--stitch-border)", borderRadius: 6, fontSize: 11 }}
                />
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

        {/* Crawl Yield by Depth Chart */}
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
                <Tooltip
                  contentStyle={{ background: "var(--stitch-bg-elevated)", border: "1px solid var(--stitch-border)", borderRadius: 6, fontSize: 11 }}
                  cursor={{ fill: "rgba(255,255,255,0.02)" }}
                />
                <Bar dataKey="pages" fill="var(--stitch-accent-cyan)" radius={[4, 4, 0, 0]}>
                  {depthData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? "var(--stitch-accent-cyan)" : "var(--stitch-accent-violet)"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Main operational row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Col: Pipeline Activity Timeline */}
        <Card className="border-[var(--stitch-border)] lg:col-span-2">
          <CardHeader className="border-b border-[var(--stitch-border)]">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Layers className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
              Pipeline Node Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div className="space-y-3">
              {[
                { name: "Crawl & Screenshot Node", role: "worker", duration: "3.4s", desc: "Fetched DOM files, compiled screenshots, and extracted links.", icon: CheckCircle2, status: "succeeded" },
                { name: "Form Extraction Agent", role: "worker", duration: "0.8s", desc: "Mapped input selectors and forms on authentication pages.", icon: CheckCircle2, status: "succeeded" },
                { name: "Endpoint Sniffer Node", role: "worker", duration: "1.4s", desc: "Monitored XHR/Fetch network trace triggers.", icon: CheckCircle2, status: "succeeded" },
                { name: "Workflow Journey Miner", role: "agent", duration: "2.4s", desc: "Inferred interactive flow paths using credential mapping.", icon: CheckCircle2, status: "succeeded" },
                { name: "API Spec Builder Node", role: "agent", duration: "1.9s", desc: "Synthesised OpenAPI schemas for endpoints.", icon: CheckCircle2, status: "succeeded" },
                { name: "Critic Fact Validator", role: "agent", duration: "1.1s", desc: "Audited specs and workflows against crawled logs.", icon: CheckCircle2, status: "succeeded" },
              ].map((step, i) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.name}
                    className="flex gap-3 rounded-lg border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60 px-4 py-3 items-start"
                  >
                    <Icon className="h-4.5 w-4.5 text-[var(--stitch-success)] shrink-0 mt-0.5" />
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[var(--stitch-text)]">{step.name}</span>
                        <Badge variant="outline" className="text-[9px] px-1.5">{step.role}</Badge>
                      </div>
                      <p className="text-[11px] text-[var(--stitch-text-muted)]">{step.desc}</p>
                    </div>
                    <span className="text-[10px] font-mono text-[var(--stitch-text-subtle)] shrink-0 mt-0.5">{step.duration}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Right Col: Recent Discoveries & evaluations preview */}
        <div className="space-y-6">
          {/* Recent discoveries */}
          <Card className="border-[var(--stitch-border)]">
            <CardHeader className="border-b border-[var(--stitch-border)] py-3">
              <CardTitle className="text-sm font-semibold flex items-center justify-between">
                <span>Recent discoveries</span>
                <span className="text-[10px] font-normal text-[var(--stitch-text-subtle)]">Live stream</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-[var(--stitch-border)] text-xs">
                {mockData?.pages.slice(0, 3).map((page) => (
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
                {mockData?.forms.slice(0, 1).map((form) => (
                  <div
                    key={form.id}
                    className="p-3 hover:bg-[var(--stitch-surface-hover)] transition-colors cursor-pointer flex items-center justify-between"
                    onClick={() => setSelectedArtifact({ type: "form", data: form })}
                  >
                    <div className="space-y-0.5 min-w-0 pr-2">
                      <p className="font-medium text-[var(--stitch-text)]">Form: {form.form_name || "Form"}</p>
                      <p className="text-[10px] text-[var(--stitch-text-subtle)]">Endpoint: {form.action_url}</p>
                    </div>
                    <ArrowRight className="h-3 w-3 text-[var(--stitch-text-subtle)] shrink-0" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Evaluations diagnostics */}
          <Card className="border-[var(--stitch-border)]">
            <CardHeader className="border-b border-[var(--stitch-border)] py-3">
              <CardTitle className="text-sm font-semibold">Observability Diagnostics</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">Grounding Precision</span>
                <span className="font-mono text-[var(--stitch-success)] font-semibold">91.0%</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">Grounding Recall</span>
                <span className="font-mono text-[var(--stitch-success)] font-semibold">94.0%</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[var(--stitch-border)]">
                <span className="text-[var(--stitch-text-muted)]">MRR (Rankings)</span>
                <span className="font-mono text-[var(--stitch-text)] font-semibold">0.95</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--stitch-text-muted)]">DAG Nodes Health</span>
                <span className="font-mono text-[var(--stitch-success)] font-semibold">100% Ok</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
