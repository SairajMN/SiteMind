import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
      <p className="mt-2 text-sm text-[var(--stitch-text-muted)]">
        Configure frontend connectivity and display preferences.
      </p>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="text-base">API connection</CardTitle>
          <CardDescription>
            Set <code className="text-[var(--stitch-accent-cyan)]">NEXT_PUBLIC_API_BASE_URL</code> in{" "}
            <code>.env.local</code> to point at your SiteMind backend.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Current API base</label>
            <Input readOnly value={apiBase} className="font-mono text-xs" />
          </div>
          <p className="text-xs text-[var(--stitch-text-subtle)]">
            All requests use the envelope format:{" "}
            <code>{`{ data, error }`}</code>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
