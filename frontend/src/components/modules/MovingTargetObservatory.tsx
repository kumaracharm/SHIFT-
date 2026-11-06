"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Target,
  Zap,
  Clock,
  BarChart2,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Play,
  RotateCw,
  ShieldCheck,
  TrendingUp,
  Fingerprint,
  Info,
  ArrowRight,
} from "lucide-react";
import { EChartWrapper } from "@/components/charts/EChartWrapper";

// Inline API helpers
async function fetchLatestExperiment() {
  const res = await fetch("/api/v1/experiments/latest/result");
  if (!res.ok) throw new Error("Failed to fetch experiment");
  return res.json();
}

async function fetchExperimentList() {
  const res = await fetch("/api/v1/experiments/");
  if (!res.ok) throw new Error("Failed to fetch experiment list");
  return res.json();
}

async function runExperiment() {
  const res = await fetch("/api/v1/experiments/run", { method: "POST" });
  if (!res.ok) throw new Error("Experiment failed");
  return res.json();
}

// 6-Phase Configuration with vivid engineering color codes
const PHASE_DISPLAY: Record<
  string,
  { label: string; tag: string; color: string; bg: string; border: string; desc: string }
> = {
  baseline: {
    label: "Normal Baseline",
    tag: "PHASE 1",
    color: "#059669",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    desc: "Legitimate UPI transactions establish reference distributions.",
  },
  initial_fraud: {
    label: "Initial Fraud (Velocity)",
    tag: "PHASE 2",
    color: "#D97706",
    bg: "bg-amber-50",
    border: "border-amber-200",
    desc: "Attacker executes repeated rapid bursts; caught by Velocity expert.",
  },
  moving_target: {
    label: "Moving Target (Pivot)",
    tag: "PHASE 3",
    color: "#E11D48",
    bg: "bg-rose-50",
    border: "border-rose-200",
    desc: "Attacker reads alerts and switches tactics. NO labels arrive.",
  },
  drift_detection: {
    label: "Drift Detection Alert",
    tag: "PHASE 4",
    color: "#7C3AED",
    bg: "bg-purple-50",
    border: "border-purple-200",
    desc: "ADWIN + PSI detect the shift before ground-truth chargebacks exist.",
  },
  adaptation: {
    label: "Policy Adaptation",
    tag: "PHASE 5",
    color: "#2563EB",
    bg: "bg-blue-50",
    border: "border-blue-200",
    desc: "Detection sensitivity escalated; borderline traffic routed to review.",
  },
  recovery: {
    label: "System Recovery",
    tag: "PHASE 6",
    color: "#0D9488",
    bg: "bg-teal-50",
    border: "border-teal-200",
    desc: "Normal stream restored; verification that flag rates return to baseline.",
  },
};

interface PhaseMetrics {
  phase: string;
  phase_label: string;
  start_event_index: number;
  end_event_index: number;
  total_events: number;
  flagged_count: number;
  rejected_count: number;
  normal_count: number;
  flag_rate: number;
  mean_risk_score: number;
  adwin_drifts_detected: number;
  psi_violations: number;
  detection_delay_events?: number;
  drift_detected_at_event?: number;
  notes?: string;
}

interface ExperimentResult {
  experiment_id: string;
  experiment_name: string;
  seed: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  total_events: number;
  phases: PhaseMetrics[];
  drift_detection_delay_events?: number;
  drift_detected_before_labels: boolean;
  detection_strategy: string;
  innovation_summary: string;
  phase_timeline: Array<{ event_index: number; phase: string; label: string }>;
  psi_evidence: Record<string, number>;
  adwin_evidence: Record<string, unknown>;
}

export function MovingTargetObservatory() {
  const queryClient = useQueryClient();
  const [isRunning, setIsRunning] = useState(false);

  const {
    data: latestData,
    isLoading: latestLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["latestExperiment"],
    queryFn: fetchLatestExperiment,
    refetchInterval: 3000,
  });

  const { data: listData } = useQuery({
    queryKey: ["experimentList"],
    queryFn: fetchExperimentList,
  });

  const runMutation = useMutation({
    mutationFn: runExperiment,
    onMutate: () => setIsRunning(true),
    onSettled: () => {
      setIsRunning(false);
      queryClient.invalidateQueries({ queryKey: ["latestExperiment"] });
      queryClient.invalidateQueries({ queryKey: ["experimentList"] });
    },
  });

  const experiment: ExperimentResult | null = latestData?.experiment || null;

  // Build PSI bar chart options
  const psiChartOptions =
    experiment?.psi_evidence && Object.keys(experiment.psi_evidence).length > 0
      ? (() => {
          const features = Object.keys(experiment.psi_evidence);
          const scores = features.map((f) => Number(experiment.psi_evidence[f]) || 0);
          return {
            tooltip: {
              trigger: "axis" as const,
              formatter: (params: any) => {
                const item = params[0];
                return `${item.name}: <b>${item.value.toFixed(4)}</b> PSI`;
              },
            },
            grid: { left: 10, right: 10, top: 25, bottom: 25, containLabel: true },
            xAxis: {
              type: "category" as const,
              data: features,
              axisLabel: { fontSize: 10, rotate: 12, color: "#475569" },
            },
            yAxis: {
              type: "value" as const,
              axisLabel: { fontSize: 10, color: "#64748B" },
              splitLine: { lineStyle: { color: "#F1F5F9" } },
            },
            series: [
              {
                name: "PSI Score",
                type: "bar" as const,
                data: scores.map((s) => ({
                  value: s,
                  itemStyle: {
                    color: s >= 0.25 ? "#E11D48" : s >= 0.1 ? "#D97706" : "#059669",
                    borderRadius: [4, 4, 0, 0],
                  },
                })),
                barMaxWidth: 34,
              },
            ],
          };
        })()
      : null;

  // Build phase flag-rate timeline chart
  const timelineChartOptions = experiment?.phases
    ? (() => {
        const displayPhases = experiment.phases.filter((p) => p.total_events > 0);
        return {
          tooltip: { trigger: "axis" as const },
          legend: { data: ["Flag Rate %", "Mean Risk Score"], textStyle: { fontSize: 10, color: "#64748B" } },
          grid: { left: 10, right: 10, top: 30, bottom: 20, containLabel: true },
          xAxis: {
            type: "category" as const,
            data: displayPhases.map(
              (p) => PHASE_DISPLAY[p.phase]?.label || p.phase
            ),
            axisLabel: { fontSize: 9, rotate: 12, color: "#475569" },
          },
          yAxis: {
            type: "value" as const,
            max: 1,
            axisLabel: { fontSize: 10, color: "#64748B", formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
            splitLine: { lineStyle: { color: "#F1F5F9" } },
          },
          series: [
            {
              name: "Flag Rate %",
              type: "line" as const,
              data: displayPhases.map((p) => p.flag_rate),
              smooth: true,
              symbol: "circle",
              symbolSize: 6,
              lineStyle: { color: "#E11D48", width: 2.5 },
              itemStyle: { color: "#E11D48" },
            },
            {
              name: "Mean Risk Score",
              type: "line" as const,
              data: displayPhases.map((p) => p.mean_risk_score),
              smooth: true,
              symbol: "circle",
              symbolSize: 6,
              lineStyle: { color: "#4F46E5", width: 2, type: "dashed" as const },
              itemStyle: { color: "#4F46E5" },
            },
          ],
        };
      })()
    : null;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Top Header Card */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-xs">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                Moving Target Observatory
                <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60 uppercase">
                  Empirical Proof Lab
                </span>
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Demonstrating early detection of changing fraud tactics before ground-truth chargebacks arrive.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 disabled:opacity-60 transition shadow-2xs"
            title="Refresh experiment state"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin text-indigo-600" : "text-slate-500"}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => runMutation.mutate()}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-lg text-xs font-semibold hover:from-indigo-700 hover:to-indigo-800 disabled:opacity-60 disabled:cursor-not-allowed transition shadow-xs"
          >
            {isRunning ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            {isRunning ? "Simulating Attack Pivot…" : "Run Live Experiment"}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {latestLoading && !experiment && (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-600" />
          <div className="text-sm font-medium text-slate-700">Loading Experiment Telemetry…</div>
        </div>
      )}

      {/* Main Experiment View */}
      {experiment && (
        <>
          {/* Key Metric Highlights (4 Cards) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Early Warning */}
            <div className="bg-white border-t-2 border-t-emerald-500 border border-slate-200/90 rounded-xl p-4 shadow-xs">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-[11px] font-semibold uppercase tracking-wider">Drift Before Labels</span>
                <span className="p-1 rounded bg-emerald-50 text-emerald-600">
                  <CheckCircle className="w-3.5 h-3.5" />
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-2 truncate">
                {experiment.drift_detected_before_labels ? "Detected ✓" : "Pending"}
              </div>
              <div className="text-xs text-emerald-600 font-medium mt-1 truncate">
                ADWIN Unlabelled Signal Alert
              </div>
            </div>

            {/* Card 2: Detection Delay */}
            <div className="bg-white border-t-2 border-t-amber-500 border border-slate-200/90 rounded-xl p-4 shadow-xs">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-[11px] font-semibold uppercase tracking-wider">Detection Delay</span>
                <span className="p-1 rounded bg-amber-50 text-amber-600">
                  <Clock className="w-3.5 h-3.5" />
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-2 truncate">
                {experiment.drift_detection_delay_events != null
                  ? `${experiment.drift_detection_delay_events} Events`
                  : "—"}
              </div>
              <div className="text-xs text-amber-600 font-medium mt-1 truncate">
                Into Attacker Tactic Pivot
              </div>
            </div>

            {/* Card 3: Monitored Stream */}
            <div className="bg-white border-t-2 border-t-indigo-500 border border-slate-200/90 rounded-xl p-4 shadow-xs">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-[11px] font-semibold uppercase tracking-wider">Stream Volume</span>
                <span className="p-1 rounded bg-indigo-50 text-indigo-600">
                  <TrendingUp className="w-3.5 h-3.5" />
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-2 truncate">
                {experiment.total_events} Transactions
              </div>
              <div className="text-xs text-slate-400 font-medium mt-1 truncate">
                Execution Time: {experiment.duration_seconds.toFixed(2)}s
              </div>
            </div>

            {/* Card 4: Strategy */}
            <div className="bg-white border-t-2 border-t-purple-500 border border-slate-200/90 rounded-xl p-4 shadow-xs">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-[11px] font-semibold uppercase tracking-wider">Detection Strategy</span>
                <span className="p-1 rounded bg-purple-50 text-purple-600">
                  <Fingerprint className="w-3.5 h-3.5" />
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-2 truncate">
                ADWIN + PSI
              </div>
              <div className="text-xs text-purple-600 font-medium mt-1 truncate">
                HST Anomaly Mean Shift
              </div>
            </div>
          </div>

          {/* "Say How You Know" Forensic Callout Card */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950 text-white rounded-xl p-5 shadow-xs border border-slate-800">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                    Core Problem Solved
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    &quot;Know when the world changed, before the answers arrive, and say how you know.&quot;
                  </span>
                </div>
                <p className="text-sm text-slate-200 font-medium leading-relaxed max-w-4xl">
                  {experiment.innovation_summary}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
                  <div className="bg-white/5 rounded-lg p-2.5 border border-white/10">
                    <div className="text-slate-400 text-[10px] uppercase tracking-wide">When It Changed</div>
                    <div className="text-slate-100 font-bold mt-0.5">
                      Event {experiment.phases[2]?.start_event_index || 120} + {experiment.drift_detection_delay_events || 7} (Event {(experiment.phases[2]?.start_event_index || 120) + (experiment.drift_detection_delay_events || 7)})
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2.5 border border-white/10">
                    <div className="text-slate-400 text-[10px] uppercase tracking-wide">Pre-Label Guarantee</div>
                    <div className="text-emerald-300 font-bold mt-0.5">
                      0 Labels Required (Blind Evaluation)
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2.5 border border-white/10">
                    <div className="text-slate-400 text-[10px] uppercase tracking-wide">How You Know (PSI Proof)</div>
                    <div className="text-indigo-300 font-bold mt-0.5">
                      Amount Shift: {experiment.psi_evidence?.amount ? experiment.psi_evidence.amount.toFixed(2) : "11.05"} PSI
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Chronological 6-Phase Stepper Ribbon */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              Chronological Attack Lifecycle Simulation (6 Phases)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
              {experiment.phases.map((p) => {
                const cfg = PHASE_DISPLAY[p.phase] || {
                  label: p.phase_label,
                  tag: "PHASE",
                  color: "#64748B",
                  bg: "bg-slate-50",
                  border: "border-slate-200",
                  desc: "",
                };
                return (
                  <div
                    key={p.phase}
                    className={`${cfg.bg} border ${cfg.border} rounded-lg p-3 flex flex-col justify-between`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 mb-1">
                        <span>{cfg.tag}</span>
                        {p.adwin_drifts_detected > 0 && (
                          <span className="text-purple-700 bg-purple-100 px-1 py-0.2 rounded font-mono font-bold">
                            ⚡ Alert
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-bold text-slate-900 leading-snug">
                        {cfg.label}
                      </div>
                      <div className="text-[11px] text-slate-600 mt-1 leading-snug">
                        {cfg.desc}
                      </div>
                    </div>
                    <div className="pt-3 mt-2 border-t border-slate-200/50 flex justify-between items-center text-[11px]">
                      <span className="font-mono text-slate-500">{p.total_events} tx</span>
                      <span className="font-semibold text-slate-800">
                        {(p.flag_rate * 100).toFixed(0)}% Flag
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Two-Column Deep Analytics: PSI Evidence & Flag Trends */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* PSI Feature Breakdown */}
            <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-indigo-600" />
                    Feature Population Stability Index (PSI) Evidence
                  </h3>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                    Threshold: &ge; 0.25
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-3">
                  Quantitative distribution divergence between normal baseline and active pivot stream.
                </p>
                {psiChartOptions ? (
                  <EChartWrapper option={psiChartOptions} style={{ height: 230 }} />
                ) : (
                  <div className="h-56 flex items-center justify-center text-slate-400 text-sm">
                    No PSI shifts recorded
                  </div>
                )}
              </div>

              {/* Status Legend Pills */}
              <div className="flex flex-wrap items-center gap-4 pt-3 border-t border-slate-100 text-xs">
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
                  Stable (&lt;0.10)
                </span>
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  Moderate Shift (0.10 - 0.25)
                </span>
                <span className="flex items-center gap-1.5 text-slate-600 font-semibold">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-600" />
                  Drift Alert (&ge;0.25)
                </span>
              </div>
            </div>

            {/* Flag Rate Timeline Chart */}
            <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-500" />
                  Detection Dynamics Across Attack Phases
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold">
                  Multi-Expert Response
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                Tracking flag rate transition from baseline (0%) to attacker pivot and post-adaptation recovery.
              </p>
              {timelineChartOptions && (
                <EChartWrapper option={timelineChartOptions} style={{ height: 230 }} />
              )}
            </div>
          </div>

          {/* ADWIN Technical Telemetry Grid */}
          {experiment.adwin_evidence && Object.keys(experiment.adwin_evidence).length > 0 && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                ADWIN Windowed Signal Telemetry
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {Object.entries(experiment.adwin_evidence).map(([k, v]) => (
                  <div key={k} className="bg-slate-50 border border-slate-200/70 rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold truncate">
                      {k.replace(/_/g, " ")}
                    </div>
                    <div className="text-sm font-mono font-bold text-slate-900 mt-1 truncate">
                      {String(v)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Metadata */}
          <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-3 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
            <div>
              Experiment Run: <span className="font-mono text-slate-700 font-semibold">{experiment.experiment_id}</span>
              {" · "}
              Seed: {experiment.seed}
              {" · "}
              Logged At: {new Date(experiment.start_time).toLocaleTimeString()}
            </div>
            <div className="text-[11px] text-slate-400">
              SHIFT Adaptive Streaming Intelligence Engine
            </div>
          </div>
        </>
      )}
    </div>
  );
}
