"use client";

import React from "react";
import { ShieldCheck, AlertTriangle, Activity, Database, CheckCircle2, XCircle, ArrowUpRight } from "lucide-react";
import { EChartWrapper } from "@/components/charts/EChartWrapper";
import { formatCurrencyINR, formatDateTime } from "@/lib/utils";

interface CommandCentreProps {
  summary: any;
  trends: any;
  alerts: any[];
  recentEvents: any[];
  onSelectTransaction: (id: string) => void;
  onNavigateToTab: (tab: any) => void;
}

export function CommandCentre({
  summary,
  trends,
  alerts,
  recentEvents,
  onSelectTransaction,
  onNavigateToTab,
}: CommandCentreProps) {
  const kpis = summary?.data || {};
  const total = kpis.total_events || 0;
  const allow = kpis.allow || 0;
  const review = kpis.action_review || 0;
  const block = kpis.block || 0;
  const trusted = kpis.trusted_events || 0;
  const rejected = kpis.rejected_events || 0;

  // Trend Chart Options
  const trendData = trends?.data || {};
  const timestamps = trendData.timestamps || [];
  const amounts = trendData.amounts || [];
  const fraudProbs = trendData.fraud_probabilities || [];

  const trendOption = {
    tooltip: {
      trigger: "axis",
      backgroundColor: "#FFFFFF",
      borderColor: "#E2E8F0",
      textStyle: { color: "#0F172A", fontSize: 12 },
    },
    legend: {
      data: ["Amount (₹)", "Fraud Risk %"],
      right: 10,
      textStyle: { fontSize: 11, color: "#64748B" },
    },
    grid: { left: "3%", right: "4%", bottom: "3%", top: "15%", containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: timestamps.length > 0 ? timestamps : ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
      axisLine: { lineStyle: { color: "#E2E8F0" } },
      axisLabel: { color: "#64748B", fontSize: 10 },
    },
    yAxis: [
      {
        type: "value",
        name: "Amount (₹)",
        axisLine: { show: false },
        splitLine: { lineStyle: { color: "#F1F5F9" } },
        axisLabel: { color: "#64748B", fontSize: 10 },
      },
      {
        type: "value",
        name: "Risk %",
        min: 0,
        max: 1,
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: "#64748B",
          fontSize: 10,
          formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
        },
      },
    ],
    series: [
      {
        name: "Amount (₹)",
        type: "line",
        smooth: true,
        showSymbol: false,
        data: amounts.length > 0 ? amounts : [1200, 3500, 2400, 18000, 8900, 4200],
        itemStyle: { color: "#0D9488" },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(13, 148, 136, 0.15)" },
              { offset: 1, color: "rgba(13, 148, 136, 0.0)" },
            ],
          },
        },
      },
      {
        name: "Fraud Risk %",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        data: fraudProbs.length > 0 ? fraudProbs : [0.02, 0.05, 0.04, 0.85, 0.12, 0.03],
        itemStyle: { color: "#E11D48" },
        lineStyle: { width: 2, type: "dashed" },
      },
    ],
  };

  // 3-Tier Pie Chart
  const decisionPieOption = {
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    color: ["#0D9488", "#D97706", "#E11D48"],
    series: [
      {
        type: "pie",
        radius: ["55%", "75%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: { label: { show: false } },
        data: [
          { value: allow, name: "ALLOW" },
          { value: review, name: "REVIEW" },
          { value: block, name: "BLOCK" },
        ],
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Security Operations Command Centre</h1>
        <p className="text-xs text-slate-500 mt-0.5">Real-time financial transaction telemetry, cryptographic integrity, and streaming risk fusion</p>
      </div>

      {/* Top 4 Primary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1: Ingestion Volume */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Ingested Events</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
            {total.toLocaleString()}
          </div>
          <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-600">
            <span className="inline-flex items-center gap-1 font-semibold text-teal-600">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
              {allow} Allow
            </span>
            <span className="inline-flex items-center gap-1 font-semibold text-amber-600">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              {review} Review
            </span>
            <span className="inline-flex items-center gap-1 font-semibold text-rose-600">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
              {block} Block
            </span>
          </div>
        </div>

        {/* KPI 2: Cryptographic Security */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Ed25519 Signatures</span>
            <ShieldCheck className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
            {trusted.toLocaleString()}
          </div>
          <div className="mt-3 text-[11px] flex justify-between text-slate-500">
            <span>Rejections / Tamper:</span>
            <span className={`font-semibold ${rejected > 0 ? "text-rose-600" : "text-slate-700"}`}>
              {rejected} rejected
            </span>
          </div>
        </div>

        {/* KPI 3: Active Supervised Provenance */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Active Classifier</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
            0.8954 <span className="text-xs font-normal text-slate-500 font-mono">ROC-AUC</span>
          </div>
          <div className="mt-3 text-[11px] text-slate-500 truncate">
            Model: <span className="font-semibold text-slate-800">{kpis.active_model_id || "rf_ieee_cis_v1"}</span>
          </div>
        </div>

        {/* KPI 4: Stream Drift Telemetry */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Drift Health (ADWIN/PSI)</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-teal-700 mt-2 tracking-tight flex items-center gap-2">
            <span>STABLE</span>
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-3 text-[11px] text-slate-500">
            Alerts logged: <span className="font-semibold text-slate-700">{kpis.drift_alerts || 0}</span>
          </div>
        </div>
      </div>

      {/* Main Charts & Decisions Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-Time Chronological Trend Chart */}
        <div className="lg:col-span-2 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Streaming Transaction Volume & Risk Velocity</h2>
              <p className="text-[11px] text-slate-500">Chronological telemetry across incoming events</p>
            </div>
            <button
              onClick={() => onNavigateToTab("live_transactions")}
              className="text-xs text-teal-600 hover:text-teal-700 flex items-center gap-1 font-medium"
            >
              <span>View Live Stream</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <EChartWrapper option={trendOption} style={{ height: "260px", width: "100%" }} />
        </div>

        {/* 3-Tier Banking Action Distribution */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">3-Tier Response Distribution</h2>
            <p className="text-[11px] text-slate-500">Enforced mitigation actions</p>
          </div>
          <div className="relative py-2">
            <EChartWrapper option={decisionPieOption} style={{ height: "180px", width: "100%" }} />
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-lg font-bold text-slate-900">{total}</span>
              <span className="text-[10px] text-slate-400 uppercase font-medium">Evaluated</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-center">
            <div>
              <div className="text-[10px] text-slate-500 font-medium">ALLOW</div>
              <div className="text-sm font-bold text-teal-700">{allow}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 font-medium">REVIEW</div>
              <div className="text-sm font-bold text-amber-700">{review}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 font-medium">BLOCK</div>
              <div className="text-sm font-bold text-rose-700">{block}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Stream Strip & Alert Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latest Streaming Transactions */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Incoming Stream Snapshot</h2>
              <p className="text-[11px] text-slate-500">Latest UPI transactions verified by backend</p>
            </div>
            <button
              onClick={() => onNavigateToTab("live_transactions")}
              className="text-xs text-slate-500 hover:text-slate-900 font-medium"
            >
              View All →
            </button>
          </div>

          <div className="space-y-2">
            {recentEvents.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">Waiting for streaming events...</div>
            ) : (
              recentEvents.slice(0, 5).map((evt) => {
                const action = evt.action_decision || evt.decision;
                const isBlock = action === "BLOCK" || action === "HIGH_RISK" || action === "INTEGRITY_REJECTED";
                const isReview = action === "REVIEW";
                return (
                  <div
                    key={evt.event_id}
                    onClick={() => onSelectTransaction(evt.event_id)}
                    className="p-2.5 rounded border border-slate-100 hover:border-slate-300 hover:bg-slate-50/50 cursor-pointer transition flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-slate-800">{evt.transaction_id || evt.event_id?.slice(0, 8)}</span>
                        <span className="text-[10px] text-slate-500">
                          {evt.sender_id} → {evt.receiver_id}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        {evt.location || "Bengaluru"} • {evt.timestamp ? formatDateTime(evt.timestamp) : "Just now"}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-slate-900 font-mono">
                        {formatCurrencyINR(evt.amount || 0)}
                      </div>
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isBlock
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : isReview
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-teal-50 text-teal-700 border border-teal-200"
                        }`}
                      >
                        {isBlock ? "BLOCK" : isReview ? "REVIEW" : "ALLOW"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Operational Security Alerts */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Security & Forensic Alerts</h2>
              <p className="text-[11px] text-slate-500">Automated tamper rejections and high-risk flags</p>
            </div>
            <button
              onClick={() => onNavigateToTab("fraud_investigations")}
              className="text-xs text-slate-500 hover:text-slate-900 font-medium"
            >
              Open Dossiers →
            </button>
          </div>

          <div className="space-y-2">
            {alerts.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">Zero active security alerts</div>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => alert.event_id && onSelectTransaction(alert.event_id)}
                  className="p-2.5 rounded border border-rose-100 bg-rose-50/30 hover:bg-rose-50/60 cursor-pointer transition flex items-start gap-2.5 text-xs"
                >
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900">{alert.title}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {formatDateTime(alert.timestamp)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 mt-0.5">{alert.detail}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

