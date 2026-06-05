"use client";

import { use, useEffect, useState } from "react";
import {
  FormInput,
  Lock,
  Globe,
  Settings,
  HelpCircle,
  Eye,
  Workflow,
  ArrowRight
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getForms, type FormSummary } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { useArtifact } from "@/context/ArtifactContext";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

export default function FormsAnalyzerPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { setSelectedArtifact, selectedArtifact } = useArtifact();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getForms(siteId)
      .then((res) => {
        setForms(res.forms);
        setLoading(false);
      })
      .catch(() => {
        const mock = getMockSite(siteId);
        if (mock) {
          setForms(mock.forms);
        } else {
          setError("Failed to load form entries.");
        }
        setLoading(false);
      });
  }, [siteId]);

  return (
    <SiteScaffold
      siteId={siteId}
      title="Form Intelligence Analyzer"
      description="Reverse-engineered interactive HTML forms. SiteMind maps input tags, constraints, client-side validations, and maps submission payloads to downstream API endpoints."
    >
      <div className="space-y-6">
        
        {loading ? (
          <div className="flex min-h-[200px] items-center justify-center text-xs text-[var(--stitch-text-muted)]">
            Analyzing DOM form registries...
          </div>
        ) : error ? (
          <div className="p-4 text-xs text-[var(--stitch-error)] text-center">{error}</div>
        ) : forms.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[220px] rounded-xl border border-dashed border-[var(--stitch-border)] p-8 text-center text-xs text-[var(--stitch-text-muted)] bg-[var(--stitch-bg-elevated)]/20">
            <FormInput className="h-8 w-8 text-[var(--stitch-text-subtle)] mb-2" />
            <p className="font-medium">No interactive forms extracted</p>
            <p className="text-[11px] text-[var(--stitch-text-subtle)] mt-1">
              Ensure crawler budget covers pages with form nodes, or check settings for screenshots and DOM extraction.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {forms.map((form) => {
              const isSelected = selectedArtifact?.type === "form" && selectedArtifact.data.id === form.id;
              return (
                <Card
                  key={form.id}
                  onClick={() => setSelectedArtifact({ type: "form", data: form })}
                  className={`border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60 hover:bg-[var(--stitch-bg-elevated)] transition-all cursor-pointer shadow-sm ${
                    isSelected ? "ring-1 ring-[var(--stitch-accent-cyan)] shadow-[var(--stitch-shadow-glow)]" : ""
                  }`}
                >
                  <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FormInput className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
                        <CardTitle className="text-sm font-semibold truncate max-w-[200px] text-[var(--stitch-text)]">
                          {form.form_name || "unnamed_form"}
                        </CardTitle>
                      </div>
                      <div className="flex items-center gap-2">
                        {form.confidence !== undefined && <ConfidenceBadge value={form.confidence} />}
                        <Badge variant="outline" className="text-[10px] font-mono py-0">
                          {form.method || "POST"}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="mt-2 space-y-1">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                        Action endpoint
                      </p>
                      <p className="font-mono text-xs text-[var(--stitch-text-muted)] truncate select-all">
                        {form.action_url || "Local Handler (Action URL unspecified)"}
                      </p>
                    </div>
                  </CardHeader>

                  <CardContent className="pt-4 space-y-4">
                    {/* Fields List */}
                    <div className="space-y-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                        Fields Mapped ({form.fields.length})
                      </p>
                      <div className="divide-y divide-[var(--stitch-border)]">
                        {form.fields.map((f) => (
                          <div key={f.id} className="flex items-center justify-between py-2 text-xs">
                            <div className="min-w-0 pr-2">
                              <span className="font-semibold text-[var(--stitch-text)] truncate block">
                                {f.name || "unnamed"}
                              </span>
                              {f.label && (
                                <span className="text-[10px] text-[var(--stitch-text-subtle)] truncate block">
                                  Label: &ldquo;{f.label}&rdquo;
                                </span>
                              )}
                            </div>
                            
                            <div className="flex items-center gap-1.5 shrink-0">
                              <Badge variant="secondary" className="font-mono text-[9px] py-0">
                                {f.field_type || "text"}
                              </Badge>
                              {f.required && (
                                <Badge variant="destructive" className="text-[8px] py-0 px-1">
                                  Req
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Footer / Right drawer trigger link */}
                    <div className="flex items-center justify-between pt-3 border-t border-[var(--stitch-border)] text-xs text-[var(--stitch-text-subtle)]">
                      <span className="flex items-center gap-1.5">
                        <Workflow className="h-3.5 w-3.5 text-[var(--stitch-accent-violet)]" />
                        Linked to Workflow miner
                      </span>
                      <span className="flex items-center gap-1 text-[var(--stitch-accent-cyan)] group hover:underline">
                        Inspect Details
                        <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </SiteScaffold>
  );
}
