"use client";

import { use, useEffect, useState } from "react";
import {
  Cpu,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ChevronRight,
  Shield,
  Activity,
  Code2,
  Lock
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getEndpoints, type EndpointSummary } from "@/lib/api-client";
import { useArtifact } from "@/context/ArtifactContext";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

export default function EndpointsExplorerPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [endpoints, setEndpoints] = useState<EndpointSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [methodFilter, setMethodFilter] = useState<"all" | "GET" | "POST" | "graphql">("all");

  const { setSelectedArtifact, selectedArtifact } = useArtifact();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getEndpoints(siteId)
      .then((res) => {
        setEndpoints(res.endpoints);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load endpoint entries.");
        setEndpoints([]);
        setLoading(false);
      });
  }, [siteId]);

  const filteredEndpoints = endpoints.filter((ep) => {
    const matchesSearch =
      ep.request_url.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ep.request_type || "").toLowerCase().includes(searchQuery.toLowerCase());

    if (methodFilter === "GET") return matchesSearch && ep.method === "GET";
    if (methodFilter === "POST") return matchesSearch && ep.method === "POST";
    if (methodFilter === "graphql") {
      return (
        matchesSearch &&
        (ep.request_url.includes("graphql") || (ep.request_type || "").includes("graphql"))
      );
    }
    return matchesSearch;
  });

  const getMethodBadgeClass = (method?: string) => {
    switch (method?.toUpperCase()) {
      case "GET": return "bg-cyan-950/40 text-cyan-400 border-cyan-800/50";
      case "POST": return "bg-purple-950/40 text-purple-400 border-purple-800/50";
      case "PUT": return "bg-amber-950/40 text-amber-400 border-amber-800/50";
      case "DELETE": return "bg-red-950/40 text-red-400 border-red-800/50";
      default: return "bg-slate-950/40 text-slate-400 border-slate-800/50";
    }
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="Network Endpoints Explorer"
      description="Reverse-engineered endpoint registry. Maps REST and GraphQL network API calls intercepted during Chromium page runs, including payload schemas."
    >
      <div className="space-y-4">

        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between text-xs">
          <div className="relative w-full sm:max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--stitch-text-subtle)]" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search endpoints by path or type..."
              className="pl-8 bg-[var(--stitch-bg-elevated)] h-9 text-xs border-[var(--stitch-border)]"
            />
          </div>

          <div className="flex border border-[var(--stitch-border)] rounded-md bg-[var(--stitch-bg-elevated)] p-0.5 text-xs font-medium w-full sm:w-auto overflow-x-auto justify-around">
            {(["all", "GET", "POST", "graphql"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setMethodFilter(t)}
                className={cn(
                  "px-3 py-1 rounded transition-colors whitespace-nowrap",
                  methodFilter === t
                    ? "bg-[var(--stitch-surface-active)] text-[var(--stitch-accent-cyan)]"
                    : "text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
                )}
              >
                {t === "graphql" ? "GraphQL" : t}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] overflow-hidden">
          {loading ? (
            <div className="flex min-h-[200px] items-center justify-center text-xs text-[var(--stitch-text-muted)]">
              Querying intercepted traces...
            </div>
          ) : error ? (
            <div className="rounded-lg border border-[var(--stitch-error)]/30 bg-[var(--stitch-error)]/5 p-4 text-xs text-[var(--stitch-error)]">
              {error}
            </div>
          ) : filteredEndpoints.length === 0 ? (
            <div className="p-8 text-xs text-[var(--stitch-text-subtle)] text-center">
              No network endpoints matched the query.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--stitch-border)] bg-[var(--stitch-bg)] text-[var(--stitch-text-subtle)] uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-4 w-20">Method</th>
                    <th className="py-2.5 px-4">Request Endpoint URL</th>
                    <th className="py-2.5 px-4 text-center w-20">Status</th>
                    <th className="py-2.5 px-4 w-24 text-center">Accuracy</th>
                    <th className="py-2.5 px-4 w-28">Observation</th>
                    <th className="py-2.5 px-4 w-12"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--stitch-border)] font-mono text-[11px]">
                  {filteredEndpoints.map((ep) => {
                    const isSelected =
                      selectedArtifact?.type === "endpoint" && selectedArtifact.data.id === ep.id;
                    return (
                      <tr
                        key={ep.id}
                        onClick={() => setSelectedArtifact({ type: "endpoint", data: ep })}
                        className={cn(
                          "hover:bg-[var(--stitch-surface-hover)] transition-colors cursor-pointer group",
                          isSelected ? "bg-[var(--stitch-surface-active)]" : ""
                        )}
                      >
                        <td className="py-3 px-4">
                          <span
                            className={cn(
                              "border rounded px-1.5 py-0.5 font-bold uppercase",
                              getMethodBadgeClass(ep.method)
                            )}
                          >
                            {ep.method || "GET"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[var(--stitch-text)] group-hover:text-[var(--stitch-accent-cyan)] transition-colors max-w-sm truncate break-all select-all font-mono">
                          {ep.request_url}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={cn(
                              "inline-block rounded px-1.5 py-0.5 font-semibold text-[10px]",
                              !ep.status_code || ep.status_code < 400
                                ? "bg-[var(--stitch-success-dim)] text-[var(--stitch-success)]"
                                : "bg-[var(--stitch-error-dim)] text-[var(--stitch-error)]"
                            )}
                          >
                            {ep.status_code || 200}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ep.confidence !== undefined && <ConfidenceBadge value={ep.confidence} />}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            variant={ep.observation_type === "observed" ? "cyan" : "secondary"}
                            className="text-[9px] py-0 font-sans font-normal"
                          >
                            {ep.observation_type || "observed"}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <ChevronRight className="inline h-4 w-4 text-[var(--stitch-text-subtle)] group-hover:text-[var(--stitch-accent-cyan)] group-hover:translate-x-0.5 transition-all" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </SiteScaffold>
  );
}
