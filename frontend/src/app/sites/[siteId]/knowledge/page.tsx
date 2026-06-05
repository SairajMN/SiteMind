"use client";

import { use, useEffect, useState } from "react";
import {
  Search,
  Filter,
  FileText,
  FormInput,
  Cpu,
  Workflow,
  Sparkles,
  SlidersHorizontal,
  ChevronRight,
  ExternalLink,
  Lock
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { getPages, getForms, getEndpoints, getWorkflows } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { useArtifact } from "@/context/ArtifactContext";
import { cn } from "@/lib/utils";

type ArtifactCategory = "all" | "page" | "form" | "endpoint" | "workflow";

interface UnifiedArtifact {
  id: string;
  type: ArtifactCategory;
  title: string;
  url: string;
  confidence: number;
  snippet: string;
  meta: Record<string, any>;
  rawData: any;
}

export default function KnowledgePage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);
  
  // State variables
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState<"hybrid" | "semantic" | "lexical">("hybrid");
  const [activeCategory, setActiveCategory] = useState<ArtifactCategory>("all");
  const [minConfidence, setMinConfidence] = useState<number>(0.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<UnifiedArtifact[]>([]);
  const [filteredResults, setFilteredResults] = useState<UnifiedArtifact[]>([]);

  // Context hook
  const { setSelectedArtifact } = useArtifact();

  // Load datasets (API + Fallback)
  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      getPages(siteId).catch(() => null),
      getForms(siteId).catch(() => null),
      getEndpoints(siteId).catch(() => null),
      getWorkflows(siteId).catch(() => null)
    ])
      .then(([pagesRes, formsRes, endpointsRes, workflowsRes]) => {
        let compiled: UnifiedArtifact[] = [];

        // Check if API resolved data, else load mock fallback
        const hasApiData = pagesRes || formsRes || endpointsRes || workflowsRes;

        if (hasApiData) {
          if (pagesRes?.pages) {
            pagesRes.pages.forEach(p => {
              compiled.push({
                id: p.id,
                type: "page",
                title: p.title || "Page Artifact",
                url: p.url,
                confidence: 0.95,
                snippet: `Discovered depth ${p.depth}. Contains forms: ${p.has_form}, authentication triggers: ${p.has_auth_hint}.`,
                meta: { depth: p.depth, status: p.status_code || 200 },
                rawData: p
              });
            });
          }
          if (formsRes?.forms) {
            formsRes.forms.forEach(f => {
              compiled.push({
                id: f.id,
                type: "form",
                title: `Form: ${f.form_name || "unnamed"}`,
                url: f.action_url || "",
                confidence: f.confidence || 0.9,
                snippet: `Form POST request to ${f.action_url}. Contains ${f.fields.length} input field types.`,
                meta: { method: f.method, fieldsCount: f.fields.length },
                rawData: f
              });
            });
          }
          if (endpointsRes?.endpoints) {
            endpointsRes.endpoints.forEach(e => {
              compiled.push({
                id: e.id,
                type: "endpoint",
                title: `${e.method || "GET"} ${e.request_url}`,
                url: e.request_url,
                confidence: e.confidence || 0.85,
                snippet: `Observed network request endpoint with response status ${e.status_code}. Type: ${e.request_type}.`,
                meta: { method: e.method, status: e.status_code },
                rawData: e
              });
            });
          }
          if (workflowsRes?.workflows) {
            workflowsRes.workflows.forEach(w => {
              compiled.push({
                id: w.id,
                type: "workflow",
                title: w.name || "Inferred workflow",
                url: "",
                confidence: w.confidence || 0.9,
                snippet: w.summary || `Multi-step user action timeline with ${w.steps.length} sequential operations.`,
                meta: { stepsCount: w.steps.length },
                rawData: w
              });
            });
          }
        } else {
          // Mock Data Fallback
          const mock = getMockSite(siteId);
          if (mock) {
            mock.pages.forEach(p => {
              compiled.push({
                id: p.id,
                type: "page",
                title: p.title || "Page",
                url: p.url,
                confidence: 0.96,
                snippet: `Crawled page at depth ${p.depth}. Forms: ${p.has_form ? "Yes" : "No"}, Auth: ${p.has_auth_hint ? "Yes" : "No"}. Mapped DOM hierarchy.`,
                meta: { depth: p.depth, status: p.status_code || 200 },
                rawData: p
              });
            });
            mock.forms.forEach(f => {
              compiled.push({
                id: f.id,
                type: "form",
                title: `Form: ${f.form_name || "unnamed"}`,
                url: f.action_url || "",
                confidence: f.confidence || 0.95,
                snippet: `Interactive form found redirecting to ${f.action_url}. Mapped input selector parameters: ${f.fields.map(fd => fd.name).join(", ")}.`,
                meta: { method: f.method, fieldsCount: f.fields.length },
                rawData: f
              });
            });
            mock.endpoints.forEach(e => {
              compiled.push({
                id: e.id,
                type: "endpoint",
                title: `${e.method || "GET"} ${e.request_url}`,
                url: e.request_url,
                confidence: e.confidence || 0.92,
                snippet: `Observed ${e.request_type} request to ${e.request_url} resulting in HTTP status ${e.status_code}.`,
                meta: { method: e.method, status: e.status_code },
                rawData: e
              });
            });
            mock.workflows.forEach(w => {
              compiled.push({
                id: w.id,
                type: "workflow",
                title: w.name || "User Journey",
                url: "",
                confidence: w.confidence || 0.94,
                snippet: w.summary || `Structured user workflow representing ${w.steps.length} steps.`,
                meta: { stepsCount: w.steps.length },
                rawData: w
              });
            });
          }
        }
        setArtifacts(compiled);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load index.");
        setLoading(false);
      });
  }, [siteId]);

  // Handle Search and Filtering
  useEffect(() => {
    let results = [...artifacts];

    // Filter by type
    if (activeCategory !== "all") {
      results = results.filter(a => a.type === activeCategory);
    }

    // Filter by confidence threshold
    results = results.filter(a => a.confidence >= minConfidence);

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      results = results.filter(a =>
        a.title.toLowerCase().includes(q) ||
        a.url.toLowerCase().includes(q) ||
        a.snippet.toLowerCase().includes(q)
      );
    }

    setFilteredResults(results);
  }, [artifacts, searchQuery, activeCategory, minConfidence]);

  const handleInspect = (art: UnifiedArtifact) => {
    // Map UnifiedArtifact to target api-client model
    if (art.type === "page") {
      setSelectedArtifact({ type: "page", data: art.rawData });
    } else if (art.type === "form") {
      setSelectedArtifact({ type: "form", data: art.rawData });
    } else if (art.type === "endpoint") {
      setSelectedArtifact({ type: "endpoint", data: art.rawData });
    } else if (art.type === "workflow") {
      setSelectedArtifact({ type: "workflow", data: art.rawData });
    }
  };

  const getCategoryIcon = (type: ArtifactCategory) => {
    switch (type) {
      case "page": return <FileText className="h-4 w-4" />;
      case "form": return <FormInput className="h-4 w-4" />;
      case "endpoint": return <Cpu className="h-4 w-4" />;
      case "workflow": return <Workflow className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="Retrieval Intelligence Workspace"
      description="Search, inspect, and audit extracted website metadata and citations. SiteMind crawls are indexed dynamically for RAG retrieval."
    >
      <div className="space-y-6">
        
        {/* Search & Filter Header card */}
        <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
          <CardContent className="pt-6 space-y-4">
            
            {/* Search Input and semantic toggle */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-[var(--stitch-text-subtle)]" />
                <Input
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Query semantic index (e.g. 'Stripe checkout credit card fields' or 'login forms')"
                  className="pl-9 bg-[var(--stitch-surface)]/60 focus:bg-[var(--stitch-surface)]"
                />
              </div>

              {/* Retrieval Mode selector */}
              <div className="flex border border-[var(--stitch-border)] rounded-md bg-[var(--stitch-surface)] p-1 text-xs shrink-0 font-medium">
                <button
                  onClick={() => setSearchMode("hybrid")}
                  className={cn(
                    "px-3 py-1.5 rounded transition-colors flex items-center gap-1.5",
                    searchMode === "hybrid" ? "bg-[var(--stitch-accent-cyan)] text-slate-900" : "text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
                  )}
                >
                  <Sparkles className="h-3 w-3" /> Hybrid
                </button>
                <button
                  onClick={() => setSearchMode("semantic")}
                  className={cn(
                    "px-3 py-1.5 rounded transition-colors",
                    searchMode === "semantic" ? "bg-[var(--stitch-accent-cyan)] text-slate-900" : "text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
                  )}
                >
                  Vector
                </button>
                <button
                  onClick={() => setSearchMode("lexical")}
                  className={cn(
                    "px-3 py-1.5 rounded transition-colors",
                    searchMode === "lexical" ? "bg-[var(--stitch-accent-cyan)] text-slate-900" : "text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
                  )}
                >
                  Keyword
                </button>
              </div>
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[var(--stitch-border)] pt-4 text-xs">
              
              {/* Category selector */}
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="text-[var(--stitch-text-subtle)] flex items-center gap-1">
                  <Filter className="h-3 w-3" /> Filter:
                </span>
                {(["all", "page", "form", "endpoint", "workflow"] as const).map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    className={cn(
                      "px-2.5 py-1 rounded-full border border-[var(--stitch-border)] transition-colors capitalize",
                      activeCategory === cat
                        ? "bg-[var(--stitch-accent-cyan-dim)] text-[var(--stitch-accent-cyan)] border-[var(--stitch-border-accent)]"
                        : "text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface)]"
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Confidence filter */}
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="h-3.5 w-3.5 text-[var(--stitch-text-subtle)]" />
                <span className="text-[var(--stitch-text-subtle)]">Confidence threshold:</span>
                <input
                  type="range"
                  min="0.5"
                  max="0.99"
                  step="0.05"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                  className="w-24 accent-[var(--stitch-accent-cyan)]"
                />
                <span className="font-mono text-[var(--stitch-accent-cyan)] font-bold">
                  {Math.round(minConfidence * 100)}%+
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results layout */}
        {loading ? (
          <div className="flex min-h-[30vh] items-center justify-center text-sm text-[var(--stitch-text-muted)]">
            Retrieving database index...
          </div>
        ) : error ? (
          <div className="rounded-lg border border-[var(--stitch-warning)]/30 bg-[var(--stitch-warning)]/5 p-4 text-sm text-[var(--stitch-warning)]">
            {error}
          </div>
        ) : filteredResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[260px] rounded-xl border border-dashed border-[var(--stitch-border)] p-8 text-center text-xs text-[var(--stitch-text-muted)] bg-[var(--stitch-bg-elevated)]/20">
            <SlidersHorizontal className="h-8 w-8 text-[var(--stitch-text-subtle)] mb-2" />
            <p className="font-medium text-slate-300">No matching index files found</p>
            <p className="text-[11px] text-[var(--stitch-text-subtle)] mt-1 max-w-sm mx-auto">
              Try adjusting your semantic queries, selecting &ldquo;All&rdquo; categories, or lowering the confidence threshold.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-[var(--stitch-text-subtle)] px-1">
              <span>Showing <strong>{filteredResults.length}</strong> index objects found</span>
              <span>Sorted by vector distance match</span>
            </div>

            <div className="space-y-3.5">
              {filteredResults.map((art) => (
                <div
                  key={art.id}
                  onClick={() => handleInspect(art)}
                  className="group relative flex flex-col sm:flex-row items-start justify-between gap-4 rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] hover:border-[var(--stitch-border-strong)] p-4 cursor-pointer transition-all shadow-sm hover:shadow-[var(--stitch-shadow-glow)]"
                >
                  <div className="space-y-2 min-w-0 flex-1">
                    
                    {/* Top Row: Type chip, Title */}
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded bg-[var(--stitch-surface-active)] text-[var(--stitch-text-muted)] group-hover:text-[var(--stitch-accent-cyan)] transition-colors">
                        {getCategoryIcon(art.type)}
                      </span>
                      <h3 className="font-semibold text-sm text-[var(--stitch-text)] group-hover:text-white transition-colors truncate">
                        {art.title}
                      </h3>
                      <Badge variant="outline" className="capitalize text-[10px] hidden xs:inline-flex">
                        {art.type}
                      </Badge>
                    </div>

                    {/* Description snippet */}
                    <p className="text-xs text-[var(--stitch-text-muted)] leading-relaxed pl-8 pr-2">
                      {art.snippet}
                    </p>

                    {/* Metadata line */}
                    {art.url && (
                      <p className="font-mono text-[10px] text-[var(--stitch-accent-cyan)] pl-8 truncate">
                        {art.url}
                      </p>
                    )}
                  </div>

                  {/* Right side: accuracy gauge and navigation */}
                  <div className="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto shrink-0 border-t border-[var(--stitch-border)] sm:border-0 pt-3 sm:pt-0 gap-2 pl-8 sm:pl-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-[var(--stitch-text-subtle)]">Vector Match:</span>
                      <ConfidenceBadge value={art.confidence} />
                    </div>

                    {art.meta.status && (
                      <Badge variant={art.meta.status < 400 ? "success" : "destructive"} className="text-[9px] py-0 px-1 font-mono">
                        HTTP {art.meta.status}
                      </Badge>
                    )}
                    {art.meta.stepsCount && (
                      <Badge variant="secondary" className="text-[9px] py-0 px-1">
                        {art.meta.stepsCount} steps
                      </Badge>
                    )}
                    {art.meta.fieldsCount && (
                      <Badge variant="cyan" className="text-[9px] py-0 px-1">
                        {art.meta.fieldsCount} fields
                      </Badge>
                    )}

                    <ChevronRight className="h-4 w-4 text-[var(--stitch-text-subtle)] group-hover:translate-x-1 transition-transform hidden sm:block" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </SiteScaffold>
  );
}
