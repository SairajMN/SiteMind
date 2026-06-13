"use client";

import { useState } from "react";
import {
  Search, Sparkles, Loader2, CheckCircle, XCircle, Clock,
  ArrowRight, Globe, ShieldCheck, Activity, Terminal, Image,
  Play, ChevronDown, BarChart3, Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { runComparison, type ComparisonResult, type ComparisonItem, type ComparisonNode, type BrowserAction } from "@/lib/api-client";

const PRESETS = [
  "Compare top 3 Hugging Face text-generation models sorted by likes",
  "Compare top 5 GitHub repositories sorted by stars",
  "Compare best SaaS project management tools",
  "Compare top AI image generation APIs by price",
];

const DAG_STEPS = ["Planner", "Browser", "Distiller", "Critic", "Formatter", "Replay"];

export default function ComparePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);

  async function handleSubmit(q?: string) {
    const qText = q || query;
    if (!qText.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setQuery(qText);
    setLoadingStep(0);

    const stepInterval = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, DAG_STEPS.length - 1));
    }, 4000);

    try {
      const res = await runComparison({ query: qText.trim() });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen bg-[#07070a] text-slate-100">
      <div className="pointer-events-none absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900 via-transparent to-transparent" />

      {/* Header */}
      <header className="relative z-10 border-b border-[var(--stitch-border)] bg-[#07070a]/60 backdrop-blur-md px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--stitch-accent-cyan-dim)] ring-1 ring-[var(--stitch-border-accent)]">
              <BarChart3 className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
            </div>
            <span className="text-sm font-semibold tracking-tight">
              Site<span className="text-gradient font-bold">Mind</span>
              <span className="ml-2 text-[var(--stitch-text-subtle)]">/ Compare</span>
            </span>
          </div>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-6xl px-6 py-8 space-y-8">
        {/* Title */}
        <div className="space-y-3">
          <div className="inline-flex">
            <Badge variant="cyan" className="gap-1.5 py-1 px-3 bg-[var(--stitch-accent-cyan-dim)]/40 border-[var(--stitch-border-accent)]">
              <Zap className="h-3 w-3 text-[var(--stitch-accent-cyan)] animate-pulse" />
              Browser Comparison Intelligence
            </Badge>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Compare anything across the web
          </h1>
          <p className="text-sm text-[var(--stitch-text-muted)] max-w-2xl">
            Real browser interactions, structured extraction, critic-validated results. The agent navigates websites, applies filters, and extracts evidence-backed comparison data.
          </p>
        </div>

        {/* Query Input */}
        <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60 backdrop-blur-md">
          <CardContent className="p-4">
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-3">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-[var(--stitch-text-subtle)]" />
                  <Input
                    placeholder="e.g. Compare top 3 Hugging Face text-generation models sorted by likes"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                    className="pl-9 h-10 border-[var(--stitch-border)] bg-[var(--stitch-surface)]/80 focus:border-[var(--stitch-border-strong)]"
                    autoFocus
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="bg-[var(--stitch-accent-cyan)] hover:bg-[var(--stitch-accent-cyan)]/90 text-slate-900 font-bold px-6 shrink-0"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <><Play className="h-4 w-4 mr-1" /> Compare</>
                  )}
                </Button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] text-[var(--stitch-text-subtle)] mr-1 self-center">Try:</span>
                {PRESETS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => { setQuery(p); handleSubmit(p); }}
                    disabled={loading}
                    className="rounded bg-[var(--stitch-surface)] border border-[var(--stitch-border)] px-2.5 py-1 text-[10px] text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)] hover:border-[var(--stitch-border-strong)] transition-colors disabled:opacity-50"
                  >
                    {p.length > 50 ? p.slice(0, 50) + "..." : p}
                  </button>
                ))}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Loading DAG Visualization */}
        {loading && (
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin text-[var(--stitch-accent-cyan)]" />
                Executing Comparison Pipeline
              </CardTitle>
              <CardDescription className="text-xs">
                Real browser actions in progress...
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-1 overflow-x-auto pb-2">
                {DAG_STEPS.map((step, i) => (
                  <div key={step} className="flex items-center">
                    <div className={cn(
                      "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium whitespace-nowrap transition-all duration-500",
                      i < loadingStep && "bg-[var(--stitch-success-dim)] text-[var(--stitch-success)] border border-[var(--stitch-success)]/30",
                      i === loadingStep && "bg-[var(--stitch-accent-cyan-dim)] text-[var(--stitch-accent-cyan)] border border-[var(--stitch-accent-cyan)]/30 animate-pulse",
                      i > loadingStep && "bg-[var(--stitch-surface)] text-[var(--stitch-text-subtle)] border border-[var(--stitch-border)]",
                    )}>
                      {i < loadingStep ? <CheckCircle className="h-3 w-3" /> : i === loadingStep ? <Loader2 className="h-3 w-3 animate-spin" /> : <Clock className="h-3 w-3" />}
                      {step}
                    </div>
                    {i < DAG_STEPS.length - 1 && (
                      <ArrowRight className="h-3 w-3 mx-1 text-[var(--stitch-text-subtle)] shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {error && (
          <Card className="border-red-500/30 bg-red-950/20">
            <CardContent className="p-4 flex items-center gap-2 text-sm text-red-400">
              <XCircle className="h-4 w-4 shrink-0" />
              {error}
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Status Bar */}
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant={result.status === "succeeded" ? "success" : "destructive"} className="text-xs gap-1">
                {result.status === "succeeded" ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                {result.status.toUpperCase()}
              </Badge>
              <Badge variant="secondary" className="text-xs gap-1">
                <Clock className="h-3 w-3" />
                {(result.wall_clock_ms / 1000).toFixed(1)}s
              </Badge>
              <Badge variant="secondary" className="text-xs gap-1">
                <Activity className="h-3 w-3" />
                {result.browser_actions.length} actions
              </Badge>
              {result.selected_path && (
                <Badge variant="cyan" className="text-xs gap-1">
                  <Globe className="h-3 w-3" />
                  Path: {result.selected_path}
                </Badge>
              )}
              {result.critic_status && (
                <Badge variant={result.critic_status === "PASSED" ? "success" : "destructive"} className="text-xs gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  Critic: {result.critic_status}
                </Badge>
              )}
            </div>

            <div className="grid gap-6 lg:grid-cols-12">
              {/* Left: Comparison Table */}
              <div className="lg:col-span-8 space-y-6">
                {/* Comparison Table */}
                {result.comparison_table.length > 0 && (
                  <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60">
                    <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                      <CardTitle className="flex items-center gap-2 text-sm">
                        <BarChart3 className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
                        Comparison Results
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {result.comparison_table.length} items extracted from live browser interactions
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-[var(--stitch-border)] bg-[var(--stitch-surface)]/50">
                              <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">#</th>
                              <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Name</th>
                              <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Likes</th>
                              <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Downloads</th>
                              <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Source</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[var(--stitch-border)]">
                            {result.comparison_table.map((item, i) => (
                              <tr key={i} className="hover:bg-[var(--stitch-surface-hover)] transition-colors">
                                <td className="px-4 py-2.5 font-mono text-[var(--stitch-accent-cyan)] font-bold">{item.rank}</td>
                                <td className="px-4 py-2.5 font-medium text-[var(--stitch-text)]">{item.name}</td>
                                <td className="px-4 py-2.5 text-[var(--stitch-text-muted)]">{item.likes}</td>
                                <td className="px-4 py-2.5 text-[var(--stitch-text-muted)]">{item.downloads}</td>
                                <td className="px-4 py-2.5 text-[var(--stitch-accent-cyan)] font-mono text-[10px] truncate max-w-[200px]">{item.source}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Browser Actions Timeline */}
                {result.browser_actions.length > 0 && (
                  <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                    <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                      <CardTitle className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                        <Terminal className="h-4 w-4" />
                        Browser Actions ({result.browser_actions.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="divide-y divide-[var(--stitch-border)] max-h-[300px] overflow-y-auto">
                        {result.browser_actions.map((action, i) => (
                          <div key={i} className="flex items-start gap-3 px-4 py-2 text-[11px]">
                            <span className="font-mono text-[var(--stitch-accent-cyan)] font-bold w-5 shrink-0">{String(action.step).padStart(2, "0")}</span>
                            <span className={cn(
                              "px-1.5 py-0.5 rounded text-[9px] font-bold uppercase shrink-0",
                              action.status === "success" && "bg-[var(--stitch-success-dim)] text-[var(--stitch-success)]",
                              action.status === "failure" && "bg-[var(--stitch-error-dim)] text-[var(--stitch-error)]",
                              action.status === "recovery" && "bg-[var(--stitch-warning-dim)] text-[var(--stitch-warning)]",
                              !["success","failure","recovery"].includes(action.status) && "bg-[var(--stitch-surface)] text-[var(--stitch-text-subtle)]",
                            )}>{action.status}</span>
                            <span className="font-medium text-[var(--stitch-text)]">{action.action}</span>
                            <span className="text-[var(--stitch-text-subtle)] truncate">{action.target?.slice(0, 60)}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Right Sidebar */}
              <div className="lg:col-span-4 space-y-4">
                {/* Path Selection */}
                <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                      Path Selection
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {["extract", "deterministic", "a11y", "vision", "blocked"].map((path) => (
                        <div key={path} className={cn(
                          "flex items-center gap-2 rounded px-3 py-1.5 text-[11px] font-medium",
                          path === result.selected_path
                            ? "bg-[var(--stitch-accent-cyan-dim)] text-[var(--stitch-accent-cyan)] border border-[var(--stitch-accent-cyan)]/30"
                            : "bg-[var(--stitch-surface)] text-[var(--stitch-text-subtle)] border border-[var(--stitch-border)]",
                        )}>
                          {path === result.selected_path ? <CheckCircle className="h-3 w-3" /> : <div className="h-3 w-3" />}
                          <span className="capitalize">{path}</span>
                          {path === result.selected_path && <Badge variant="cyan" className="ml-auto text-[8px] py-0">SELECTED</Badge>}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* DAG Nodes */}
                <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                      DAG Pipeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.nodes.map((node: ComparisonNode, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-[11px]">
                          {node.status === "succeeded" ? (
                            <CheckCircle className="h-3 w-3 text-[var(--stitch-success)] shrink-0" />
                          ) : node.status === "failed" ? (
                            <XCircle className="h-3 w-3 text-[var(--stitch-error)] shrink-0" />
                          ) : (
                            <Clock className="h-3 w-3 text-[var(--stitch-text-subtle)] shrink-0" />
                          )}
                          <span className="font-medium text-[var(--stitch-text)] flex-1">{node.key}</span>
                          <span className="text-[var(--stitch-text-subtle)] font-mono">{node.duration_ms ? `${node.duration_ms.toFixed(0)}ms` : "—"}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Critic Evaluation */}
                <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                      <ShieldCheck className="h-4 w-4" />
                      Critic Evaluation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.nodes
                        .filter((n: ComparisonNode) => n.key === "critic_agent" && n.output_preview)
                        .map((node: ComparisonNode, _i: number) => {
                          const checks = (node.output_preview as Record<string, unknown>)?.checks as Record<string, Record<string, unknown>> | undefined;
                          if (!checks) return null;
                          return Object.entries(checks).map(([name, check]) => (
                            <div key={name} className="flex items-start gap-2 text-[11px]">
                              {check.passed ? (
                                <CheckCircle className="h-3.5 w-3.5 text-[var(--stitch-success)] shrink-0 mt-0.5" />
                              ) : (
                                <XCircle className="h-3.5 w-3.5 text-[var(--stitch-error)] shrink-0 mt-0.5" />
                              )}
                              <span className="text-[var(--stitch-text-muted)]">{String(check.name || name)}</span>
                            </div>
                          ));
                        })}
                    </div>
                  </CardContent>
                </Card>

                {/* Metrics */}
                {Object.keys(result.metrics).length > 0 && (
                  <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                        Metrics
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(result.metrics).map(([k, v]) => (
                          <div key={k} className="bg-[var(--stitch-surface)] rounded p-2 text-center">
                            <div className="text-base font-bold text-[var(--stitch-accent-cyan)]">
                              {typeof v === "number" ? v.toFixed(1) : String(v)}
                            </div>
                            <div className="text-[9px] text-[var(--stitch-text-subtle)] mt-0.5">
                              {k.replace(/_/g, " ")}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
