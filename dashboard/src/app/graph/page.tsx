/**
 * Graph — Interactive claim relationship visualisation using D3.js.
 */
"use client";

import { useEffect, useRef, useState } from "react";

interface GraphNode {
  id: string;
  label: string;
  verdict: string | null;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  similarity_score: number;
}

// ── Static demo data ────────────────────────────────────────────────────────
const DEMO_NODES: GraphNode[] = [
  { id: "c1", label: "Free electricity announced", verdict: "FALSE" },
  { id: "c2", label: "Coffee prevents cancer", verdict: "MISLEADING" },
  { id: "c3", label: "Interest rate unchanged", verdict: "TRUE" },
  { id: "c4", label: "Flood photo misattributed", verdict: "FALSE" },
  { id: "c5", label: "Deepfake video confirmed", verdict: "TRUE" },
  { id: "c6", label: "Crypto celebrity endorsement", verdict: "FALSE" },
  { id: "c7", label: "Earthquake prediction hoax", verdict: "FALSE" },
  { id: "c8", label: "Vaccine efficacy 90%", verdict: "TRUE" },
  { id: "c9", label: "Election fraud claims", verdict: "MISLEADING" },
  { id: "c10", label: "Climate data manipulated", verdict: "FALSE" },
];

const DEMO_EDGES: GraphEdge[] = [
  { source: "c1", target: "c4", similarity_score: 0.72 },
  { source: "c1", target: "c6", similarity_score: 0.65 },
  { source: "c2", target: "c8", similarity_score: 0.81 },
  { source: "c4", target: "c7", similarity_score: 0.58 },
  { source: "c5", target: "c9", similarity_score: 0.44 },
  { source: "c6", target: "c7", similarity_score: 0.73 },
  { source: "c3", target: "c8", similarity_score: 0.35 },
  { source: "c9", target: "c10", similarity_score: 0.67 },
  { source: "c1", target: "c9", similarity_score: 0.51 },
];

export default function GraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    // Dynamically import D3 to avoid SSR issues
    import("d3").then((d3) => {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();

      const width = svgRef.current!.clientWidth;
      const height = svgRef.current!.clientHeight;

      const verdictColor = (v: string | null) => {
        switch (v) {
          case "TRUE": return "#34d399";
          case "FALSE": return "#f87171";
          case "MISLEADING": return "#fbbf24";
          default: return "#94a3b8";
        }
      };

      const simulation = d3
        .forceSimulation(DEMO_NODES as d3.SimulationNodeDatum[])
        .force("link", d3.forceLink(DEMO_EDGES).id((d: any) => d.id).distance(120))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide(40));

      // Edges
      const link = svg
        .append("g")
        .selectAll("line")
        .data(DEMO_EDGES)
        .enter()
        .append("line")
        .attr("stroke", "rgba(255,255,255,0.08)")
        .attr("stroke-width", (d: any) => d.similarity_score * 3);

      // Nodes
      const node = svg
        .append("g")
        .selectAll("g")
        .data(DEMO_NODES)
        .enter()
        .append("g")
        .style("cursor", "pointer")
        .on("click", (_: any, d: GraphNode) => setSelected(d));

      node
        .append("circle")
        .attr("r", 18)
        .attr("fill", (d: GraphNode) => verdictColor(d.verdict))
        .attr("opacity", 0.8)
        .attr("stroke", (d: GraphNode) => verdictColor(d.verdict))
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 0.3);

      node
        .append("text")
        .text((d: GraphNode) => d.label.slice(0, 12))
        .attr("text-anchor", "middle")
        .attr("dy", 32)
        .attr("fill", "#94a3b8")
        .attr("font-size", "10px");

      simulation.on("tick", () => {
        link
          .attr("x1", (d: any) => d.source.x)
          .attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x)
          .attr("y2", (d: any) => d.target.y);

        node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
      });

      // Drag behaviour
      const drag = d3.drag<SVGGElement, GraphNode>()
        .on("start", (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        });

      node.call(drag as any);
    });
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Claim Graph</h1>
        <p className="mt-1 text-gray-500">
          Explore claim relationships and detect coordinated campaigns
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Graph canvas */}
        <div className="lg:col-span-3 glass-card overflow-hidden" style={{ height: 600 }}>
          <svg ref={svgRef} className="w-full h-full" />
        </div>

        {/* Detail panel */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Node Details
          </h3>
          {selected ? (
            <div className="space-y-3">
              <div>
                <span className="text-xs text-gray-500">Claim</span>
                <p className="text-sm font-medium mt-0.5">{selected.label}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">Verdict</span>
                <p className="mt-0.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      selected.verdict === "TRUE" ? "badge-true" :
                      selected.verdict === "FALSE" ? "badge-false" :
                      selected.verdict === "MISLEADING" ? "badge-misleading" :
                      "badge-unverifiable"
                    }`}
                  >
                    {selected.verdict || "UNVERIFIABLE"}
                  </span>
                </p>
              </div>
              <div>
                <span className="text-xs text-gray-500">ID</span>
                <p className="text-sm font-mono text-gray-400 mt-0.5">
                  {selected.id}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-600">
              Click a node to view details
            </p>
          )}

          <div className="mt-6 pt-4 border-t border-gray-800/60">
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Legend</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-400" />
                <span className="text-gray-400">True</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <span className="text-gray-400">False</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <span className="text-gray-400">Misleading</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-400" />
                <span className="text-gray-400">Unverifiable</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
