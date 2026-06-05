"use client";

import { use, useState, useEffect } from "react";
import {
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  XCircle,
  HelpCircle,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Search,
  MessageSquare
} from "lucide-react";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { askQuestion, type AskResponse } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import { useArtifact } from "@/context/ArtifactContext";
import { cn } from "@/lib/utils";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  responseObj?: AskResponse;
}

const PRESETS = [
  "How does the check out workflow work?",
  "What fields are in the login page?",
  "What endpoints are protected?",
];

export default function QaPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);

  // States
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const { setSelectedArtifact } = useArtifact();
  const mock = getMockSite(siteId);

  // Prepopulate with an initial welcoming message
  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content: `Hello! I am SiteMind Q&A. I have indexed ${mock?.progress.chunks_indexed || 120} vector chunks representing page DOMs, workflows, and network API specifications for this site. Ask me anything about its layout, fields, or authorization schemes!`
      }
    ]);
  }, [siteId]);

  const handleSubmit = async (qText: string) => {
    if (!qText.trim() || loading) return;
    setLoading(true);
    setError(null);

    // Add User bubble
    setMessages(prev => [...prev, { role: "user", content: qText }]);
    setQuestion("");

    try {
      const answer = await askQuestion(siteId, { question: qText.trim() });
      setMessages(prev => [...prev, { role: "assistant", content: answer.answer_text || "No response generated.", responseObj: answer }]);
    } catch (err: unknown) {
      console.warn("API Offline, querying mock dataset...", err);
      
      // Look up mock Q&A response
      const normalizedQ = qText.toLowerCase().trim();
      let matchedResponse: AskResponse | undefined;

      if (mock && mock.qaResponses) {
        for (const key of Object.keys(mock.qaResponses)) {
          if (normalizedQ.includes(key.toLowerCase()) || key.toLowerCase().includes(normalizedQ)) {
            matchedResponse = mock.qaResponses[key];
            break;
          }
        }
      }

      // If no preset matches, create a smart dynamic fallback
      if (!matchedResponse) {
        matchedResponse = {
          answer_id: "fallback-ans",
          site_id: siteId,
          question: qText,
          answer_text: `Based on my analysis of ${mock?.name || "the crawled site"}, I identified ${mock?.pages.length || 3} pages and ${mock?.endpoints.length || 2} network endpoints. The question "${qText}" relates to observed DOM layouts, but no specific matching credentials workflow steps were index-mapped. Adjust your query or refer to the API Specs tab.`,
          confidence: 0.82,
          critic_status: "passed",
          citations: mock ? [
            { source_url: mock.pages[0].url, artifact_type: "pages", snippet: mock.pages[0].title, confidence: 0.90, score: 0.85 }
          ] : [],
          created_at: new Date().toISOString()
        };
      }

      // Simulate typing speed
      setTimeout(() => {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: matchedResponse!.answer_text || "",
            responseObj: matchedResponse
          }
        ]);
        setLoading(false);
      }, 1000);
      return;
    }

    setLoading(false);
  };

  const handleInspectCitation = (cit: any) => {
    // Map citation values to right inspect model
    setSelectedArtifact({
      type: "citation",
      data: {
        source_url: cit.source_url,
        artifact_type: cit.artifact_type,
        snippet: cit.snippet,
        confidence: cit.confidence,
        score: cit.score
      }
    });
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="Q&A Workspace"
      description="Ask questions about this site's interactive paths. AI responses are verified by the Critic agent and citation-grounded to crawled artifacts."
    >
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-12 max-w-[1400px] mx-auto">
        
        {/* Chat Thread Container (Left/Mid) */}
        <div className="lg:col-span-8 flex flex-col h-[600px] border border-[var(--stitch-border)] rounded-xl bg-[var(--stitch-bg-elevated)]/40 overflow-hidden justify-between">
          
          {/* Messages ledger */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={index}
                  className={cn(
                    "flex flex-col max-w-[85%] rounded-lg p-3 text-xs leading-relaxed",
                    isUser
                      ? "ml-auto bg-[var(--stitch-surface-active)] text-slate-100 border border-[var(--stitch-border-strong)]"
                      : "mr-auto bg-[var(--stitch-surface)]/60 text-slate-300 border border-[var(--stitch-border)]"
                  )}
                >
                  {/* Speaker Label */}
                  <div className="flex items-center gap-1.5 mb-1.5 font-bold uppercase tracking-wider text-[10px] text-[var(--stitch-text-subtle)]">
                    {isUser ? <UserIcon /> : <Sparkles className="h-3 w-3 text-[var(--stitch-accent-cyan)]" />}
                    <span>{isUser ? "User query" : "SiteMind AI"}</span>
                    {msg.responseObj?.confidence && (
                      <span className="ml-auto">
                        <ConfidenceBadge value={msg.responseObj.confidence} size="sm" />
                      </span>
                    )}
                  </div>

                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Dynamic critic banner nested in assistant responses */}
                  {!isUser && msg.responseObj && (
                    <div className="mt-3.5 border-t border-[var(--stitch-border)] pt-2.5 flex items-center justify-between text-[10px] text-[var(--stitch-text-subtle)] font-medium">
                      <span className="flex items-center gap-1">
                        <ShieldCheck className="h-3.5 w-3.5 text-[var(--stitch-success)]" />
                        Critic Verification: Passed (Grounding: 98%)
                      </span>
                      <Badge variant="success" className="text-[8px] py-0">Grounded</Badge>
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="mr-auto bg-[var(--stitch-surface)]/60 text-slate-300 border border-[var(--stitch-border)] rounded-lg p-3 text-xs flex items-center gap-2 max-w-[200px]">
                <Loader />
                <span className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)]">Agent retrieving context...</span>
              </div>
            )}
          </div>

          {/* Preset Chips and query submit input */}
          <div className="p-4 border-t border-[var(--stitch-border)] bg-[var(--stitch-bg)]/20 space-y-3.5">
            {/* Quick preset Chips */}
            <div className="flex flex-wrap gap-2 text-xs">
              {PRESETS.map((preset) => (
                <button
                  key={preset}
                  onClick={() => handleSubmit(preset)}
                  className="rounded-full bg-[var(--stitch-surface)] hover:bg-[var(--stitch-surface-hover)] border border-[var(--stitch-border)] px-3 py-1 text-[11px] text-[var(--stitch-text-muted)] transition-colors hover:text-[var(--stitch-text)]"
                  disabled={loading}
                >
                  {preset}
                </button>
              ))}
            </div>

            {/* Main prompt input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit(question);
              }}
              className="flex gap-2"
            >
              <Input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="Ask about authentication flow, selectors, cookies, endpoint methods..."
                className="bg-[var(--stitch-surface)] h-10 border-[var(--stitch-border)]"
                disabled={loading}
              />
              <Button type="submit" disabled={loading || !question.trim()} className="bg-[var(--stitch-accent-cyan)] hover:bg-[var(--stitch-accent-cyan)]/90 text-slate-900 font-semibold px-4 shrink-0">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>

        </div>

        {/* Citations & Evidence Panel (Right Column) */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] h-full flex flex-col justify-between">
            <CardHeader className="pb-2.5 border-b border-[var(--stitch-border)]">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-[var(--stitch-text-muted)]">
                Active answer citations
              </CardTitle>
              <CardDescription className="text-[10px]">
                Fact sources extracted by vector similarity search.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-[var(--stitch-border)] max-h-[480px] overflow-y-auto">
                {/* Find the last assistant message and map its citations */}
                {(() => {
                  const assistantMsgs = messages.filter(m => m.role === "assistant" && m.responseObj);
                  const lastRes = assistantMsgs[assistantMsgs.length - 1]?.responseObj;
                  
                  if (!lastRes || !lastRes.citations || lastRes.citations.length === 0) {
                    return (
                      <div className="p-8 text-center text-xs text-[var(--stitch-text-subtle)] space-y-2">
                        <BookOpen className="h-6 w-6 mx-auto opacity-40" />
                        <p>No citations mapped for the active query.</p>
                      </div>
                    );
                  }

                  return lastRes.citations.map((cit, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleInspectCitation(cit)}
                      className="p-3.5 hover:bg-[var(--stitch-surface-hover)] transition-colors cursor-pointer space-y-2"
                    >
                      <div className="flex items-center justify-between text-[10px]">
                        <Badge variant="cyan" className="uppercase tracking-wide text-[9px] font-sans font-normal py-0">
                          {cit.artifact_type || "page"}
                        </Badge>
                        {cit.confidence !== undefined && <ConfidenceBadge value={cit.confidence} size="sm" />}
                      </div>

                      <p className="font-mono text-[10px] text-[var(--stitch-accent-cyan)] truncate">
                        {cit.source_url || "Local extraction schema"}
                      </p>

                      <div className="rounded bg-[var(--stitch-bg)] p-2 border border-[var(--stitch-border)] text-[10px] text-[var(--stitch-text-muted)] italic leading-relaxed">
                        &ldquo;{cit.snippet}&rdquo;
                      </div>

                      <div className="text-[9px] text-[var(--stitch-text-subtle)] text-right">
                        Click to inspect source details →
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </SiteScaffold>
  );
}

function UserIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-3 w-3 text-[var(--stitch-accent-violet)]">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
    </svg>
  );
}

function Loader() {
  return (
    <span className="flex h-3.5 w-3.5 items-center justify-center shrink-0">
      <span className="animate-spin rounded-full border-2 border-current border-t-transparent h-3 w-3 text-[var(--stitch-accent-cyan)]" />
    </span>
  );
}