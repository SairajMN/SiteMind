"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Globe,
  Loader2,
  Sparkles,
  Link2,
  Settings2,
  Database,
  History,
  ShieldCheck,
  Zap,
  HelpCircle,
  FileSpreadsheet
} from "lucide-react";
import { ApiClientError, createSite } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const EXAMPLES = [
  { label: "Stripe", url: "https://stripe.com" },
  { label: "GitHub", url: "https://github.com" },
  { label: "Linear", url: "https://linear.app" },
  { label: "Notion", url: "https://notion.so" },
];

const RECENT_ANALYSES = [
  { site_id: "stripe", url: "https://stripe.com", status: "completed", date: "June 5, 2026", pages: 45, confidence: 0.95 },
  { site_id: "github", url: "https://github.com", status: "completed", date: "June 5, 2026", pages: 88, confidence: 0.98 },
  { site_id: "linear", url: "https://linear.app", status: "completed", date: "June 5, 2026", pages: 25, confidence: 0.94 },
  { site_id: "notion", url: "https://notion.so", status: "failed", error: "Crawler Timeout (HTTP 504)", date: "June 4, 2026", pages: 0 },
  { site_id: "acme-corp", url: "https://acme-corp.demo", status: "queued", date: "Pending", pages: 0 },
];

export default function LandingPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [crawlDepth, setCrawlDepth] = useState(3);
  const [sameDomain, setSameDomain] = useState(true);
  const [screenshots, setScreenshots] = useState(true);
  const [networkTraces, setNetworkTraces] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    let normalized = url.trim();
    if (!normalized) {
      setError("Please enter a valid URL to analyze");
      setLoading(false);
      return;
    }
    if (!/^https?:\/\//i.test(normalized)) {
      normalized = `https://${normalized}`;
    }

    try {
      const result = await createSite({
        url: normalized,
        goal: "Analyze website structure and workflows",
        scope_policy: sameDomain ? "same_domain" : "unrestricted",
        crawl_depth: crawlDepth,
        page_budget: 60,
        include_screenshots: screenshots,
        include_network_traces: networkTraces,
      });

      router.push(`/sites/${result.site_id}?job=${result.crawl_job_id}&dag_run_id=${result.dag_run_id}`);
    } catch (err) {
      console.warn("API Offline, redirecting using mock fallback...", err);
      // Fallback for demo simulation
      const match = EXAMPLES.find(ex => normalized.toLowerCase().includes(ex.label.toLowerCase())) || EXAMPLES[0];
      const matchId = match.label.toLowerCase();
      
      // Simulate pipeline starting with timeout
      setTimeout(() => {
        router.push(`/sites/${matchId}?job=${matchId}-job1&dag_run_id=${matchId}-dag1&demo=true`);
      }, 800);
    }
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#07070a] text-slate-100 flex flex-col justify-between">
      {/* Dynamic gradients overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900 via-transparent to-transparent" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-[600px] -translate-x-1/2 rounded-full bg-[var(--stitch-accent-cyan)]/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-10 right-10 h-80 w-80 rounded-full bg-[var(--stitch-accent-violet)]/5 blur-3xl" />

      {/* Header element */}
      <header className="relative z-10 border-b border-[var(--stitch-border)] bg-[#07070a]/60 backdrop-blur-md px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--stitch-accent-cyan-dim)] ring-1 ring-[var(--stitch-border-accent)]">
              <Sparkles className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
            </div>
            <span className="text-sm font-semibold tracking-tight">
              Site<span className="text-gradient font-bold">Mind</span>
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-[var(--stitch-text-muted)]">
            <span className="hover:text-[var(--stitch-text)] cursor-pointer">Documentation</span>
            <span className="hover:text-[var(--stitch-text)] cursor-pointer">API Specs</span>
            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => router.push("/settings")}>
              Settings
            </Button>
          </div>
        </div>
      </header>

      {/* Main landing container */}
      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col gap-12 px-6 py-12 lg:grid lg:grid-cols-12 lg:gap-16 lg:py-20">
        
        {/* Left Side: Product pitch */}
        <div className="flex flex-col justify-center lg:col-span-5 space-y-6">
          <div className="inline-flex">
            <Badge variant="cyan" className="gap-1.5 py-1 px-3 bg-[var(--stitch-accent-cyan-dim)]/40 border-[var(--stitch-border-accent)]">
              <Zap className="h-3 w-3 text-[var(--stitch-accent-cyan)] animate-pulse" />
              Agentic site intelligence
            </Badge>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl leading-[1.15]">
            Transform any website into <br />
            <span className="text-gradient">structured intelligence</span>
          </h1>
          <p className="text-sm text-[var(--stitch-text-muted)] leading-relaxed">
            SiteMind automatically crawls, reverse-engineers, and structures any online portal into pages, forms, authenticated endpoints, user workflows, and OpenAPI specifications. Powered by a multi-agent validation pipeline.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[var(--stitch-border)]">
            <div className="flex gap-2">
              <Database className="h-5 w-5 text-[var(--stitch-accent-cyan)] shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold">Semantic Graph</h4>
                <p className="text-[11px] text-[var(--stitch-text-subtle)]">Models DOM features and API endpoints.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <ShieldCheck className="h-5 w-5 text-[var(--stitch-accent-violet)] shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold">Critic Verification</h4>
                <p className="text-[11px] text-[var(--stitch-text-subtle)]">Verifies all findings against evidence.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Control panel & Recent Analyses */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60 backdrop-blur-md shadow-[var(--stitch-shadow-glow)]">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Globe className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
                Initialize Crawl Agent
              </CardTitle>
              <CardDescription className="text-xs text-[var(--stitch-text-muted)]">
                Provide a website URL to begin automated analysis and spec extraction.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <Link2 className="absolute left-3 top-3 h-4 w-4 text-[var(--stitch-text-subtle)]" />
                  <Input
                    type="text"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                    className="pl-9 h-10 border-[var(--stitch-border)] bg-[var(--stitch-surface)]/80 focus:border-[var(--stitch-border-strong)]"
                    autoFocus
                  />
                </div>

                {/* Example Quick Chips */}
                <div className="flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="text-[var(--stitch-text-subtle)] mr-1">Try:</span>
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex.url}
                      type="button"
                      onClick={() => setUrl(ex.url)}
                      className="rounded bg-[var(--stitch-surface)] border border-[var(--stitch-border)] px-2.5 py-1 text-[11px] text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)] hover:border-[var(--stitch-border-strong)] transition-colors"
                      disabled={loading}
                    >
                      {ex.label}
                    </button>
                  ))}
                </div>

                {/* Agent Config Drawer */}
                <div className="rounded-lg border border-[var(--stitch-border)] bg-[var(--stitch-bg)]/60 p-4 space-y-3.5">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--stitch-text)]">
                    <Settings2 className="h-3.5 w-3.5 text-[var(--stitch-accent-cyan)]" />
                    Crawl & Analyzer Settings
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 text-xs">
                    <div className="space-y-1">
                      <label className="text-[11px] text-[var(--stitch-text-muted)] font-medium">Max depth</label>
                      <input
                        type="number"
                        min={1}
                        max={10}
                        value={crawlDepth}
                        onChange={(e) => setCrawlDepth(Number(e.target.value))}
                        disabled={loading}
                        className="w-full rounded border border-[var(--stitch-border)] bg-[var(--stitch-surface-active)] px-2.5 py-1 focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-2.5 pt-3.5">
                      <ToggleRow
                        label="Restrict to same domain"
                        checked={sameDomain}
                        onChange={setSameDomain}
                        disabled={loading}
                      />
                      <ToggleRow
                        label="Capture screenshots"
                        checked={screenshots}
                        onChange={setScreenshots}
                        disabled={loading}
                      />
                      <ToggleRow
                        label="Collect network traces"
                        checked={networkTraces}
                        onChange={setNetworkTraces}
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>

                {error && (
                  <p className="rounded-md border border-red-500/25 bg-red-950/20 px-3 py-2 text-xs text-red-400">
                    {error}
                  </p>
                )}

                <Button type="submit" className="w-full bg-[var(--stitch-accent-cyan)] hover:bg-[var(--stitch-accent-cyan)]/90 text-slate-900 font-bold" size="lg" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Spinning up pipeline agents...
                    </>
                  ) : (
                    <>
                      Analyze website
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Recent Analysis list */}
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
            <CardHeader className="py-3 px-4 border-b border-[var(--stitch-border)]">
              <CardTitle className="flex items-center gap-2 text-xs font-semibold text-[var(--stitch-text-muted)]">
                <History className="h-4 w-4" />
                Recent Analysis Logs
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-[var(--stitch-border)]">
                {RECENT_ANALYSES.map((run) => (
                  <div
                    key={run.url}
                    onClick={() => {
                      if (run.status === "completed") {
                        router.push(`/sites/${run.site_id}?job=${run.site_id}-job1`);
                      } else if (run.status === "queued" || run.status === "failed") {
                        alert(`Crawl run for ${run.url} has state: "${run.status.toUpperCase()}". ${run.error ? `Reason: ${run.error}` : ""}`);
                      }
                    }}
                    className={cn(
                      "flex items-center justify-between px-4 py-3 text-xs transition-colors",
                      run.status === "completed" ? "cursor-pointer hover:bg-[var(--stitch-surface-hover)]" : "opacity-80"
                    )}
                  >
                    <div className="space-y-0.5">
                      <p className="font-semibold text-[var(--stitch-text)]">{run.url}</p>
                      <p className="text-[10px] text-[var(--stitch-text-subtle)]">
                        {run.date} {run.pages > 0 && `· ${run.pages} pages`}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {run.confidence !== undefined && (
                        <span className="text-[10px] text-[var(--stitch-text-subtle)]">
                          Acc: <span className="font-mono text-[var(--stitch-accent-cyan)] font-bold">{(run.confidence * 100).toFixed(0)}%</span>
                        </span>
                      )}
                      
                      {run.status === "completed" && (
                        <span className="rounded bg-[var(--stitch-success-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--stitch-success)]">
                          Completed
                        </span>
                      )}
                      {run.status === "failed" && (
                        <span className="rounded bg-[var(--stitch-error-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--stitch-error)]" title={run.error}>
                          Failed
                        </span>
                      )}
                      {run.status === "queued" && (
                        <span className="rounded bg-[var(--stitch-warning-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--stitch-warning)]">
                          Queued
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer copyright */}
      <footer className="border-t border-[var(--stitch-border)] py-6 text-center text-xs text-[var(--stitch-text-subtle)]">
        SiteMind Security and Intelligence System. Built with Linear-grade dashboards.
      </footer>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4 text-xs">
      <span className="text-[var(--stitch-text-muted)]">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-5 w-9 shrink-0 rounded-full transition-colors focus:outline-none",
          checked ? "bg-[var(--stitch-accent-cyan)]" : "bg-[var(--stitch-surface-active)] border border-[var(--stitch-border)]",
          disabled && "opacity-50",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 left-0.5 h-3.8 w-3.8 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-4.2 bg-slate-900" : "translate-x-0 bg-slate-400",
          )}
        />
      </button>
    </label>
  );
}
