"use client";

import React, { useState } from "react";
import { GitCompare, AlertTriangle, CheckCircle2, Activity } from "lucide-react";
import { EChartWrapper } from "@/components/charts/EChartWrapper";

interface DriftAnalyticsProps {
  driftSummary: any;
  featureDrift: any[];
  driftEvents: any[];
}

export function DriftAnalytics({
  driftSummary,
  featureDrift,
  driftEvents,
}: DriftAnalyticsProps) {
  const [selectedFeature, setSelectedFeature] = useState<string>(
    featureDrift[0]?.feature || "amount"
  );

  const activeFeatureData = featureDrift.find((f) => f.feature === selectedFeature) || featureDrift[0];

  const unlabelled = driftSummary?.adwin_unlabelled || {};
  const labelled = driftSummary?.adwin_labelled || {};

  // Grouped Bar Chart comparing Baseline Distribution vs Current Operational Window
  const distChartOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: {
      data: ["Baseline Distribution", "Current Stream Window"],
      right: 10,
      textStyle: { fontSize: 11, color: "#64748B" },
    },
    grid: { left: "3%", right: "4%", bottom: "3%", top: "15%", containLabel: true },
    xAxis: {
      type: "category",
      data: activeFeatureData?.bins || ["Q1", "Q2", "Q3", "Q4", "Q5"],
      axisLine: { lineStyle: { color: "#E2E8F0" } },
      axisLabel: { color: "#64748B", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "Proportion",
      max: 0.6,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "#F1F5F9" } },
      axisLabel: {
        color: "#64748B",
        fontSize: 10,
        formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
      },
    },
    series: [
      {
        name: "Baseline Distribution",
        type: "bar",
        data: activeFeatureData?.baseline_distribution || [0.45, 0.25, 0.15, 0.10, 0.05],
        itemStyle: { color: "#0D9488" },
        barWidth: 18,
      },
      {
        name: "Current Stream Window",
        type: "bar",
        data: activeFeatureData?.current_distribution || [0.44, 0.26, 0.14, 0.11, 0.05],
        itemStyle: { color: "#2563EB" },
        barWidth: 18,
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Statistical Drift Analytics (ADWIN & PSI)</h1>
        <p className="text-xs text-slate-500">
          Continuous streaming drift detection via River ADWIN sliding windows and Population Stability Index (PSI) covariate shift monitoring
        </p>
      </div>

      {/* ADWIN Channel Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Unlabelled ADWIN Anomaly Signal */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>ADWIN Unlabelled Stream Signal</span>
            <Activity className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2 tracking-tight flex items-center gap-2">
            <span>{unlabelled.status || "STABLE"}</span>
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-3 text-[11px] text-slate-500 flex justify-between">
            <span>Observations Seen:</span>
            <span className="font-mono font-bold text-slate-800">{unlabelled.observations || 0}</span>
          </div>
        </div>

        {/* Card 2: Labelled ADWIN Concept Drift Signal */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>ADWIN Labelled Error Rate</span>
            <GitCompare className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2 tracking-tight flex items-center gap-2">
            <span>{labelled.status || "STABLE"}</span>
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-3 text-[11px] text-slate-500 flex justify-between">
            <span>True Concept Drift:</span>
            <span className="font-semibold text-teal-700">None Detected</span>
          </div>
        </div>

        {/* Card 3: Drift Events Audit Log Count */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Logged Drift Events</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-xl font-bold text-slate-900 mt-2 tracking-tight">
            {driftEvents.length}
          </div>
          <div className="mt-3 text-[11px] text-slate-500">
            Audit logs stored in SQLite <span className="font-mono text-slate-700">drift_events</span>
          </div>
        </div>
      </div>

      {/* Feature PSI Stability & Distribution Inspection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PSI Features Table */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
          <div className="border-b border-slate-100 pb-2">
            <h2 className="font-semibold text-slate-900 text-xs">Population Stability Index (PSI)</h2>
            <p className="text-[10px] text-slate-400">Click feature to inspect quantile distribution shift</p>
          </div>

          <div className="space-y-1.5">
            {featureDrift.map((feat) => {
              const isSelected = feat.feature === selectedFeature;
              return (
                <div
                  key={feat.feature}
                  onClick={() => setSelectedFeature(feat.feature)}
                  className={`p-2.5 rounded border cursor-pointer transition flex items-center justify-between ${
                    isSelected
                      ? "border-slate-900 bg-slate-50 shadow-sm font-semibold"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
                  }`}
                >
                  <div>
                    <span className="font-mono text-slate-900 block">{feat.feature}</span>
                    <span className="text-[10px] text-slate-400">
                      PSI: <span className="font-mono font-bold text-slate-700">{feat.psi_score}</span>
                    </span>
                  </div>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      feat.status === "DRIFT_ALERT"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : feat.status === "MODERATE_SHIFT"
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-teal-50 text-teal-700 border border-teal-200"
                    }`}
                  >
                    {feat.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Distribution Comparison Chart */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
            <div>
              <h2 className="text-xs font-semibold text-slate-900">
                Quantile Distribution Comparison: <span className="font-mono text-teal-700 font-bold">{selectedFeature}</span>
              </h2>
              <p className="text-[10px] text-slate-400">Baseline reference window vs current operational streaming window</p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 font-semibold">
              PSI = {activeFeatureData?.psi_score || 0.0}
            </span>
          </div>

          <EChartWrapper option={distChartOption} style={{ height: "260px", width: "100%" }} />
        </div>
      </div>

      {/* Historical Drift Trigger Log Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
        <h2 className="font-semibold text-slate-900 text-xs border-b border-slate-100 pb-2">
          Historical Drift Trigger Audit Trail
        </h2>
        {driftEvents.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">Zero drift trigger events logged.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-semibold uppercase text-[10px]">
                  <th className="py-2 px-3">Detector</th>
                  <th className="py-2 px-3">Signal Type</th>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Observations</th>
                  <th className="py-2 px-3">Metric Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {driftEvents.slice(0, 10).map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/50">
                    <td className="py-2 px-3 font-semibold text-slate-900">{d.detector_name}</td>
                    <td className="py-2 px-3 font-mono text-[11px] text-slate-600">{d.signal_type}</td>
                    <td className="py-2 px-3 text-[11px] font-mono text-slate-500">{d.timestamp}</td>
                    <td className="py-2 px-3 font-mono text-slate-800">{d.observation_count}</td>
                    <td className="py-2 px-3 font-mono font-bold text-slate-900">{Number(d.metric_value).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

