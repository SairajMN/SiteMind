"use client";

import { use, useEffect, useState } from "react";
import {
  Workflow,
  ChevronRight,
  GitCommit,
  ExternalLink,
  Link,
  Compass,
  Cpu,
  Layers,
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { getWorkflows, type WorkflowSummary, type WorkflowStepSummary } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { useArtifact } from "@/context/ArtifactContext";
import { cn } from "@/lib/utils";

export default function WorkflowsPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [hoveredStep, setHoveredStep] = useState<string | null>(null);

  const { setSelectedArtifact } = useArtifact();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getWorkflows(siteId)
      .then((res) => {
        setWorkflows(res.workflows);
        if (res.workflows.length > 0) {
          setActiveWorkflowId(res.workflows[0].id);
        }
        setLoading(false);
      })
      .catch(() => {
        // Fallback to mock data
        const mock = getMockSite(siteId);
        if (mock) {
          setWorkflows(mock.workflows);
          if (mock.workflows.length > 0) {
            setActiveWorkflowId(mock.workflows[0].id);
          }
        } else {
          setError("Failed to load workflows.");
        }
        setLoading(false);
      });
  }, [siteId]);

  const activeWorkflow = workflows.find((w) => w.id === activeWorkflowId);

  const getStepIcon = (actionType?: string) => {
    switch (actionType?.toLowerCase()) {
      case "navigate":
        return <Compass className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />;
      case "fill":
        return <Layers className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />;
      case "click":
        return <GitCommit className="h-4.5 w-4.5 text-[var(--stitch-warning)]" style={{ transform: "rotate(45deg)" }} />;
      default:
        return <Cpu className="h-4.5 w-4.5 text-[var(--stitch-text-subtle)]" />;
    }
  };

  const inspectStepEvidence = (step: WorkflowStepSummary) => {
    // Generate a temporary citation detail or map to page
    setSelectedArtifact({
      type: "citation",
      data: {
        source_url: `Page: ${step.page_id || "Unknown"}`,
        artifact_type: "workflows",
        snippet: `Step ${step.step_index}: Inferred Action '${step.action_type || "action"}' on selector '${step.selector || "none"}'. ${step.description}`,
        confidence: step.confidence || 0.90,
        score: 0.95
      }
    });
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="Workflow Explorer"
      description="Multi-step user journeys reverse-engineered from observed navigation paths, interactive form structures, and API network payloads."
    >
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-12">

        {/* Left Col: List of workflow cards */}
        <div className="lg:col-span-4 space-y-4">
          <div className="text-xs text-[var(--stitch-text-subtle)] font-medium px-1">
            DISCOVERED WORKFLOWS ({workflows.length})
          </div>
          {loading ? (
            <div className="flex min-h-[150px] items-center justify-center text-xs text-[var(--stitch-text-muted)]">
              Mapping paths...
            </div>
          ) : error ? (
            <div className="text-xs text-[var(--stitch-error)] p-2">{error}</div>
          ) : workflows.length === 0 ? (
            <div className="text-xs text-[var(--stitch-text-subtle)] p-4 border border-dashed rounded-lg text-center">
              No active workflows discovered.
            </div>
          ) : (
            <div className="space-y-3">
              {workflows.map((wf) => {
                const isActive = activeWorkflowId === wf.id;
                return (
                  <Card
                    key={wf.id}
                    onClick={() => setActiveWorkflowId(wf.id)}
                    className={cn(
                      "border-[var(--stitch-border)] hover:border-[var(--stitch-border-strong)] transition-all cursor-pointer p-4 bg-[var(--stitch-bg-elevated)]/60 hover:bg-[var(--stitch-bg-elevated)]",
                      isActive ? "ring-1 ring-[var(--stitch-accent-cyan)] shadow-sm bg-[var(--stitch-bg-elevated)]" : ""
                    )}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-[var(--stitch-text)]">{wf.name}</span>
                        {wf.confidence !== undefined && <ConfidenceBadge value={wf.confidence} />}
                      </div>
                      <p className="text-[11px] text-[var(--stitch-text-muted)] line-clamp-2 leading-relaxed">
                        {wf.summary}
                      </p>
                      <div className="flex items-center justify-between text-[10px] text-[var(--stitch-text-subtle)] pt-1 border-t border-[var(--stitch-border)]">
                        <span>{wf.steps.length} steps</span>
                        <span className="text-[var(--stitch-accent-cyan)] hover:underline flex items-center gap-0.5">
                          View details <ChevronRight className="h-3 w-3" />
                        </span>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Col: Interactive Visual step timeline */}
        <div className="lg:col-span-8">
          {activeWorkflow ? (
            <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
              <CardHeader className="border-b border-[var(--stitch-border)]">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold text-[var(--stitch-text)]">{activeWorkflow.name}</CardTitle>
                    <CardDescription className="text-xs">{activeWorkflow.summary}</CardDescription>
                  </div>
                  <Badge variant="outline" className="font-mono text-xs">{activeWorkflow.steps.length} steps</Badge>
                </div>
              </CardHeader>

              <CardContent className="pt-6">

                {/* Visual Step Timeline */}
                <div className="relative border-l border-[var(--stitch-border)] pl-6 ml-3 space-y-6">
                  {activeWorkflow.steps.map((step) => {
                    const isHovered = hoveredStep === step.id;
                    return (
                      <div
                        key={step.id}
                        onMouseEnter={() => setHoveredStep(step.id)}
                        onMouseLeave={() => setHoveredStep(null)}
                        onClick={() => inspectStepEvidence(step)}
                        className={cn(
                          "relative rounded-lg p-3 border transition-all cursor-pointer",
                          isHovered
                            ? "bg-[var(--stitch-surface-hover)] border-[var(--stitch-border-strong)] shadow-sm"
                            : "bg-[var(--stitch-surface)]/40 border-[var(--stitch-border)]"
                        )}
                      >
                        {/* Step Marker Dot */}
                        <div className="absolute -left-[35px] top-4 flex h-6.5 w-6.5 items-center justify-center rounded-full bg-[var(--stitch-surface-active)] ring-4 ring-[var(--stitch-bg-elevated)] text-[10px] font-bold text-[var(--stitch-text-subtle)] border border-[var(--stitch-border)]">
                          {step.step_index}
                        </div>

                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1.5 min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              {getStepIcon(step.action_type)}
                              <span className="font-bold text-[10px] uppercase tracking-wider text-[var(--stitch-text-muted)]">
                                {step.action_type || "ACTION"}
                              </span>
                              {step.confidence !== undefined && <ConfidenceBadge value={step.confidence} size="sm" />}
                            </div>

                            <p className="text-xs text-[var(--stitch-text)] font-semibold leading-relaxed">
                              {step.description}
                            </p>

                            {step.selector && (
                              <div className="font-mono text-[10px] text-[var(--stitch-accent-cyan)] bg-[var(--stitch-bg)]/80 p-1.5 rounded border border-[var(--stitch-border)] mt-1 truncate max-w-lg">
                                Selector: <span className="text-[var(--stitch-accent-violet)]">{step.selector}</span>
                              </div>
                            )}

                            {step.endpoint_id && (
                              <div className="flex items-center gap-2 mt-2 pt-1 border-t border-[var(--stitch-border)]/50 text-[10px] text-[var(--stitch-text-subtle)] font-mono">
                                <Link className="h-3.5 w-3.5 shrink-0" />
                                <span>Triggers network endpoint: <span className="text-[var(--stitch-success)]">{step.endpoint_id}</span></span>
                              </div>
                            )}
                          </div>

                          <ChevronRight className={cn(
                            "h-4 w-4 text-[var(--stitch-text-subtle)] transition-all mt-1 shrink-0",
                            isHovered ? "text-[var(--stitch-accent-cyan)] translate-x-0.5" : ""
                          )} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Evidence Note */}
                <div className="mt-6 border-t border-[var(--stitch-border)] pt-4 flex items-center justify-between text-xs text-[var(--stitch-text-subtle)]">
                  <span>ℹ Click on any timeline node to inspect RAG evidence context.</span>
                  <span className="text-[var(--stitch-accent-cyan)] hover:underline flex items-center gap-0.5 cursor-pointer">
                    Export JSON path <ExternalLink className="h-3 w-3" />
                  </span>
                </div>

              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40 h-full flex flex-col justify-center items-center p-8 text-center text-xs text-[var(--stitch-text-muted)]">
              <Workflow className="h-8 w-8 text-[var(--stitch-text-subtle)] mb-2 animate-pulse" />
              <p className="font-medium">No workflow selected</p>
              <p className="text-[11px] text-[var(--stitch-text-subtle)] mt-1">
                Select a user journey in the left pane to explore its timeline.
              </p>
            </Card>
          )}
        </div>

      </div>
    </SiteScaffold>
  );
}
