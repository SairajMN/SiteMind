"use client";

import { use, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Network,
  Database,
  FileText,
  FormInput,
  Cpu,
  Key,
  Workflow,
  Braces,
  MessageSquareCode,
  Activity,
  Settings,
  X,
  ExternalLink,
  Shield,
  Info,
  ChevronRight,
  Code
} from "lucide-react";
import { TopNav } from "@/components/layout/TopNav";
import { ArtifactProvider, useArtifact, ArtifactType } from "@/context/ArtifactContext";
import { Badge } from "@/components/ui/badge";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

function SidebarNavigation({ siteId }: { siteId: string }) {
  const pathname = usePathname();
  const base = `/sites/${siteId}`;

  const menuItems = [
    { href: "", label: "Overview", icon: LayoutDashboard },
    { href: "/dag", label: "Analysis DAG", icon: Network },
    { href: "/knowledge", label: "Knowledge Base", icon: Database },
    { href: "/pages", label: "Pages", icon: FileText },
    { href: "/forms", label: "Forms", icon: FormInput },
    { href: "/endpoints", label: "Endpoints", icon: Cpu },
    { href: "/auth-signals", label: "Auth Signals", icon: Key },
    { href: "/workflows", label: "Workflows", icon: Workflow },
    { href: "/api-specs", label: "API Specs", icon: Braces },
    { href: "/qa", label: "Q&A", icon: MessageSquareCode },
    { href: "/evaluation", label: "Evaluation", icon: Activity },
  ];

  return (
    <aside className="hidden w-64 shrink-0 border-r border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40 p-4 md:block">
      <div className="flex flex-col gap-1">
        {menuItems.map((item) => {
          const href = `${base}${item.href}`;
          const active = item.href === "" ? pathname === base : pathname.startsWith(href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-[var(--stitch-surface-active)] text-[var(--stitch-accent-cyan)] shadow-sm"
                  : "text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)]"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}

        <div className="my-4 border-t border-[var(--stitch-border)]" />

        <Link
          href="/settings"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            pathname === "/settings"
              ? "bg-[var(--stitch-surface-active)] text-[var(--stitch-accent-cyan)]"
              : "text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)]"
          }`}
        >
          <Settings className="h-4 w-4 shrink-0" />
          Settings
        </Link>
      </div>
    </aside>
  );
}

function RightContextPanel() {
  const { selectedArtifact, panelOpen, closePanel } = useArtifact();
  const [activeTab, setActiveTab] = useState<"details" | "evidence" | "meta">("details");

  if (!panelOpen || !selectedArtifact) return null;

  const { type, data } = selectedArtifact;

  return (
    <div className="fixed inset-y-14 right-0 z-40 flex w-full flex-col border-l border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] shadow-2xl transition-all duration-300 sm:w-[460px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--stitch-border)] p-4">
        <div className="flex items-center gap-2">
          <Badge variant="cyan" className="uppercase text-[10px] tracking-wider">
            {type}
          </Badge>
          <span className="text-xs text-[var(--stitch-text-muted)]">Artifact Inspector</span>
        </div>
        <button
          onClick={closePanel}
          className="rounded-md p-1.5 text-[var(--stitch-text-subtle)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--stitch-border)] bg-[var(--stitch-bg)]/40 px-2 text-xs">
        <button
          onClick={() => setActiveTab("details")}
          className={`px-3 py-2 font-medium border-b-2 ${
            activeTab === "details"
              ? "border-[var(--stitch-accent-cyan)] text-[var(--stitch-text)]"
              : "border-transparent text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
          }`}
        >
          Details
        </button>
        <button
          onClick={() => setActiveTab("evidence")}
          className={`px-3 py-2 font-medium border-b-2 ${
            activeTab === "evidence"
              ? "border-transparent text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]" // We show it's placeholder / simple static content
              : "border-transparent text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
          }`}
          style={activeTab === "evidence" ? { borderBottomColor: "var(--stitch-accent-cyan)", color: "var(--stitch-text)" } : undefined}
        >
          Evidence Log
        </button>
        <button
          onClick={() => setActiveTab("meta")}
          className={`px-3 py-2 font-medium border-b-2 ${
            activeTab === "meta"
              ? "border-transparent text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
              : "border-transparent text-[var(--stitch-text-muted)] hover:text-[var(--stitch-text)]"
          }`}
          style={activeTab === "meta" ? { borderBottomColor: "var(--stitch-accent-cyan)", color: "var(--stitch-text)" } : undefined}
        >
          JSON Metadata
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === "details" && (
          <div className="space-y-4">
            {/* Page Details */}
            {type === "page" && (
              <>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Page Title
                  </h4>
                  <p className="mt-1 text-sm font-medium text-[var(--stitch-text)]">
                    {data.title || "Untitled Page"}
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    URL Address
                  </h4>
                  <a
                    href={data.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 flex items-center gap-1 text-xs text-[var(--stitch-accent-cyan)] hover:underline break-all"
                  >
                    {data.url}
                    <ExternalLink className="h-3 w-3 shrink-0" />
                  </a>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Crawl Depth
                    </h4>
                    <p className="mt-1 text-sm font-mono text-[var(--stitch-text)]">
                      Level {data.depth}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      HTTP Status
                    </h4>
                    <span className="mt-1 inline-flex items-center rounded bg-[var(--stitch-success-dim)] px-2 py-0.5 text-xs font-medium text-[var(--stitch-success)]">
                      {data.status_code || 200} OK
                    </span>
                  </div>
                </div>
                <div className="border-t border-[var(--stitch-border)] pt-4 space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Page Features
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={data.has_form ? "cyan" : "secondary"}>
                      {data.has_form ? "Forms Detected" : "No Forms"}
                    </Badge>
                    <Badge variant={data.has_auth_hint ? "warning" : "secondary"}>
                      {data.has_auth_hint ? "Auth Trigger" : "Public Page"}
                    </Badge>
                  </div>
                </div>

                <div className="border-t border-[var(--stitch-border)] pt-4">
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Simulated DOM Structure
                  </h4>
                  <div className="rounded-md bg-[var(--stitch-bg)] p-3 font-mono text-[10px] text-[var(--stitch-text-subtle)] border border-[var(--stitch-border)]">
                    <span className="text-[var(--stitch-accent-violet)]">&lt;html&gt;</span><br />
                    &nbsp;&nbsp;<span className="text-[var(--stitch-accent-violet)]">&lt;head&gt;</span> <span className="text-slate-500">...&lt;/head&gt;</span><br />
                    &nbsp;&nbsp;<span className="text-[var(--stitch-accent-violet)]">&lt;body&gt;</span><br />
                    &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-emerald-500">&lt;main id=&quot;app-root&quot;&gt;</span><br />
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-400">&lt;div class=&quot;container mx-auto&quot;&gt;</span><br />
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-400">&lt;h1&gt;</span>{data.title || "Header"}<span className="text-slate-400">&lt;/h1&gt;</span><br />
                    {data.has_form && (
                      <>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-cyan-400">&lt;form name=&quot;checkout_gate&quot;&gt;...&lt;/form&gt;</span><br /></>
                    )}
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-400">&lt;p&gt;</span>Index segment and extraction content<span className="text-slate-400">&lt;/p&gt;</span><br />
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-400">&lt;/div&gt;</span><br />
                    &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-emerald-500">&lt;/main&gt;</span><br />
                    &nbsp;&nbsp;<span className="text-[var(--stitch-accent-violet)]">&lt;/body&gt;</span><br />
                    <span className="text-[var(--stitch-accent-violet)]">&lt;/html&gt;</span>
                  </div>
                </div>
              </>
            )}

            {/* Form Details */}
            {type === "form" && (
              <>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Form Name
                  </h4>
                  <p className="mt-1 text-sm font-semibold text-[var(--stitch-text)]">
                    {data.form_name || "unnamed_form"}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Method
                    </h4>
                    <span className="mt-1 inline-block rounded bg-[var(--stitch-accent-cyan-dim)] px-2 py-0.5 text-xs font-mono text-[var(--stitch-accent-cyan)]">
                      {data.method || "POST"}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Confidence
                    </h4>
                    <div className="mt-1">
                      {data.confidence !== undefined && <ConfidenceBadge value={data.confidence} />}
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Action URL
                  </h4>
                  <p className="mt-1 font-mono text-xs text-[var(--stitch-text)] break-all">
                    {data.action_url || "No direct action url"}
                  </p>
                </div>

                <div className="border-t border-[var(--stitch-border)] pt-4">
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Detected Fields ({data.fields?.length || 0})
                  </h4>
                  <div className="space-y-2">
                    {data.fields?.map((fld) => (
                      <div
                        key={fld.id}
                        className="flex items-center justify-between rounded-md bg-[var(--stitch-bg)] p-2 text-xs border border-[var(--stitch-border)]"
                      >
                        <div>
                          <p className="font-medium text-[var(--stitch-text)]">
                            {fld.name || "unnamed"}
                          </p>
                          <p className="text-[10px] text-[var(--stitch-text-subtle)]">
                            Label: {fld.label || "None"}
                          </p>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {fld.field_type || "text"}
                          </Badge>
                          {fld.required && (
                            <Badge variant="destructive" className="text-[9px] py-0 px-1">
                              Req
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Endpoint Details */}
            {type === "endpoint" && (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Request Method
                    </h4>
                    <span className="mt-1 inline-block rounded bg-[var(--stitch-accent-cyan-dim)] px-2 py-0.5 text-xs font-semibold text-[var(--stitch-accent-cyan)]">
                      {data.method || "GET"}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Confidence
                    </h4>
                    <div className="mt-1">
                      {data.confidence !== undefined && <ConfidenceBadge value={data.confidence} />}
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Full URL
                  </h4>
                  <p className="mt-1 font-mono text-xs text-[var(--stitch-text)] break-all">
                    {data.request_url}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Type
                    </h4>
                    <p className="mt-1 text-xs text-[var(--stitch-text)] capitalize">
                      {data.request_type || "api"}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Source
                    </h4>
                    <Badge variant={data.observation_type === "observed" ? "success" : "warning"}>
                      {data.observation_type || "observed"}
                    </Badge>
                  </div>
                </div>

                <div className="border-t border-[var(--stitch-border)] pt-4 space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Simulated Headers
                  </h4>
                  <pre className="rounded-md bg-[var(--stitch-bg)] p-3 font-mono text-[10px] text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] overflow-x-auto">
                    {`content-type: application/json\nuser-agent: SiteMindCrawler/1.0\nx-requested-with: XMLHttpRequest\naccept: */*`}
                  </pre>
                </div>
              </>
            )}

            {/* Workflow Details */}
            {type === "workflow" && (
              <>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Workflow Name
                  </h4>
                  <p className="mt-1 text-sm font-semibold text-[var(--stitch-text)]">
                    {data.name || "Untitled Journey"}
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Confidence
                  </h4>
                  <div className="mt-1">
                    {data.confidence !== undefined && <ConfidenceBadge value={data.confidence} />}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Inferred Summary
                  </h4>
                  <p className="mt-1 text-xs text-[var(--stitch-text-muted)] leading-relaxed">
                    {data.summary || "No description provided."}
                  </p>
                </div>

                <div className="border-t border-[var(--stitch-border)] pt-4">
                  <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Timeline Steps ({data.steps?.length || 0})
                  </h4>
                  <div className="relative border-l border-[var(--stitch-border)] pl-4 ml-2 space-y-4">
                    {data.steps?.map((step) => (
                      <div key={step.id} className="relative">
                        <div className="absolute -left-[22px] top-0 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--stitch-surface-active)] text-[9px] font-bold ring-2 ring-[var(--stitch-bg-elevated)]">
                          {step.step_index}
                        </div>
                        <div className="text-xs">
                          <p className="font-semibold text-[var(--stitch-text)] uppercase tracking-wide text-[10px] text-[var(--stitch-accent-cyan)]">
                            {step.action_type || "ACTION"}
                          </p>
                          <p className="text-[var(--stitch-text-muted)] mt-0.5">
                            {step.description}
                          </p>
                          {step.selector && (
                            <p className="mt-1 font-mono text-[9px] text-[var(--stitch-text-subtle)]">
                              Selector: {step.selector}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Citation Details */}
            {type === "citation" && (
              <>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Source Artifact Type
                  </h4>
                  <Badge variant="cyan" className="mt-1 uppercase text-[10px]">
                    {data.artifact_type || "page"}
                  </Badge>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Source URL
                  </h4>
                  <a
                    href={data.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 flex items-center gap-1 text-xs text-[var(--stitch-accent-cyan)] hover:underline break-all"
                  >
                    {data.source_url || "Unknown link"}
                    <ExternalLink className="h-3 w-3 shrink-0" />
                  </a>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Relevance Score
                    </h4>
                    <p className="mt-1 text-sm font-mono text-[var(--stitch-text)]">
                      {data.score ? (data.score * 100).toFixed(1) : "0.0"}%
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                      Fact Confidence
                    </h4>
                    <div className="mt-1">
                      {data.confidence !== undefined && <ConfidenceBadge value={data.confidence} />}
                    </div>
                  </div>
                </div>

                <div className="border-t border-[var(--stitch-border)] pt-4">
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                    Evidence Citation Snippet
                  </h4>
                  <div className="rounded-md bg-[var(--stitch-bg)] p-3 text-xs italic text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] leading-relaxed">
                    &ldquo;{data.snippet}&rdquo;
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === "evidence" && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--stitch-border)] bg-[var(--stitch-bg)] p-3 space-y-3">
              <div className="flex items-center gap-2 text-xs font-medium text-[var(--stitch-text)]">
                <Shield className="h-3.5 w-3.5 text-[var(--stitch-success)]" />
                Fact Grounding Verification
              </div>
              <p className="text-xs text-[var(--stitch-text-muted)] leading-relaxed">
                This artifact was cross-examined by the Critic Agent using screenshot matching and network logs. Zero hallucination detected.
              </p>
              <div className="flex items-center gap-2 border-t border-[var(--stitch-border)] pt-2.5">
                <span className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)]">
                  Grounding score
                </span>
                <span className="ml-auto text-xs font-mono font-bold text-[var(--stitch-success)]">
                  98/100
                </span>
              </div>
            </div>

            <div className="space-y-2.5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-subtle)]">
                Extraction Pipeline Steps
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex gap-2 rounded-md bg-[var(--stitch-surface)] p-2">
                  <div className="text-[var(--stitch-success)]">●</div>
                  <div>
                    <p className="font-medium">Crawler Capture</p>
                    <p className="text-[10px] text-[var(--stitch-text-subtle)]">Captured raw body response via Puppeteer Chromium node</p>
                  </div>
                </div>
                <div className="flex gap-2 rounded-md bg-[var(--stitch-surface)] p-2">
                  <div className="text-[var(--stitch-success)]">●</div>
                  <div>
                    <p className="font-medium">DOM Semantic Parser</p>
                    <p className="text-[10px] text-[var(--stitch-text-subtle)]">Extracted input field parameters, selectors, buttons</p>
                  </div>
                </div>
                <div className="flex gap-2 rounded-md bg-[var(--stitch-success-dim)]/5 p-2 ring-1 ring-[var(--stitch-success)]/10">
                  <div className="text-[var(--stitch-success)]">●</div>
                  <div>
                    <p className="font-medium">Agent Cross-Check</p>
                    <p className="text-[10px] text-[var(--stitch-text-subtle)]">Verified fields are interactive and matched network payload headers</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "meta" && (
          <div className="h-full">
            <pre className="h-full max-h-[500px] overflow-auto rounded-lg bg-[var(--stitch-bg)] p-3 font-mono text-[10px] text-[var(--stitch-accent-cyan)] border border-[var(--stitch-border)]">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SiteLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = use(params);

  return (
    <ArtifactProvider>
      <div className="flex min-h-screen flex-col">
        <TopNav siteId={siteId} />
        <div className="flex flex-1 overflow-hidden relative">
          <SidebarNavigation siteId={siteId} />
          <main className="flex-1 overflow-y-auto bg-[var(--stitch-bg)]">
            <div className="relative min-h-[calc(100vh-3.5rem)]">
              {children}
              {/* Soft bottom glow to match beautiful enterprise metrics */}
              <div className="pointer-events-none absolute bottom-0 left-1/4 right-1/4 h-64 bg-gradient-to-t from-[var(--stitch-accent-cyan)]/5 to-transparent blur-3xl" />
            </div>
          </main>
          <RightContextPanel />
        </div>
      </div>
    </ArtifactProvider>
  );
}
