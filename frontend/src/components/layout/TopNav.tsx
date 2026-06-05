"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BrainCircuit, Search, Bell, BookOpen, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const siteLinks = [
  { href: "", label: "Overview" },
  { href: "/dag", label: "DAG" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/workflows", label: "Workflows" },
  { href: "/api-specs", label: "API Specs" },
  { href: "/qa", label: "Q&A" },
  { href: "/evaluation", label: "Evaluation" },
] as const;

export type TopNavProps = {
  siteId?: string;
};

export function TopNav({ siteId }: TopNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const base = siteId ? `/sites/${siteId}` : "";

  const handleSiteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextSite = e.target.value;
    if (nextSite === "new") {
      router.push("/");
    } else {
      router.push(`/sites/${nextSite}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--stitch-border)] bg-[var(--stitch-bg)]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-4 px-4 sm:px-6">
        {/* Logo */}
        <Link href="/" className="flex shrink-0 items-center gap-2 mr-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--stitch-accent-cyan-dim)] ring-1 ring-[var(--stitch-border-accent)]">
            <BrainCircuit className="h-4 w-4 text-[var(--stitch-accent-cyan)]" />
          </div>
          <span className="text-sm font-semibold tracking-tight hidden sm:inline-block">
            Site<span className="text-gradient font-bold">Mind</span>
          </span>
        </Link>

        {/* Site Selector Dropdown */}
        {siteId && (
          <div className="relative flex items-center gap-1 bg-[var(--stitch-surface)] hover:bg-[var(--stitch-surface-hover)] rounded-md border border-[var(--stitch-border)] px-2.5 py-1 text-xs text-[var(--stitch-text)] transition-colors">
            <select
              value={siteId}
              onChange={handleSiteChange}
              className="appearance-none bg-transparent pr-6 font-medium focus:outline-none cursor-pointer"
            >
              <option value="stripe">stripe.com</option>
              <option value="github">github.com</option>
              <option value="linear">linear.app</option>
              <option value="new">+ Start New Crawl</option>
            </select>
            <ChevronDown className="absolute right-2.5 pointer-events-none h-3 w-3 text-[var(--stitch-text-subtle)]" />
          </div>
        )}

        {/* Search Bar Container */}
        <div className="hidden max-w-sm flex-1 md:block relative">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[var(--stitch-text-subtle)]" />
            <input
              type="text"
              placeholder="Search pages, forms, endpoints... (Cmd+K)"
              className="w-full h-8.5 rounded-md border border-[var(--stitch-border)] bg-[var(--stitch-surface)]/60 py-1.5 pl-9 pr-4 text-xs text-[var(--stitch-text)] placeholder-[var(--stitch-text-subtle)] focus:border-[var(--stitch-border-strong)] focus:bg-[var(--stitch-surface)] focus:outline-none"
              readOnly
              onClick={() => alert("Search command palette is simulated. Try typing Q&A queries directly inside the Q&A workspace!")}
            />
            <kbd className="absolute right-3 top-2.5 pointer-events-none hidden items-center gap-0.5 rounded border border-[var(--stitch-border)] bg-[var(--stitch-surface-active)] px-1.5 font-mono text-[9px] text-[var(--stitch-text-subtle)] md:flex">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Mid-Navigation (Responsive only) */}
        {siteId && (
          <nav className="flex items-center gap-0.5 md:hidden">
            <Link
              href={`${base}`}
              className={cn(
                "rounded px-2.5 py-1 text-xs",
                pathname === base ? "text-[var(--stitch-accent-cyan)] font-medium" : "text-[var(--stitch-text-muted)]"
              )}
            >
              Overview
            </Link>
            <Link
              href={`${base}/dag`}
              className={cn(
                "rounded px-2.5 py-1 text-xs",
                pathname.startsWith(`${base}/dag`) ? "text-[var(--stitch-accent-cyan)] font-medium" : "text-[var(--stitch-text-muted)]"
              )}
            >
              DAG
            </Link>
          </nav>
        )}

        {/* Right Nav Options */}
        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          {/* Docs button */}
          <Link
            href="/docs"
            onClick={(e) => {
              e.preventDefault();
              alert("SiteMind Documentation site is under construction. Please use Q&A to ask direct model questions!");
            }}
            className="rounded-md p-2 text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)] transition-colors hidden sm:block"
            title="API Documentation"
          >
            <BookOpen className="h-4 w-4" />
          </Link>

          {/* Notifications bell */}
          <button
            onClick={() => alert("You have 2 new notifications: \n- Crawl stripe.com completed.\n- API spec generated successfully.")}
            className="relative rounded-md p-2 text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)] transition-colors"
            title="Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1 right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--stitch-accent-cyan)] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--stitch-accent-cyan)]"></span>
            </span>
          </button>

          {/*  profile dropdown placeholder */}
          <div className="flex items-center gap-2 border-l border-[var(--stitch-border)] pl-3">
            <button
              onClick={() => alert("SiteMind Enterprise profile dashboard. Connected as admin@sitemind.io")}
              className="flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-[var(--stitch-accent-cyan)] to-[var(--stitch-accent-violet)] ring-1 ring-[var(--stitch-border)] text-xs font-semibold text-black hover:opacity-90 transition-opacity"
            >
              JD
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
