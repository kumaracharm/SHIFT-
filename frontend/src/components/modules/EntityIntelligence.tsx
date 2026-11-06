"use client";

import React, { useState } from "react";
import { Network, User, Smartphone, MapPin, AlertOctagon, ArrowRight } from "lucide-react";
import { EChartWrapper } from "@/components/charts/EChartWrapper";
import { formatCurrencyINR } from "@/lib/utils";

interface EntityIntelligenceProps {
  graphData: {
    nodes: any[];
    links: any[];
    categories: any[];
  };
  onSelectEntity?: (entityId: string) => void;
}

export function EntityIntelligence({ graphData }: EntityIntelligenceProps) {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

  const categories = graphData.categories || [
    { name: "Sender User" },
    { name: "Merchant" },
    { name: "Device" },
    { name: "Location" },
    { name: "Mule Ring" },
  ];

  const graphOption = {
    tooltip: {
      trigger: "item",
      formatter: (params: any) => {
        if (params.dataType === "node") {
          return `<div style="font-size: 11px;">
            <b>${params.data.name}</b><br/>
            Category: ${categories[params.data.category]?.name || "Entity"}<br/>
            Risk Tier: ${params.data.risk_tier || "NORMAL"}
          </div>`;
        }
        if (params.dataType === "edge") {
          return `<div style="font-size: 11px;">
            Transfer: <b>${params.data.source} → ${params.data.target}</b><br/>
            Amount: ${params.data.label || ""}
          </div>`;
        }
        return "";
      },
    },
    legend: [
      {
        data: categories.map((c) => c.name),
        textStyle: { fontSize: 11, color: "#64748B" },
        top: 5,
        right: 10,
      },
    ],
    color: ["#0F172A", "#2563EB", "#64748B", "#D97706", "#E11D48"],
    series: [
      {
        type: "graph",
        layout: "force",
        data: graphData.nodes || [],
        links: graphData.links || [],
        categories: categories,
        roam: true,
        label: {
          show: true,
          position: "right",
          formatter: "{b}",
          fontSize: 10,
          color: "#334155",
        },
        force: {
          repulsion: 220,
          edgeLength: [60, 120],
          gravity: 0.1,
        },
        lineStyle: {
          curveness: 0.15,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 4 },
        },
      },
    ],
  };

  const onEvents = {
    click: (params: any) => {
      if (params.dataType === "node") {
        setSelectedNode(params.data);
      }
    },
  };

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">Entity Intelligence & Mule Ring Graph</h1>
          <p className="text-xs text-slate-500">
            Interactive relational network analyzing counterparty relationships, shared device fingerprints, and mule ring clusters
          </p>
        </div>
        <div className="text-xs text-slate-500 font-mono">
          {graphData.nodes?.length || 0} nodes • {graphData.links?.length || 0} edges
        </div>
      </div>

      {/* Main Grid: Interactive Network Left, Entity Profile Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Graph Container */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
            <span className="font-semibold text-slate-900 text-xs flex items-center gap-1.5">
              <Network className="w-4 h-4 text-slate-600" />
              <span>Multi-Hop Entity Correlation Topology</span>
            </span>
            <span className="text-[10px] text-slate-400">Click any node to inspect profile</span>
          </div>

          <EChartWrapper
            option={graphOption}
            style={{ height: "540px", width: "100%" }}
            onEvents={onEvents}
          />
        </div>

        {/* Entity Dossier / Inspection Sidebar */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4 text-xs">
          <h2 className="font-semibold text-slate-900 text-xs border-b border-slate-100 pb-2">
            Entity Identity Dossier
          </h2>

          {selectedNode ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Node Identifier</span>
                <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
                  {selectedNode.name}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800">
                    {categories[selectedNode.category]?.name || "Entity"}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      selectedNode.risk_tier === "CRITICAL"
                        ? "bg-rose-100 text-rose-800"
                        : selectedNode.risk_tier === "HIGH"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-teal-100 text-teal-800"
                    }`}
                  >
                    Risk: {selectedNode.risk_tier || "LOW"}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-slate-700">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Accumulated Volume:</span>
                  <span className="font-mono font-bold text-slate-900">
                    {formatCurrencyINR(selectedNode.value || 0)}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Topology Degree:</span>
                  <span className="font-mono text-slate-800 font-semibold">
                    {graphData.links.filter(
                      (l) => l.source === selectedNode.id || l.target === selectedNode.id
                    ).length}{" "}
                    connections
                  </span>
                </div>
              </div>

              {selectedNode.category === 4 && (
                <div className="p-3 rounded bg-rose-50 border border-rose-200 text-rose-800 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-xs">
                    <AlertOctagon className="w-4 h-4 text-rose-600" />
                    <span>Mule Ring Cluster Alert</span>
                  </div>
                  <p className="text-[11px] text-rose-700">
                    This node exhibits structural characteristics of a fund dispersion aggregator. Immediate automated quarantine recommended.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="py-16 text-center text-slate-400 text-xs">
              Click on any node in the graph (e.g. USER_xxxx, MERCHANT_xxx, DEV-xxx) to inspect counterparty metrics and risk scoring.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

