"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

/**
 * Conceptual Claim Map — High-end topological visualization.
 * Clusters claims by narrative context into an intelligence constellation.
 */

interface GraphNode {
  id: string;
  label: string;
  verdict: string | null;
  type?: "claim" | "source" | "topic";
  group?: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  similarity_score: number;
  type?: string;
}

export default function GraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [data, setData] = useState<{ nodes: GraphNode[]; links: GraphEdge[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchGraph() {
      try {
        const res = await fetch("http://localhost:8000/v1/public/dashboard/graph");
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Failed to fetch graph:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchGraph();
  }, []);

  useEffect(() => {
    if (!svgRef.current || !data?.nodes?.length) return;

    import("d3").then((d3) => {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();

      const width = svgRef.current!.clientWidth;
      const height = svgRef.current!.clientHeight;

      // ── DEFINITIONS (Glow Filters) ──────────────────────────────────
      const defs = svg.append("defs");
      
      const createGlow = (id: string, color: string) => {
        const filter = defs.append("filter").attr("id", id).attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
        filter.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "blur");
        filter.append("feFlood").attr("flood-color", color).attr("flood-opacity", "0.6").attr("result", "color");
        filter.append("feComposite").attr("in", "color").attr("in2", "blur").attr("operator", "in").attr("result", "glow");
        const merge = filter.append("feMerge");
        merge.append("feMergeNode").attr("in", "glow");
        merge.append("feMergeNode").attr("in", "SourceGraphic");
      };

      createGlow("glow-true", "#34d399");
      createGlow("glow-false", "#f87171");
      createGlow("glow-misleading", "#fbbf24");
      createGlow("glow-topic", "#4fd1c5");

      // ── SIMULATION ──────────────────────────────────────────────────
      const simulation = d3
        .forceSimulation(data.nodes as d3.SimulationNodeDatum[])
        .force("link", d3.forceLink(data.links).id((d: any) => d.id).distance((d: any) => d.type === 'topology' ? 80 : 160))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide(70));

      // ── RENDERING ───────────────────────────────────────────────────
      const link = svg
        .append("g")
        .selectAll("line")
        .data(data.links)
        .enter()
        .append("line")
        .attr("stroke", (d: any) => d.type === 'topology' ? "rgba(79, 209, 197, 0.15)" : "rgba(255,255,255,0.06)")
        .attr("stroke-width", (d: any) => d.type === 'topology' ? 1.5 : 1)
        .attr("stroke-dasharray", (d: any) => d.type === 'topology' ? "4 2" : "none");

      const node = svg
        .append("g")
        .selectAll("g")
        .data(data.nodes)
        .enter()
        .append("g")
        .style("cursor", "pointer")
        .on("click", (_: any, d: GraphNode) => setSelected(d));

      // Circular nodes
      node
        .append("circle")
        .attr("r", (d: any) => d.type === "topic" ? 10 : d.type === "claim" ? 22 : 8)
        .attr("fill", (d: any) => {
          if (d.type === "topic") return "rgba(79, 209, 197, 0.2)";
          if (d.type === "source") return "rgba(148, 163, 184, 0.1)";
          switch (d.verdict) {
            case "TRUE": return "#34d399";
            case "FALSE": return "#f87171";
            case "MISLEADING": return "#fbbf24";
            default: return "rgba(255,255,255,0.05)";
          }
        })
        .attr("stroke", (d: any) => {
          if (d.type === "topic") return "#4fd1c5";
          if (d.type === "source") return "rgba(148, 163, 184, 0.3)";
          return "rgba(255,255,255,0.2)";
        })
        .attr("stroke-width", (d: any) => d.type === "topic" ? 2 : 1)
        .attr("filter", (d: any) => {
          if (d.type === "topic") return "url(#glow-topic)";
          if (d.verdict === "TRUE") return "url(#glow-true)";
          if (d.verdict === "FALSE") return "url(#glow-false)";
          if (d.verdict === "MISLEADING") return "url(#glow-misleading)";
          return "none";
        });

      // Labels
      node
        .append("text")
        .text((d: GraphNode) => d.label.length > 18 ? d.label.slice(0, 18) + "..." : d.label)
        .attr("text-anchor", "middle")
        .attr("dy", (d: any) => d.type === "claim" ? 42 : d.type === "topic" ? -20 : 25)
        .attr("fill", (d: any) => d.type === "topic" ? "#4fd1c5" : d.type === "claim" ? "#f1f5f9" : "#94a3b8")
        .attr("font-size", (d: any) => d.type === "topic" ? "12px" : "10px")
        .attr("font-weight", (d: any) => d.type === "topic" ? "bold" : "normal")
        .style("text-shadow", "0 0 10px rgba(0,0,0,0.8)");

      simulation.on("tick", () => {
        link
          .attr("x1", (d: any) => d.source.x)
          .attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x)
          .attr("y2", (d: any) => d.target.y);

        node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
      });

      // Drag behaviour
      const drag = d3.drag<SVGGElement, any>()
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
  }, [data]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8 relative">
        <div className="flex items-center gap-3 mb-1">
           <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></div>
           <span className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Forensic Topology</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Conceptual Claim Map</h1>
        <p className="mt-1 text-gray-400">
           Clustering verified narratives into topic constellations to detect coordinated campaign patterns.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3 glass-card overflow-hidden relative" style={{ height: 700 }}>
          {/* Subtle Grid Background */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
               style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
          
          {loading ? (
             <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-medium animate-pulse">
                Calibrating Narrative Nodes...
             </div>
          ) : (
             <svg ref={svgRef} className="w-full h-full relative z-10" />
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">Intelligence Node</h2>
            {selected ? (
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Entity</span>
                  <p className="text-sm font-semibold mt-1 text-gray-100 uppercase">{selected.type}</p>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Payload</span>
                  <p className="text-sm font-medium mt-1 leading-snug">{selected.label}</p>
                </div>
                {selected.verdict && (
                  <div>
                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Forensic Status</span>
                    <div className="mt-2">
                       <span className={`px-2.5 py-1 rounded text-[10px] font-bold tracking-wider border ${
                          selected.verdict === 'TRUE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                          selected.verdict === 'FALSE' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
                          'bg-yellow-500/10 text-yellow-500 border-yellow-500/30'
                       }`}>
                          {selected.verdict}
                       </span>
                    </div>
                  </div>
                )}
                <div className="pt-4 mt-4 border-t border-gray-800">
                   <Link href={selected.type === 'claim' ? `/receipt/${selected.id.replace('a_', '')}` : '#'}
                         className="w-full inline-flex items-center justify-center bg-gray-800 hover:bg-gray-700 py-2 rounded text-xs font-semibold transition-colors">
                      Open Audit Receipt
                   </Link>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600 italic">Select a node in the constellation to view its forensic metadata.</p>
            )}
          </div>

          <div className="glass-card p-5">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">Map Legend</h2>
            <div className="space-y-3">
               <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(79,209,197,0.8)]"></div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Narrative Topic</span>
               </div>
               <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Verified Truth</span>
               </div>
               <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.8)]"></div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Coordinated Falsehood</span>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
