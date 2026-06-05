"use client";

import { use, useEffect, useState } from "react";
import {
  Key,
  Shield,
  Lock,
  Unlock,
  AlertTriangle,
  ArrowRight,
  Database,
  RefreshCcw,
  FileKey
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getPages, getForms, getEndpoints, type PageSummary, type FormSummary, type EndpointSummary } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

interface AuthSignal {
  type: "cookie" | "token" | "form" | "redirect";
  name: string;
  source: string;
  confidence: number;
  extractedValue: string;
}

interface ProtectedRoute {
  path: string;
  type: string;
  status: number;
  validation: string;
}

export default function AuthSignalsPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  const [authSignals, setAuthSignals] = useState<AuthSignal[]>([]);
  const [protectedRoutes, setProtectedRoutes] = useState<ProtectedRoute[]>([]);
  const [loginGateway, setLoginGateway] = useState<string>("/login");
  const [authPagesCount, setAuthPagesCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      getPages(siteId).catch(() => null),
      getForms(siteId).catch(() => null),
      getEndpoints(siteId).catch(() => null),
    ])
      .then(([pagesRes, formsRes, endpointsRes]) => {
        const pages: PageSummary[] = pagesRes?.pages ?? [];
        const forms: FormSummary[] = formsRes?.forms ?? [];
        const endpoints: EndpointSummary[] = endpointsRes?.endpoints ?? [];

        const signals: AuthSignal[] = [];
        const routes: ProtectedRoute[] = [];

        // 1. Form-based login signals
        forms.forEach((form) => {
          const fieldNames = (form.fields || []).map((f) => (f.name || "").toLowerCase());
          const isLogin =
            fieldNames.some((n) => n.includes("email") || n.includes("user") || n.includes("login")) &&
            fieldNames.some((n) => n.includes("password") || n.includes("pass"));
          if (isLogin && form.action_url) {
            signals.push({
              type: "form",
              name: "Login Gateway Form",
              source: form.action_url,
              confidence: form.confidence ?? 0.9,
              extractedValue: `action='${form.action_url}', method='${form.method || "POST"}', fields=[${fieldNames.join(", ")}]`,
            });
          }
        });

        // 2. Auth-hinted pages
        const authPages = pages.filter((p) => p.has_auth_hint);
        setAuthPagesCount(authPages.length);
        if (authPages.length > 0) {
          const gateway = authPages[0];
          setLoginGateway(gateway.path || "/login");
          signals.push({
            type: "redirect",
            name: "Login Auth Handshake",
            source: gateway.url,
            confidence: 0.9,
            extractedValue: `Page marked with auth hint: ${gateway.title || gateway.url}`,
          });
        }

        // 3. Endpoints matching auth patterns
        endpoints.forEach((ep) => {
          const url = ep.request_url.toLowerCase();
          if (url.includes("/login") || url.includes("/auth") || url.includes("/session") || url.includes("/token")) {
            signals.push({
              type: "token",
              name: "Authentication Endpoint",
              source: ep.request_url,
              confidence: ep.confidence ?? 0.85,
              extractedValue: `${ep.method || "POST"} ${ep.request_url} (observed network trace)`,
            });
          }
          if (url.includes("cookie") || url.includes("session")) {
            signals.push({
              type: "cookie",
              name: "Session Cookie Identifier",
              source: ep.request_url,
              confidence: ep.confidence ?? 0.8,
              extractedValue: `Endpoint pattern detected: ${ep.request_url}`,
            });
          }
          if (ep.status_code === 401 || ep.status_code === 403 || ep.status_code === 302) {
            try {
              routes.push({
                path: new URL(ep.request_url).pathname,
                type: "api",
                status: ep.status_code,
                validation:
                  ep.status_code === 302
                    ? "Redirected (likely to login)"
                    : ep.status_code === 401
                      ? "HTTP 401 Unauthorized"
                      : "HTTP 403 Forbidden",
              });
            } catch {
              // ignore malformed URLs
            }
          }
        });

        // 4. Pages with auth hints -> protected routes
        authPages.forEach((p) => {
          routes.push({
            path: p.path || p.url,
            type: p.has_form ? "dashboard" : "page",
            status: p.status_code && p.status_code >= 400 ? p.status_code : 302,
            validation: p.status_code && p.status_code >= 400 ? "Access Denied" : "Redirected to /login",
          });
        });

        setAuthSignals(signals);
        setProtectedRoutes(routes);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to derive auth signals.");
        setAuthSignals([]);
        setProtectedRoutes([]);
        setLoading(false);
      });
  }, [siteId]);

  return (
    <SiteScaffold
      siteId={siteId}
      title="Authentication Signals"
      description="Identity & session mapping records. Detects auth pages, cookie trackers, token patterns, and lists protected routes."
    >
      <div className="space-y-6">
        {loading ? (
          <div className="flex min-h-[200px] items-center justify-center text-xs text-[var(--stitch-text-muted)]">
            Scanning for authentication patterns...
          </div>
        ) : error ? (
          <div className="rounded-lg border border-[var(--stitch-error)]/30 bg-[var(--stitch-error)]/5 p-4 text-xs text-[var(--stitch-error)]">
            {error}
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                <CardHeader className="pb-2">
                  <CardDescription className="text-xs uppercase tracking-wider text-[var(--stitch-text-subtle)]">Auth Mechanism</CardDescription>
                  <CardTitle className="text-base font-bold flex items-center gap-1.5">
                    <Shield className="h-4.5 w-4.5 text-[var(--stitch-success)]" />
                    {authSignals.length > 0 ? "Detected" : "None Detected"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant={authSignals.length > 0 ? "success" : "secondary"} className="text-[10px]">
                    {authSignals.length > 0 ? "Active" : "Inactive"}
                  </Badge>
                </CardContent>
              </Card>

              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                <CardHeader className="pb-2">
                  <CardDescription className="text-xs uppercase tracking-wider text-[var(--stitch-text-subtle)]">Login Gateway</CardDescription>
                  <CardTitle className="text-base font-bold flex items-center gap-1.5 truncate">
                    <Lock className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />
                    {loginGateway}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="text-[10px]">
                    {authPagesCount > 0 ? `${authPagesCount} auth-hinted` : "No hints"}
                  </Badge>
                </CardContent>
              </Card>

              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                <CardHeader className="pb-2">
                  <CardDescription className="text-xs uppercase tracking-wider text-[var(--stitch-text-subtle)]">Protected Routes</CardDescription>
                  <CardTitle className="text-base font-bold flex items-center gap-1.5">
                    <AlertTriangle className="h-4.5 w-4.5 text-[var(--stitch-error)]" />
                    {protectedRoutes.length} Found
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant={protectedRoutes.length > 0 ? "destructive" : "secondary"} className="text-[10px]">
                    {protectedRoutes.length > 0 ? "Auth Required" : "None"}
                  </Badge>
                </CardContent>
              </Card>
            </div>

            <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Authentication Handshake Cycle</CardTitle>
                <CardDescription className="text-xs">Visual redirection flow discovered by the Crawler agent.</CardDescription>
              </CardHeader>
              <CardContent className="py-4">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 px-4">
                  <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                    <Badge variant="outline" className="text-[9px]">Step 1</Badge>
                    <Lock className="h-5 w-5 text-[var(--stitch-text-subtle)]" />
                    <h4 className="text-xs font-semibold">Secure Page Access</h4>
                    <p className="text-[10px] text-[var(--stitch-text-muted)]">User requests protected resource</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />
                  <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                    <Badge variant="warning" className="text-[9px]">Step 2</Badge>
                    <RefreshCcw className="h-5 w-5 text-[var(--stitch-warning)] animate-spin" style={{ animationDuration: "8s" }} />
                    <h4 className="text-xs font-semibold">302 Redirect</h4>
                    <p className="text-[10px] text-[var(--stitch-text-muted)]">Server returns Auth Challenge</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />
                  <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                    <Badge variant="cyan" className="text-[9px]">Step 3</Badge>
                    <Key className="h-5 w-5 text-[var(--stitch-accent-cyan)]" />
                    <h4 className="text-xs font-semibold">Form credentials</h4>
                    <p className="text-[10px] text-[var(--stitch-text-muted)]">User submits email &amp; password</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />
                  <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                    <Badge variant="success" className="text-[9px]">Step 4</Badge>
                    <Unlock className="h-5 w-5 text-[var(--stitch-success)]" />
                    <h4 className="text-xs font-semibold">JWT Bind</h4>
                    <p className="text-[10px] text-[var(--stitch-text-muted)]">Token stored, access allowed</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                <CardHeader className="pb-2 border-b border-[var(--stitch-border)]">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                    <Database className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
                    Authentication Signals Detected
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 text-xs">
                  {authSignals.length === 0 ? (
                    <div className="p-6 text-center text-[var(--stitch-text-subtle)]">
                      No auth patterns detected in the crawled artifacts.
                    </div>
                  ) : (
                    <div className="divide-y divide-[var(--stitch-border)]">
                      {authSignals.map((signal, idx) => (
                        <div key={idx} className="p-3.5 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[var(--stitch-text)]">{signal.name}</span>
                            <ConfidenceBadge value={signal.confidence} />
                          </div>
                          <p className="text-[10px] text-[var(--stitch-text-subtle)]">Discovered: {signal.source}</p>
                          <pre className="mt-1.5 rounded bg-[var(--stitch-bg)] p-2 font-mono text-[10px] text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                            {signal.extractedValue}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
                <CardHeader className="pb-2 border-b border-[var(--stitch-border)]">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                    <FileKey className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />
                    Protected Route Catalog
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 text-xs">
                  {protectedRoutes.length === 0 ? (
                    <div className="p-6 text-center text-[var(--stitch-text-subtle)]">
                      No protected routes observed.
                    </div>
                  ) : (
                    <div className="divide-y divide-[var(--stitch-border)]">
                      {protectedRoutes.map((route, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3.5">
                          <div className="space-y-0.5 min-w-0 pr-2">
                            <p className="font-mono font-semibold text-[var(--stitch-text)] truncate">{route.path}</p>
                            <p className="text-[10px] text-[var(--stitch-text-subtle)]">Validation type: {route.type}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <Badge variant="destructive" className="font-mono text-[9px] py-0">{route.status}</Badge>
                            <p className="text-[10px] text-[var(--stitch-text-muted)] mt-0.5">{route.validation}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </SiteScaffold>
  );
}
