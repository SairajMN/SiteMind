"use client";

import { useState } from "react";
import {
    Search, Sparkles, Loader2, CheckCircle, XCircle, Clock,
    ArrowRight, Globe, ShieldCheck, Activity, Terminal, Image,
    Play, ChevronDown, BarChart3, Zap, ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { runWebSearch, type WebSearchResult, type WebSearchItem } from "@/lib/api-client";

const PRESETS = [
    "Best laptops under 80000 in India",
    "Compare iPhone 16 vs Samsung S25",
    "Top 5 project management tools 2025",
    "Best budget headphones under 5000",
];

const DAG_STEPS = ["Planner", "Search", "Visit Pages", "VLM Analyze", "Format"];

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<WebSearchResult | null>(null);
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
        }, 8000);

        try {
            const res = await runWebSearch({ query: qText.trim() });
            setResult(res);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Web search failed");
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
                            <Globe className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
                        </div>
                        <span className="text-sm font-semibold tracking-tight">
                            Site<span className="text-gradient font-bold">Mind</span>
                            <span className="ml-2 text-[var(--stitch-text-subtle)]">/ Web Search</span>
                        </span>
                    </div>
                </div>
            </header>

            <div className="relative z-10 mx-auto max-w-6xl px-6 py-8 space-y-8">
                {/* Title */}
                <div className="space-y-3">
                    <div className="inline-flex">
                        <Badge variant="cyan" className="gap-1.5 py-1 px-3 bg-[var(--stitch-accent-cyan-dim)]/40 border-[var(--stitch-border-accent)]">
                            <Sparkles className="h-3 w-3 text-[var(--stitch-accent-cyan)] animate-pulse" />
                            Web Search with Vision AI
                        </Badge>
                    </div>
                    <h1 className="text-3xl font-extrabold tracking-tight">
                        Search anything across the web
                    </h1>
                    <p className="text-sm text-[var(--stitch-text-muted)] max-w-2xl">
                        Real browser visits, screenshots, VLM analysis, and DOM extraction.
                        The agent searches the web, visits top pages, and extracts detailed
                        product info, prices, ratings, and specs.
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
                                        placeholder="e.g. Best laptops under 80000 in India"
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
                                        <><Play className="h-4 w-4 mr-1" /> Search</>
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
                                Executing Web Search Pipeline
                            </CardTitle>
                            <CardDescription className="text-xs">
                                Searching the web, visiting pages, analyzing with VLM...
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
                                {result.total_items} items
                            </Badge>
                            <Badge variant="cyan" className="text-xs gap-1">
                                <Globe className="h-3 w-3" />
                                {result.total_pages} pages
                            </Badge>
                        </div>

                        <div className="grid gap-6 lg:grid-cols-12">
                            {/* Left: Results Table */}
                            <div className="lg:col-span-8 space-y-6">
                                {/* Results Table */}
                                {result.comparison_table.length > 0 && (
                                    <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60">
                                        <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                                            <CardTitle className="flex items-center gap-2 text-sm">
                                                <BarChart3 className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
                                                Search Results
                                            </CardTitle>
                                            <CardDescription className="text-xs">
                                                {result.total_items} items extracted from {result.total_pages} pages via VLM + DOM analysis
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent className="p-0">
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-xs">
                                                    <thead>
                                                        <tr className="border-b border-[var(--stitch-border)] bg-[var(--stitch-surface)]/50">
                                                            <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">#</th>
                                                            <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Name</th>
                                                            <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Price</th>
                                                            <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Rating</th>
                                                            <th className="px-4 py-2.5 text-left font-semibold text-[var(--stitch-text-muted)]">Source</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-[var(--stitch-border)]">
                                                        {result.comparison_table.map((item: WebSearchItem, i: number) => (
                                                            <tr key={i} className="hover:bg-[var(--stitch-surface-hover)] transition-colors">
                                                                <td className="px-4 py-2.5 font-mono text-[var(--stitch-accent-cyan)] font-bold">{item.rank || i + 1}</td>
                                                                <td className="px-4 py-2.5 font-medium text-[var(--stitch-text)] max-w-[200px] truncate">{item.name}</td>
                                                                <td className="px-4 py-2.5 text-[var(--stitch-text-muted)] font-mono">{item.price}</td>
                                                                <td className="px-4 py-2.5 text-[var(--stitch-text-muted)]">{item.rating}</td>
                                                                <td className="px-4 py-2.5">
                                                                    {item.source && (
                                                                        <a
                                                                            href={item.source}
                                                                            target="_blank"
                                                                            rel="noopener noreferrer"
                                                                            className="text-[var(--stitch-accent-cyan)] font-mono text-[10px] truncate max-w-[200px] flex items-center gap-1 hover:underline"
                                                                        >
                                                                            {item.page_title || item.source.slice(0, 40)}
                                                                            <ExternalLink className="h-3 w-3 shrink-0" />
                                                                        </a>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )}

                                {/* Final Answer */}
                                {result.final_answer && (
                                    <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                                        <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                                            <CardTitle className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                                                <Sparkles className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
                                                AI Analysis
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="p-4">
                                            <pre className="text-xs text-[var(--stitch-text)] whitespace-pre-wrap font-sans leading-relaxed">
                                                {result.final_answer}
                                            </pre>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>

                            {/* Right Sidebar */}
                            <div className="lg:col-span-4 space-y-4">
                                {/* DAG Pipeline */}
                                <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                                            <Terminal className="h-4 w-4 inline mr-1" />
                                            DAG Pipeline
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2">
                                            {result.nodes.map((node, i) => (
                                                <div key={i} className="flex items-center gap-2 text-[11px]">
                                                    {node.status === "succeeded" ? (
                                                        <CheckCircle className="h-3 w-3 text-[var(--stitch-success)] shrink-0" />
                                                    ) : node.status === "failed" ? (
                                                        <XCircle className="h-3 w-3 text-[var(--stitch-error)] shrink-0" />
                                                    ) : (
                                                        <Clock className="h-3 w-3 text-[var(--stitch-text-subtle)] shrink-0" />
                                                    )}
                                                    <span className="font-medium text-[var(--stitch-text)] flex-1 capitalize">{node.key}</span>
                                                    <span className="text-[var(--stitch-text-subtle)] font-mono">{node.duration_ms ? `${node.duration_ms.toFixed(0)}ms` : "—"}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Summary stats */}
                                <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                                            Summary
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="bg-[var(--stitch-surface)] rounded p-2 text-center">
                                                <div className="text-base font-bold text-[var(--stitch-accent-cyan)]">{result.total_items}</div>
                                                <div className="text-[9px] text-[var(--stitch-text-subtle)] mt-0.5">Items Found</div>
                                            </div>
                                            <div className="bg-[var(--stitch-surface)] rounded p-2 text-center">
                                                <div className="text-base font-bold text-[var(--stitch-accent-cyan)]">{result.total_pages}</div>
                                                <div className="text-[9px] text-[var(--stitch-text-subtle)] mt-0.5">Pages Analyzed</div>
                                            </div>
                                            <div className="bg-[var(--stitch-surface)] rounded p-2 text-center">
                                                <div className="text-base font-bold text-[var(--stitch-accent-cyan)]">{(result.wall_clock_ms / 1000).toFixed(1)}s</div>
                                                <div className="text-[9px] text-[var(--stitch-text-subtle)] mt-0.5">Duration</div>
                                            </div>
                                            <div className="bg-[var(--stitch-surface)] rounded p-2 text-center">
                                                <div className="text-base font-bold text-[var(--stitch-accent-cyan)]">{result.iterations}</div>
                                                <div className="text-[9px] text-[var(--stitch-text-subtle)] mt-0.5">Iterations</div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}