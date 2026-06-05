"use client";

import { use, useEffect, useState } from "react";
import {
  Braces,
  BookOpen,
  Code2,
  FileCode,
  AlertTriangle,
  CheckCircle,
  Copy,
  Terminal,
  ChevronRight,
  ExternalLink
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getApiSpecs, type ApiSpecSummary } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { cn } from "@/lib/utils";

export default function ApiSpecsPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [specs, setSpecs] = useState<ApiSpecSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activePath, setActivePath] = useState<string>("");
  const [specTab, setSpecTab] = useState<"openapi" | "examples" | "schema">("openapi");

  useEffect(() => {
    setLoading(true);
    setError(null);
    getApiSpecs(siteId)
      .then((res) => {
        setSpecs(res);
        if (res.length > 0 && res[0].spec_json) {
          const paths = res[0].spec_json.paths as Record<string, any> | undefined;
          if (paths && Object.keys(paths).length > 0) {
            setActivePath(Object.keys(paths)[0]);
          }
        }
        setLoading(false);
      })
      .catch(() => {
        // Fallback to mock data
        const mock = getMockSite(siteId);
        if (mock && mock.apiSpecs) {
          setSpecs(mock.apiSpecs);
          if (mock.apiSpecs.length > 0 && mock.apiSpecs[0].spec_json) {
            const paths = mock.apiSpecs[0].spec_json.paths as Record<string, any> | undefined;
            if (paths && Object.keys(paths).length > 0) {
              setActivePath(Object.keys(paths)[0]);
            }
          }
        } else {
          setError("Failed to load OpenAPI documents.");
        }
        setLoading(false);
      });
  }, [siteId]);

  const activeSpec = specs[0];
  const paths = activeSpec?.spec_json?.paths as Record<string, any> | undefined;
  const activePathDetails = paths && activePath ? paths[activePath] : null;
  const activeMethod = activePathDetails ? Object.keys(activePathDetails)[0] : "post";
  const activeMethodDetails = activePathDetails ? activePathDetails[activeMethod] : null;

  // Determine if endpoint is inferred or observed
  const isInferred = activePath ? activePath.includes("payment_intents") || activePath.includes("search") : true;

  const handleCopySpec = () => {
    if (activeSpec?.spec_json) {
      navigator.clipboard.writeText(JSON.stringify(activeSpec.spec_json, null, 2));
      alert("OpenAPI JSON copied to clipboard!");
    }
  };

  const getMethodColor = (m: string) => {
    switch (m.toLowerCase()) {
      case "get": return "text-cyan-400 bg-cyan-950/40 border-cyan-800/50";
      case "post": return "text-purple-400 bg-purple-950/40 border-purple-800/50";
      default: return "text-slate-400 bg-slate-950/40 border-slate-800/50";
    }
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="OpenAPI Specifications"
      description="Synthesised OpenAPI endpoints, JSON schemas, and curls. SiteMind aggregates observed network logs and models inferred API surfaces."
    >
      <div className="space-y-6">
        
        {loading ? (
          <div className="flex min-h-[200px] items-center justify-center text-sm text-[var(--stitch-text-muted)]">
            Compiling spec schemas...
          </div>
        ) : error ? (
          <div className="text-xs text-[var(--stitch-error)] p-2">{error}</div>
        ) : !activeSpec ? (
          <div className="text-xs text-[var(--stitch-text-subtle)] p-6 border border-dashed rounded-lg text-center bg-[var(--stitch-bg-elevated)]/20">
            No API Specifications generated. Specs require workflows to be mined.
          </div>
        ) : (
          <div className="flex flex-col gap-6 lg:grid lg:grid-cols-12">
            
            {/* Left Column: List of API paths */}
            <div className="lg:col-span-4 space-y-3">
              <div className="text-xs text-[var(--stitch-text-subtle)] font-semibold px-1">
                API ENDPOINT PATHS
              </div>
              
              <div className="space-y-2">
                {paths && Object.keys(paths).map((pathKey) => {
                  const details = paths[pathKey];
                  const method = Object.keys(details)[0];
                  const isActive = activePath === pathKey;
                  return (
                    <div
                      key={pathKey}
                      onClick={() => setActivePath(pathKey)}
                      className={cn(
                        "flex items-center gap-2 rounded-lg border border-[var(--stitch-border)] p-2.5 cursor-pointer transition-colors bg-[var(--stitch-bg-elevated)]/60 hover:bg-[var(--stitch-bg-elevated)]",
                        isActive ? "ring-1 ring-[var(--stitch-accent-cyan)] shadow-sm bg-[var(--stitch-bg-elevated)]" : ""
                      )}
                    >
                      <span className={cn("border rounded px-1.5 py-0.5 text-[9px] font-bold uppercase", getMethodColor(method))}>
                        {method}
                      </span>
                      <span className="font-mono text-xs text-[var(--stitch-text)] truncate max-w-[180px]">
                        {pathKey}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Spec Playground */}
            <div className="lg:col-span-8 space-y-4">
              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                
                {/* Header */}
                <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Braces className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
                      <CardTitle className="text-sm font-semibold truncate max-w-sm">
                        {activePath}
                      </CardTitle>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleCopySpec}
                        className="rounded border border-[var(--stitch-border)] hover:bg-[var(--stitch-surface-hover)] px-2.5 py-1 text-[10px] text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)] flex items-center gap-1 transition-colors"
                      >
                        <Copy className="h-3 w-3" /> Copy JSON
                      </button>
                      <Badge variant="outline" className="text-[10px]">OpenAPI 3.0</Badge>
                    </div>
                  </div>

                  {/* Warning banner for inferred spec endpoints */}
                  {isInferred && (
                    <div className="mt-3 flex items-start gap-2.5 rounded-lg border border-amber-500/20 bg-amber-950/20 p-3 text-xs text-amber-400">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <div className="space-y-0.5">
                        <p className="font-semibold">Inferred Endpoint</p>
                        <p className="text-[11px] text-slate-300">
                          This API schema was synthesised using DOM forms and workflow structures. Validate variables before production deployment.
                        </p>
                      </div>
                    </div>
                  )}
                </CardHeader>

                {/* Tab selector */}
                <div className="flex border-b border-[var(--stitch-border)] px-4 bg-[var(--stitch-bg)]/20 text-xs">
                  <button
                    onClick={() => setSpecTab("openapi")}
                    className={cn(
                      "px-3 py-2 font-medium border-b-2",
                      specTab === "openapi" ? "border-[var(--stitch-accent-cyan)] text-[var(--stitch-text)]" : "border-transparent text-[var(--stitch-text-muted)]"
                    )}
                  >
                    OpenAPI JSON
                  </button>
                  <button
                    onClick={() => setSpecTab("examples")}
                    className={cn(
                      "px-3 py-2 font-medium border-b-2",
                      specTab === "examples" ? "border-[var(--stitch-accent-cyan)] text-[var(--stitch-text)]" : "border-transparent text-[var(--stitch-text-muted)]"
                    )}
                  >
                    cURL Examples
                  </button>
                  <button
                    onClick={() => setSpecTab("schema")}
                    className={cn(
                      "px-3 py-2 font-medium border-b-2",
                      specTab === "schema" ? "border-[var(--stitch-accent-cyan)] text-[var(--stitch-text)]" : "border-transparent text-[var(--stitch-text-muted)]"
                    )}
                  >
                    JSON Schema
                  </button>
                </div>

                <CardContent className="pt-4">
                  {specTab === "openapi" && (
                    <pre className="max-h-96 overflow-auto rounded-lg bg-black p-4 font-mono text-[11px] text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] leading-relaxed select-all">
                      {JSON.stringify(activePathDetails || activeSpec.spec_json, null, 2)}
                    </pre>
                  )}

                  {specTab === "examples" && (
                    <div className="space-y-4">
                      {/* curl request */}
                      <div>
                        <h4 className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)] tracking-wider flex items-center gap-1.5 mb-1.5">
                          <Terminal className="h-3.5 w-3.5" /> curl Request Example
                        </h4>
                        <pre className="rounded-lg bg-black p-3.5 font-mono text-[10px] text-[var(--stitch-accent-cyan)] border border-[var(--stitch-border)] overflow-x-auto">
                          {`curl -X ${activeMethod.toUpperCase()} "${siteId === "stripe" ? "https://api.stripe.com" : "https://api.github.com"}${activePath}" \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(
                            activeMethodDetails?.requestBody?.content?.["application/json"]?.schema?.properties 
                              ? Object.keys(activeMethodDetails.requestBody.content["application/json"].schema.properties).reduce((acc: any, key) => {
                                  acc[key] = key === "email" ? "user@example.com" : "••••••••";
                                  return acc;
                                }, {}) 
                              : { query: "mutation { ... }" },
                            null,
                            2
                          )}'`}
                        </pre>
                      </div>

                      {/* expected response */}
                      <div>
                        <h4 className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)] tracking-wider flex items-center gap-1.5 mb-1.5">
                          <FileCode className="h-3.5 w-3.5" /> Expected Response (HTTP 200)
                        </h4>
                        <pre className="rounded-lg bg-black p-3.5 font-mono text-[10px] text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] overflow-x-auto">
                          {JSON.stringify(
                            activeMethodDetails?.responses?.["200"] 
                              || activeMethodDetails?.responses?.["201"] 
                              || { status: "success", object: "session_token" },
                            null,
                            2
                          )}
                        </pre>
                      </div>
                    </div>
                  )}

                  {specTab === "schema" && (
                    <pre className="max-h-96 overflow-auto rounded-lg bg-[#050508] p-4 font-mono text-[11px] text-[var(--stitch-accent-violet)] border border-[var(--stitch-border)]">
                      {JSON.stringify(
                        activeMethodDetails?.requestBody?.content?.["application/json"]?.schema 
                          || { type: "object", properties: {} },
                        null,
                        2
                      )}
                    </pre>
                  )}
                </CardContent>

              </Card>
            </div>

          </div>
        )}

      </div>
    </SiteScaffold>
  );
}