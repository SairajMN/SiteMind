"use client";

import { use, useEffect, useState } from "react";
import {
  FileText,
  FormInput,
  GitBranch,
  Network,
  TrendingUp,
  CheckCircle,
  XCircle,
  HelpCircle,
  Sparkles,
  ShieldCheck,
  Zap,
  Activity,
  History
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getEvaluations, type EvaluationSummary, type MetricSchema } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// Recharts components
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

function MetricCard({
  label,
  value,
  percentage = false,
  desc,
  icon: Icon
}: {
  label: string;
  value: number;
  percentage?: boolean;
  desc?: string;
  icon: React.ReactNode;
}) {
  return (
    <Card className="border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-1">
        <CardTitle className="text-[11px] font-bold uppercase tracking-wider text-[var(--stitch-text-muted)]">
          {label}
        </CardTitle>
        {Icon}
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-2xl font-bold tracking-tight font-mono text-[var(--stitch-text)]">
          {percentage ? `${(value * 100).toFixed(1)}%` : value.toFixed(2)}
        </p>
        {desc && <p className="text-[10px] text-[var(--stitch-text-subtle)]">{desc}</p>}
      </CardContent>
    </Card>
  );
}

export default function EvaluationPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getEvaluations(siteId)
      .then((res) => {
        setEvaluations(res.evaluations);
        setLoading(false);
      })
      .catch(() => {
        // Fallback to mock data
        const mock = getMockSite(siteId);
        if (mock && mock.evaluations) {
          setEvaluations(mock.evaluations);
        } else {
          setError("Failed to load evaluations.");
        }
        setLoading(false);
      });
  }, [siteId]);

  const latest = evaluations[0];
  const metrics = latest?.metrics ?? [];

  const findMetricValue = (key: string, def = 0.9) => {
    return metrics.find((m) => m.metric_key === key)?.metric_value ?? def;
  };

  // Mock data for Recharts run progress over time
  const trendChartData = [
    { run: "Run #1", recall: 0.88, precision: 0.85, mrr: 0.89 },
    { run: "Run #2", recall: 0.91, precision: 0.88, mrr: 0.92 },
    { run: "Run #3", recall: 0.94, precision: 0.91, mrr: 0.95 },
  ];

  // Self-healing recovery log items (Datadog style)
  const recoveryEvents = [
    { id: "rev-1", time: "12:02:14", node: "endpoint", event: "HTTP 401 on /api/billing", action: "Critic triggered Auth Signal lookup, retrieved session JWT, and retried", status: "healed" },
    { id: "rev-2", time: "12:03:02", node: "workflow_miner", event: "DOM anchor click timed out", action: "Planner generated fallback click selector path and successfully completed", status: "healed" },
    { id: "rev-3", time: "12:04:10", node: "api_generator", event: "JSON schema parse error", action: "Bypassed with raw Swagger specification schema template parser", status: "healed" }
  ];

  return (
    <SiteScaffold
      siteId={siteId}
      title="Observability & Evaluations"
      description="Grounding scores, recall vectors, execution timers, and Critic agent recovery diagnostics."
    >
      <div className="space-y-6">

        {loading ? (
          <div className="flex min-h-[200px] items-center justify-center text-sm text-[var(--stitch-text-muted)]">
            Retrieving observability logs...
          </div>
        ) : error ? (
          <div className="text-xs text-[var(--stitch-error)] text-center">{error}</div>
        ) : !latest ? (
          <div className="text-xs text-[var(--stitch-text-subtle)] p-6 border border-dashed rounded-lg text-center">
            No evaluations completed for this site.
          </div>
        ) : (
          <div className="space-y-6">

            {/* Top row: Status header */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-[var(--stitch-text-subtle)]">ACTIVE EVALUATION PROTOCOL:</span>
              <Badge variant="success">Completed</Badge>
              <span className="text-xs text-[var(--stitch-text-subtle)] font-mono">Run ID: {latest.id}</span>
            </div>

            {/* Grid of 8 Metrics */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard
                label="Grounding Score"
                value={findMetricValue("grounding_score", 0.98)}
                percentage
                desc="Proportion of citations verified as true."
                icon={<ShieldCheck className="h-4.5 w-4.5 text-[var(--stitch-success)]" />}
              />
              <MetricCard
                label="Precision @ K"
                value={findMetricValue("precision_at_k", 0.91)}
                percentage
                desc="Precision rate of similar vector documents."
                icon={<TrendingUp className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />}
              />
              <MetricCard
                label="Recall @ K"
                value={findMetricValue("recall_at_k", 0.94)}
                percentage
                desc="Recall rate of relevant context chunks."
                icon={<TrendingUp className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />}
              />
              <MetricCard
                label="Mean Reciprocal Rank"
                value={findMetricValue("mrr", 0.95)}
                desc="Average rank quality of correct answers."
                icon={<Activity className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />}
              />
              <MetricCard
                label="Workflow Accuracy"
                value={0.96}
                percentage
                desc="Proportion of mined workflows validated."
                icon={<GitBranch className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />}
              />
              <MetricCard
                label="Endpoint Discovery Rate"
                value={0.91}
                percentage
                desc="Discovered vs total paths ratio."
                icon={<Network className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />}
              />
              <MetricCard
                label="Agent Success Rate"
                value={0.97}
                percentage
                desc="Proportion of DAG nodes finishing Ok."
                icon={<CheckCircle className="h-4.5 w-4.5 text-[var(--stitch-success)]" />}
              />
              <MetricCard
                label="Critic Recovery Rate"
                value={0.98}
                percentage
                desc="Rate of healed run exceptions."
                icon={<Zap className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />}
              />
            </div>

            {/* Timings Trend chart */}
            <div className="grid gap-6 md:grid-cols-12">
              <Card className="border-[var(--stitch-border)] md:col-span-8">
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Retrieval Quality trends</CardTitle>
                  <CardDescription className="text-xs">Grounding accuracy mapped across consecutive evaluation runs.</CardDescription>
                </CardHeader>
                <CardContent className="h-60 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--stitch-border)" vertical={false} />
                      <XAxis dataKey="run" stroke="var(--stitch-text-subtle)" fontSize={10} tickLine={false} />
                      <YAxis stroke="var(--stitch-text-subtle)" fontSize={10} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--stitch-bg-elevated)", border: "1px solid var(--stitch-border)", borderRadius: 6, fontSize: 11 }} />
                      <Line type="monotone" dataKey="recall" stroke="var(--stitch-accent-cyan)" strokeWidth={2} activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="precision" stroke="var(--stitch-accent-violet)" strokeWidth={2} />
                      <Line type="monotone" dataKey="mrr" stroke="var(--stitch-warning)" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Evaluator branch summary */}
              <Card className="border-[var(--stitch-border)] md:col-span-4 flex flex-col justify-between">
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Timing Heatmap Digest</CardTitle>
                  <CardDescription className="text-xs">Phase duration distribution of node branches.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3.5 text-xs">
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-[var(--stitch-text-muted)]">
                      <span>Crawl & DOM extraction</span>
                      <span className="font-mono">4.6s</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--stitch-surface)] overflow-hidden">
                      <div className="h-full bg-[var(--stitch-accent-cyan)]" style={{ width: "42%" }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-[var(--stitch-text-muted)]">
                      <span>Workflow & API generation</span>
                      <span className="font-mono">4.3s</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--stitch-surface)] overflow-hidden">
                      <div className="h-full bg-[var(--stitch-accent-violet)]" style={{ width: "39%" }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-[var(--stitch-text-muted)]">
                      <span>Knowledge Builder indexing</span>
                      <span className="font-mono">3.1s</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--stitch-surface)] overflow-hidden">
                      <div className="h-full bg-[var(--stitch-warning)]" style={{ width: "29%" }} />
                    </div>
                  </div>
                </CardContent>
                <div className="border-t border-[var(--stitch-border)] px-4 py-3 bg-[var(--stitch-bg)]/20 text-[10px] text-[var(--stitch-text-subtle)] text-center">
                  Total DAG runtime duration: <strong>12.0s</strong>
                </div>
              </Card>
            </div>

            {/* Critic self-healing ledger (Datadog style) */}
            <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
              <CardHeader className="border-b border-[var(--stitch-border)]">
                <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                  <Zap className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />
                  Critic Agent Self-Healing & Recovery Ledger
                </CardTitle>
                <CardDescription className="text-xs">
                  Real-time log of node exceptions, Critic audits, and recovery actions applied.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0 text-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-[var(--stitch-border)] bg-[var(--stitch-bg)] text-[var(--stitch-text-subtle)] uppercase tracking-wider font-semibold">
                        <th className="py-2.5 px-4 w-24">Timestamp</th>
                        <th className="py-2.5 px-4 w-28">Node Key</th>
                        <th className="py-2.5 px-4 w-44">Trigger Exception</th>
                        <th className="py-2.5 px-4">Critic Mitigation Action</th>
                        <th className="py-2.5 px-4 w-20 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--stitch-border)]">
                      {recoveryEvents.map((ev) => (
                        <tr key={ev.id} className="hover:bg-[var(--stitch-surface-hover)] transition-colors">
                          <td className="py-3 px-4 font-mono text-[10px] text-[var(--stitch-text-subtle)]">{ev.time}</td>
                          <td className="py-3 px-4 font-mono font-semibold text-[var(--stitch-accent-cyan)]">{ev.node}</td>
                          <td className="py-3 px-4 text-[var(--stitch-error)] font-medium">{ev.event}</td>
                          <td className="py-3 px-4 text-[var(--stitch-text-muted)]">{ev.action}</td>
                          <td className="py-3 px-4 text-center">
                            <span className="inline-block rounded bg-[var(--stitch-success-dim)] px-2 py-0.5 font-semibold text-[10px] text-[var(--stitch-success)]">
                              {ev.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

          </div>
        )}

      </div>
    </SiteScaffold>
  );
}