"use client";

import { use, useEffect, useState } from "react";
import {
  FileText,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
  FormInput,
  Key
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getPages, type PageSummary } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { useArtifact } from "@/context/ArtifactContext";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export default function PagesExplorerPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [pages, setPages] = useState<PageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof PageSummary>("url");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [filterType, setFilterType] = useState<"all" | "forms" | "auth" | "broken">("all");

  const { setSelectedArtifact, selectedArtifact } = useArtifact();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getPages(siteId)
      .then((res) => {
        setPages(res.pages);
        setLoading(false);
      })
      .catch(() => {
        // Mock fallback
        const mock = getMockSite(siteId);
        if (mock) {
          setPages(mock.pages);
        } else {
          setError("Failed to load page entries.");
        }
        setLoading(false);
      });
  }, [siteId]);

  // Sort and filter pages
  const handleSort = (field: keyof PageSummary) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const processedPages = pages
    .filter((p) => {
      // Search filter
      const matchesSearch =
        p.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.title || "").toLowerCase().includes(searchQuery.toLowerCase());

      // Tab filter
      if (filterType === "forms") return matchesSearch && p.has_form;
      if (filterType === "auth") return matchesSearch && p.has_auth_hint;
      if (filterType === "broken") return matchesSearch && p.status_code && p.status_code >= 400;
      return matchesSearch;
    })
    .sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (typeof valA === "string" && typeof valB === "string") {
        return sortOrder === "asc"
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      }
      
      // Numeric or Boolean
      const numA = typeof valA === "boolean" ? (valA ? 1 : 0) : (valA ?? 0);
      const numB = typeof valB === "boolean" ? (valB ? 1 : 0) : (valB ?? 0);
      return sortOrder === "asc"
        ? (numA > numB ? 1 : -1)
        : (numA < numB ? 1 : -1);
    });

  return (
    <SiteScaffold
      siteId={siteId}
      title="Pages Explorer"
      description="Database of crawled HTML pages, including link hierarchies, visual structures, form nodes, and page-level metadata."
    >
      <div className="space-y-4">
        
        {/* Table Filters & Search */}
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between text-xs">
          
          {/* Quick Search */}
          <div className="relative w-full sm:max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--stitch-text-subtle)]" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by URL or title..."
              className="pl-8 bg-[var(--stitch-bg-elevated)] h-9 text-xs border-[var(--stitch-border)]"
            />
          </div>

          {/* Filtering buttons */}
          <div className="flex border border-[var(--stitch-border)] rounded-md bg-[var(--stitch-bg-elevated)] p-0.5 text-xs font-medium w-full sm:w-auto overflow-x-auto justify-around">
            {(["all", "forms", "auth", "broken"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={cn(
                  "px-3 py-1 rounded capitalize transition-colors whitespace-nowrap",
                  filterType === t
                    ? "bg-[var(--stitch-surface-active)] text-[var(--stitch-accent-cyan)]"
                    : "text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
                )}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Compact Table */}
        <div className="rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] overflow-hidden">
          {loading ? (
            <div className="flex min-h-[200px] items-center justify-center text-xs text-[var(--stitch-text-muted)]">
              Querying database registry...
            </div>
          ) : error ? (
            <div className="p-4 text-xs text-[var(--stitch-error)] text-center">{error}</div>
          ) : processedPages.length === 0 ? (
            <div className="p-8 text-xs text-[var(--stitch-text-subtle)] text-center">
              No pages match the active query.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--stitch-border)] bg-[var(--stitch-bg)] text-[var(--stitch-text-subtle)] uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-4 cursor-pointer hover:text-[var(--stitch-text)]" onClick={() => handleSort("title")}>
                      Page Title <ArrowUpDown className="inline h-3 w-3 ml-0.5" />
                    </th>
                    <th className="py-2.5 px-4 cursor-pointer hover:text-[var(--stitch-text)]" onClick={() => handleSort("url")}>
                      URL Path <ArrowUpDown className="inline h-3 w-3 ml-0.5" />
                    </th>
                    <th className="py-2.5 px-4 cursor-pointer hover:text-[var(--stitch-text)] text-center" onClick={() => handleSort("depth")}>
                      Depth <ArrowUpDown className="inline h-3 w-3 ml-0.5" />
                    </th>
                    <th className="py-2.5 px-4 cursor-pointer hover:text-[var(--stitch-text)] text-center" onClick={() => handleSort("status_code")}>
                      Status <ArrowUpDown className="inline h-3 w-3 ml-0.5" />
                    </th>
                    <th className="py-2.5 px-4 text-center">Form</th>
                    <th className="py-2.5 px-4 text-center">Auth</th>
                    <th className="py-2.5 px-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--stitch-border)]">
                  {processedPages.map((page) => {
                    const isSelected = selectedArtifact?.type === "page" && selectedArtifact.data.id === page.id;
                    return (
                      <tr
                        key={page.id}
                        onClick={() => setSelectedArtifact({ type: "page", data: page })}
                        className={cn(
                          "hover:bg-[var(--stitch-surface-hover)] transition-colors cursor-pointer group",
                          isSelected ? "bg-[var(--stitch-surface-active)]" : ""
                        )}
                      >
                        {/* Title */}
                        <td className="py-3 px-4 font-medium text-[var(--stitch-text)] max-w-xs truncate">
                          {page.title || "Untitled page"}
                        </td>
                        
                        {/* URL */}
                        <td className="py-3 px-4 font-mono text-[11px] text-[var(--stitch-accent-cyan)] max-w-[240px] truncate">
                          {page.url}
                        </td>
                        
                        {/* Depth */}
                        <td className="py-3 px-4 text-center font-mono font-medium text-[var(--stitch-text-muted)]">
                          d{page.depth}
                        </td>
                        
                        {/* Status Code */}
                        <td className="py-3 px-4 text-center">
                          <span
                            className={cn(
                              "inline-block rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold",
                              !page.status_code || page.status_code < 300
                                ? "bg-[var(--stitch-success-dim)] text-[var(--stitch-success)]"
                                : "bg-[var(--stitch-error-dim)] text-[var(--stitch-error)]"
                            )}
                          >
                            {page.status_code || 200}
                          </span>
                        </td>
                        
                        {/* Form Presence Indicator */}
                        <td className="py-3 px-4 text-center">
                          {page.has_form ? (
                            <FormInput aria-label="Form Detected" className="inline h-4 w-4 text-[var(--stitch-accent-cyan)]" />
                          ) : (
                            <span className="text-[var(--stitch-text-subtle)]">-</span>
                          )}
                        </td>
                        
                        {/* Auth Presence Indicator */}
                        <td className="py-3 px-4 text-center">
                          {page.has_auth_hint ? (
                            <Key aria-label="Authentication Signals Identified" className="inline h-4 w-4 text-[var(--stitch-warning)]" />
                          ) : (
                            <span className="text-[var(--stitch-text-subtle)]">-</span>
                          )}
                        </td>

                        {/* Interactive Inspection arrow */}
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
