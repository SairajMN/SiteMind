import { type ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export type SiteScaffoldProps = {
  title: string;
  description: string;
  siteId: string;
  children?: ReactNode;
};

export function SiteScaffold({ title, description, siteId, children }: SiteScaffoldProps) {
  return (
    <div className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6">
      <div className="mb-8">
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--stitch-text-subtle)]">
          Site {siteId.slice(0, 8)}…
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--stitch-text-muted)]">
          {description}
        </p>
      </div>
      {children ?? (
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle className="text-base">Coming soon</CardTitle>
            <CardDescription>
              This view will connect to the SiteMind API when the backend pipeline is ready.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 rounded-md bg-[var(--stitch-bg-elevated)] ring-1 ring-[var(--stitch-border)]" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
