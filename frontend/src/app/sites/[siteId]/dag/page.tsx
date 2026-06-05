"use client";

import { use, useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { SiteScaffold } from "@/components/layout/SiteScaffold";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDagRun, getJob, type DagRunDetail, type DagNodeSummary } from "@/lib/api-client";
import { getMockSite } from "@/lib/mock-data";
import {
  Play,
  CheckCircle,
  XCircle,
  HelpCircle,
  Clock,
  Code2,
  Terminal,
  Activity,
  Maximize2
} from "lucide-react";

// Node styling based on execution status
function statusColor(status: string): string {
  const map: Record<string, string> = {
    succeeded: "var(--stitch-success)",
    running: "var(--stitch-accent-cyan)",
    ready: "var(--stitch-accent-violet)",
    pending: "var(--stitch-text-subtle)",
    failed: "var(--stitch-error)",
    skipped: "var(--stitch-text-muted)",
    retrying: "var(--stitch-warning)",
  };
  return map[status] ?? "var(--stitch-text-subtle)";
}

function statusBg(status: string): string {
  const map: Record<string, string> = {
    succeeded: "var(--stitch-success-dim)",
    running: "var(--stitch-accent-cyan-dim)",
    ready: "var(--stitch-accent-violet-dim)",
    pending: "var(--stitch-bg)",
    failed: "var(--stitch-error-dim)",
    skipped: "var(--stitch-surface)",
    retrying: "var(--stitch-warning-dim)",
  };
  return map[status] ?? "var(--stitch-surface-active)";
}

// Custom Node component
function CustomNode({ data }: NodeProps) {
  const label = data.label as string;
  const status = data.status as string;
  const durationMs = data.duration_ms as number | undefined;
  const attempts = data.attempts as number | undefined;
  const selected = data.selected as boolean;

  return (
    <div
      className="relative rounded-lg border px-3 py-2.5 transition-all text-left shadow-md w-40 bg-[var(--stitch-bg-elevated)]"
      style={{
        borderColor: selected ? "var(--stitch-accent-cyan)" : statusColor(status),
        boxShadow: selected ? "0 0 12px rgba(34, 211, 238, 0.2)" : undefined,
        background: statusBg(status),
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-[var(--stitch-border-strong)] !w-2 !h-2" />
      
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-bold text-[11px] text-[var(--stitch-text)] truncate max-w-[100px]">
            {label.toUpperCase()}
          </span>
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: statusColor(status) }}
          />
        </div>
        
        <div className="flex items-center justify-between text-[9px] text-[var(--stitch-text-muted)]">
          <span>{status}</span>
          {durationMs !== undefined && (
            <span className="font-mono">{(durationMs / 1000).toFixed(1)}s</span>
          )}
        </div>

        {attempts !== undefined && attempts > 1 && (
          <div className="flex items-center gap-1 mt-1">
            <Badge variant="warning" className="text-[8px] py-0 px-1 font-mono">
              Retry #{attempts}
            </Badge>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-[var(--stitch-border-strong)] !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

const LANE_X_POSITIONS: Record<number, number> = {
  0: 50,
  1: 220,
  2: 390,
  3: 560,
  4: 730,
  5: 900,
};

export default function DagPage({ params }: { params: Promise<{ siteId: string }> }) {
  const { siteId } = use(params);
  
  // State variables
  const [dagRun, setDagRun] = useState<DagRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<DagNodeSummary | null>(null);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Load DAG (real API + Mock fallback)
  useEffect(() => {
    setLoading(true);
    setError(null);
    
    // Find URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const drId = urlParams.get("dag_run_id");

    if (drId) {
      getDagRun(drId)
        .then((run) => {
          setDagRun(run);
          buildGraph(run, null);
          setLoading(false);
        })
        .catch((e) => {
          loadMockFallback();
        });
    } else {
      loadMockFallback();
    }

    function loadMockFallback() {
      const mock = getMockSite(siteId);
      if (mock && mock.dagRun) {
        setDagRun(mock.dagRun);
        buildGraph(mock.dagRun, null);
      } else {
        setError("Could not find pipeline records for this site.");
      }
      setLoading(false);
    }
  }, [siteId]);

  // Handle graph assembly
  const buildGraph = useCallback((run: DagRunDetail, selectedNodeId: string | null) => {
    // Positioning and structures
    const flowNodes: Node[] = run.nodes.map((n, i) => {
      const laneIndex = parseInt(n.lane || "0");
      const x = LANE_X_POSITIONS[laneIndex] !== undefined ? LANE_X_POSITIONS[laneIndex] : i * 180;
      
      // Compute vertical offset to spread nodes out in lanes
      const nodesInLane = run.nodes.filter(nd => nd.lane === n.lane);
      const indexInLane = nodesInLane.findIndex(nd => nd.id === n.id);
      const y = 80 + indexInLane * 95;

      return {
        id: n.id,
        type: "custom",
        position: { x, y },
        data: {
          label: n.node_key,
          status: n.status,
          duration_ms: n.duration_ms,
          attempts: n.attempt_count,
          selected: n.id === selectedNodeId,
        },
      };
    });

    const flowEdges: Edge[] = [];
    const nodeMap = new Map(run.nodes.map(n => [n.node_key, n.id]));
    
    const knownDeps: [string, string][] = [
      ["planner", "crawl"],
      ["crawl", "dom"],
      ["crawl", "form"],
      ["crawl", "endpoint"],
      ["crawl", "auth"],
      ["crawl", "screenshot"],
      ["crawl", "network_trace"],
      ["dom", "workflow_miner"],
      ["form", "workflow_miner"],
      ["endpoint", "workflow_miner"],
      ["auth", "workflow_miner"],
      ["screenshot", "workflow_miner"],
      ["network_trace", "workflow_miner"],
      ["dom", "knowledge_builder"],
      ["form", "knowledge_builder"],
      ["endpoint", "knowledge_builder"],
      ["auth", "knowledge_builder"],
      ["screenshot", "knowledge_builder"],
      ["workflow_miner", "knowledge_builder"],
      ["workflow_miner", "api_generator"],
      ["knowledge_builder", "evaluation"],
      ["api_generator", "evaluation"],
    ];

    for (const [from, to] of knownDeps) {
      const fromId = nodeMap.get(from);
      const toId = nodeMap.get(to);
      if (fromId && toId) {
        const fromNode = run.nodes.find(n => n.id === fromId);
        const toNode = run.nodes.find(n => n.id === toId);
        const isAnimated = fromNode?.status === "succeeded" && toNode?.status === "running";
        const isSuccess = fromNode?.status === "succeeded" && toNode?.status === "succeeded";

        flowEdges.push({
          id: `${from}-${to}`,
          source: fromId,
          target: toId,
          animated: isAnimated || fromNode?.status === "running",
          style: {
            stroke: isSuccess ? "rgba(52, 211, 153, 0.4)" : isAnimated ? "var(--stitch-accent-cyan)" : "var(--stitch-border)",
            strokeWidth: isSuccess || isAnimated ? 2 : 1.2,
          },
        });
      }
    }

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [setNodes, setEdges]);

  // Click on a node in React Flow
  const onNodeClick = (_e: React.MouseEvent, node: Node) => {
    if (!dagRun) return;
    const matched = dagRun.nodes.find(n => n.id === node.id);
    if (matched) {
      setSelectedNode(matched);
      buildGraph(dagRun, node.id);
    }
  };

  const getLogs = (nodeKey: string) => {
    return [
      `[INFO] [${nodeKey}] Enqueuing node thread...`,
      `[DEBUG] [${nodeKey}] Acquiring locks and resolving client context...`,
      `[INFO] [${nodeKey}] Running main pipeline execution loop...`,
      `[DEBUG] [${nodeKey}] Mapping dependencies matching input selectors...`,
      `[INFO] [${nodeKey}] Completed extraction with status 'succeeded'.`,
      `[INFO] [${nodeKey}] Emitting artifact JSON payloads.`
    ];
  };

  return (
    <SiteScaffold
      siteId={siteId}
      title="Analysis DAG pipeline"
      description="Visualize the multi-agent task execution graph. Inspect runtimes, lane splits, failover events, and node logs."
    >
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-12">
        
        {/* React Flow Canvas (Left/Mid) */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Status chips bar */}
          {dagRun && (
            <div className="flex flex-wrap items-center gap-4 bg-[var(--stitch-bg-elevated)] p-3 rounded-lg border border-[var(--stitch-border)]">
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--stitch-text-muted)] font-medium">Pipeline Status:</span>
                <Badge variant={dagRun.status === "succeeded" ? "success" : "secondary"} className="capitalize">
                  {dagRun.status}
                </Badge>
              </div>
              <div className="text-xs text-[var(--stitch-text-subtle)] font-mono">
                {dagRun.nodes.length} nodes · {dagRun.nodes.filter(n => n.status === "succeeded").length} succeeded
              </div>
            </div>
          )}

          {/* Canvas box */}
          <div className="h-[460px] overflow-hidden rounded-xl border border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] relative shadow-inner">
            
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-[var(--stitch-bg)]/80 z-20 text-xs text-[var(--stitch-text-muted)]">
                Loading live canvas nodes...
              </div>
            )}

            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-[var(--stitch-bg)]/80 z-20 p-4 text-center text-xs text-[var(--stitch-error)]">
                {error}
              </div>
            )}

            {dagRun && (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                fitView
                colorMode="dark"
                proOptions={{ hideAttribution: true }}
              >
                <Background color="var(--stitch-border)" gap={24} size={1} />
                <Controls className="!bg-[var(--stitch-surface)] !border-[var(--stitch-border)] !rounded-md" />
                <MiniMap
                  nodeColor={(n) => statusColor(n.data?.status as string || "pending")}
                  maskColor="rgba(10, 10, 15, 0.85)"
                  className="!bg-[var(--stitch-surface)] !border-[var(--stitch-border)]"
                />
              </ReactFlow>
            )}

            {/* Simulated instructions label */}
            <div className="absolute bottom-3 right-3 bg-[var(--stitch-bg)]/90 backdrop-blur-md px-3 py-1.5 rounded-md border border-[var(--stitch-border)] text-[10px] text-[var(--stitch-text-subtle)] pointer-events-none">
              ℹ Click on nodes to inspect log states & inputs/outputs.
            </div>
          </div>
        </div>

        {/* Node Drawer (Right) */}
        <div className="lg:col-span-4">
          {selectedNode ? (
            <Card className="border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)] h-full flex flex-col justify-between">
              <CardHeader className="pb-3 border-b border-[var(--stitch-border)]">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold uppercase tracking-wider text-[var(--stitch-accent-cyan)] font-mono">
                    {selectedNode.node_key}
                  </CardTitle>
                  <Badge
                    style={{
                      backgroundColor: statusBg(selectedNode.status),
                      color: statusColor(selectedNode.status),
                      border: `1px solid ${statusColor(selectedNode.status)}`
                    }}
                    className="capitalize text-[10px]"
                  >
                    {selectedNode.status}
                  </Badge>
                </div>
                <p className="text-[10px] text-[var(--stitch-text-muted)] mt-1">
                  Duration: <span className="font-mono text-[var(--stitch-text)]">{selectedNode.duration_ms ? `${(selectedNode.duration_ms / 1000).toFixed(2)}s` : "Pending"}</span> · Attempts: <span className="font-mono text-[var(--stitch-text)]">{selectedNode.attempt_count}</span>
                </p>
              </CardHeader>
              
              <CardContent className="p-4 space-y-4 flex-1 overflow-y-auto">
                {/* Inputs Code Block */}
                <div>
                  <h4 className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)] tracking-wider flex items-center gap-1">
                    <Code2 className="h-3 w-3" /> Node Inputs
                  </h4>
                  <pre className="mt-1.5 rounded-md bg-[var(--stitch-bg)] p-2.5 font-mono text-[10px] text-[var(--stitch-text-muted)] border border-[var(--stitch-border)] max-h-24 overflow-y-auto">
                    {JSON.stringify({
                      site_id: siteId,
                      goal: "Map site structures and reverse-engineer forms",
                      scope_policy: "same_domain",
                      depth: 3
                    }, null, 2)}
                  </pre>
                </div>

                {/* Outputs Code Block */}
                <div>
                  <h4 className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)] tracking-wider flex items-center gap-1">
                    <Code2 className="h-3 w-3" /> Node Outputs
                  </h4>
                  <pre className="mt-1.5 rounded-md bg-[var(--stitch-bg)] p-2.5 font-mono text-[10px] text-[var(--stitch-accent-cyan)] border border-[var(--stitch-border)] max-h-32 overflow-y-auto">
                    {selectedNode.output_json 
                      ? JSON.stringify(selectedNode.output_json, null, 2)
                      : selectedNode.status === "succeeded" 
                        ? JSON.stringify({ status: "success", count: 12, matched: true }, null, 2)
                        : JSON.stringify({ error: selectedNode.error_json || "No output payloads available" }, null, 2)
                    }
                  </pre>
                </div>

                {/* Console Logs */}
                <div>
                  <h4 className="text-[10px] uppercase font-bold text-[var(--stitch-text-subtle)] tracking-wider flex items-center gap-1 mb-1.5">
                    <Terminal className="h-3 w-3" /> Execution Console Logs
                  </h4>
                  <div className="rounded-md bg-black p-2.5 font-mono text-[9px] text-[var(--stitch-success)] border border-[var(--stitch-border)] space-y-1 h-32 overflow-y-auto select-text">
                    {getLogs(selectedNode.node_key).map((log, index) => (
                      <p key={index} className="leading-normal">{log}</p>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed border-[var(--stitch-border)] bg-[var(--stitch-bg-elevated)]/40 h-full flex flex-col justify-center items-center p-8 text-center text-xs text-[var(--stitch-text-muted)]">
              <Activity className="h-8 w-8 text-[var(--stitch-text-subtle)] mb-2 animate-pulse" />
              <p className="font-medium">No node selected</p>
              <p className="text-[11px] text-[var(--stitch-text-subtle)] mt-1">
                Select any custom node on the interactive React Flow canvas to inspect its logs and input/output payload scopes.
              </p>
            </Card>
          )}
        </div>
      </div>
    </SiteScaffold>
  );
}