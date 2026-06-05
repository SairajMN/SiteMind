"use client";

import { use, useEffect, useState } from "react";
import {
  Key,
  Shield,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  ArrowRight,
  Database,
  RefreshCcw,
  FileKey
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { getPages, getForms, getEndpoints } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
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

export default function AuthSignalsPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // Mock structures representing authentications
  const mock = getMockSite(siteId);

  const authSignals: AuthSignal[] = mock ? [
    { type: "form", name: "Login Gateway Form", source: "dashboard.stripe.com/login", confidence: 0.98, extractedValue: "action='https://api.stripe.com/v1/auth/login', fields=['email', 'password']" },
    { type: "cookie", name: "Session Cookie Identifier", source: "stripe.com", confidence: 0.95, extractedValue: "cookie: __session_stripe_id (Secure, SameSite=Lax, HttpOnly)" },
    { type: "token", name: "Bearer Token Spec", source: "api.stripe.com", confidence: 0.96, extractedValue: "headers: 'Authorization: Bearer <pk_live_...>' pattern detected in Fetch traces" },
    { type: "redirect", name: "Login Auth Handshake", source: "stripe.com/dashboard", confidence: 0.92, extractedValue: "HTTP 302 Redirect to /login triggered on unauthenticated access" }
  ] : [
    { type: "form", name: "Login Gateway Form", source: "login.domain.com", confidence: 0.90, extractedValue: "action='/session', method='POST'" }
  ];

  const protectedRoutes = mock ? [
    { path: "/dashboard", type: "dashboard", status: 302, validation: "Redirected to /login" },
    { path: "/settings/billing", type: "checkout", status: 401, validation: "Access Denied (Bearer Token Missing)" },
    { path: "/api/v1/customers", type: "api", status: 401, validation: "HTTP 401 Unauthorized" },
    { path: "/dashboard/webhooks", type: "dashboard", status: 302, validation: "Redirected to /login" }
  ] : [
    { path: "/secure-path", type: "dashboard", status: 401, validation: "Unauthorized" }
  ];

  return (
    <SiteScaffold
      siteId={siteId}
      title="Authentication Signals"
      description="Identity & session mapping records. Detects auth pages, cookie trackers, token patterns, and lists protected routes."
    >
      <div className="space-y-6">
        
        {/* Top Summary Block */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs uppercase tracking-wider text-[var(--stitch-text-subtle)]">Auth Mechanism</CardDescription>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Shield className="h-4.5 w-4.5 text-[var(--stitch-success)]" />
                Bearer JWT / Cookie
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="success" className="text-[10px]">Active</Badge>
            </CardContent>
          </Card>

          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs uppercase tracking-wider text-[var(--stitch-text-subtle)]">Login Gateway</CardDescription>
              <CardTitle className="text-base font-bold flex items-center gap-1.5 truncate">
                <Lock className="h-4.5 w-4.5 text-[var(--stitch-warning)]" />
                {mock ? mock.pages.find(p => p.has_auth_hint)?.path || "/login" : "/login"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="outline" className="text-[10px]">Confidence 98%</Badge>
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
              <Badge variant="destructive" className="text-[10px]">Auth Required</Badge>
            </CardContent>
          </Card>
        </div>

        {/* Visual redirect handshake diagram */}
        <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/60">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Authentication Handshake Cycle</CardTitle>
            <CardDescription className="text-xs">Visual redirection flow discovered by the Crawler agent.</CardDescription>
          </CardHeader>
          <CardContent className="py-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 px-4">
              
              {/* Step 1 */}
              <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                <Badge variant="outline" className="text-[9px]">Step 1</Badge>
                <Lock className="h-5 w-5 text-[var(--stitch-text-subtle)]" />
                <h4 className="text-xs font-semibold">Secure Page Access</h4>
                <p className="text-[10px] text-[var(--stitch-text-muted)]">User requests /dashboard</p>
              </div>

              <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />

              {/* Step 2 */}
              <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                <Badge variant="warning" className="text-[9px]">Step 2</Badge>
                <RefreshCcw className="h-5 w-5 text-[var(--stitch-warning)] animate-spin" style={{ animationDuration: "8s" }} />
                <h4 className="text-xs font-semibold">302 Redirect</h4>
                <p className="text-[10px] text-[var(--stitch-text-muted)]">Server returns Auth Challenge</p>
              </div>

              <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />

              {/* Step 3 */}
              <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                <Badge variant="cyan" className="text-[9px]">Step 3</Badge>
                <Key className="h-5 w-5 text-[var(--stitch-accent-cyan)]" />
                <h4 className="text-xs font-semibold">Form credentials</h4>
                <p className="text-[10px] text-[var(--stitch-text-muted)]">User submits email & password</p>
              </div>

              <ArrowRight className="h-5 w-5 text-[var(--stitch-text-subtle)] shrink-0 hidden md:block" />

              {/* Step 4 */}
              <div className="flex flex-col items-center text-center space-y-2 bg-[var(--stitch-surface)] p-3 rounded-lg border border-[var(--stitch-border)] w-full md:w-1/4">
                <Badge variant="success" className="text-[9px]">Step 4</Badge>
                <Unlock className="h-5 w-5 text-[var(--stitch-success)]" />
                <h4 className="text-xs font-semibold">JWT Bind</h4>
                <p className="text-[10px] text(--stitch-text-muted)">Token stored, access allowed</p>
              </div>

            </div>
          </CardContent>
        </Card>

        {/* Mapped Signals & Protected Routes Ledger */}
        <div className="grid gap-6 md:grid-cols-2">
          
          {/* Left Table: Session cookies and header signals */}
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
            <CardHeader className="pb-2 border-b border-[var(--stitch-border)]">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <Database className="h-4.5 w-4.5 text-[var(--stitch-accent-cyan)]" />
                Authentication Signals Detected
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 text-xs">
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
            </CardContent>
          </Card>

          {/* Right Table: Protected URL Paths */}
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]">
            <CardHeader className="pb-2 border-b border-[var(--stitch-border)]">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <FileKey className="h-4.5 w-4.5 text-[var(--stitch-accent-violet)]" />
                Protected Route Catalog
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 text-xs">
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
            </CardContent>
          </Card>

        </div>

      </div>
    </SiteScaffold>
  );
}
