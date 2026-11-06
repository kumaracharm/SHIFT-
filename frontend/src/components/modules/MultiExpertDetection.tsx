"use client";

import React, { useState } from "react";
import { Cpu, Sliders, CheckCircle2, Play, RefreshCw, BarChart2 } from "lucide-react";
import { EChartWrapper } from "@/components/charts/EChartWrapper";

interface MultiExpertDetectionProps {
  statusData: any;
  onUpdateWeights: (weights: Record<string, number>) => Promise<any>;
  onEvaluatePayload: (payload: any) => Promise<any>;
}

export function MultiExpertDetection({
  statusData,
  onUpdateWeights,
  onEvaluatePayload,
}: MultiExpertDetectionProps) {
  const experts = statusData?.experts || [];

  // Local state for interactive test evaluation
  const [testAmount, setTestAmount] = useState<number>(45000);
  const [testVelocity, setTestVelocity] = useState<number>(3.5);
  const [testDeviceConsistency, setTestDeviceConsistency] = useState<number>(0.4);
  const [testNetworkRisk, setTestNetworkRisk] = useState<number>(1.0);
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Dynamic weights editing
  const [weights, setWeights] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    experts.forEach((e: any) => {
      init[e.name] = e.weight;
    });
    return init;
  });
  const [weightSaved, setWeightSaved] = useState(false);

  const handleWeightChange = (name: string, val: number) => {
    setWeights((prev) => ({ ...prev, [name]: val }));
  };

  const handleSaveWeights = async () => {
    await onUpdateWeights(weights);
    setWeightSaved(true);
    setTimeout(() => setWeightSaved(false), 3000);
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const res = await onEvaluatePayload({
        amount: testAmount,
        features: {
          amount: testAmount,
          log_amount: Math.log1p(testAmount),
          amount_zscore: (testAmount - 2000) / 10000,
          time_since_prev: 2.0,
          transaction_velocity: testVelocity,
          device_consistency: testDeviceConsistency,
          session_consistency: 0.5,
          network_risk_flag: testNetworkRisk,
        },
      });
      setEvalResult(res?.data || null);
    } finally {
      setIsEvaluating(false);
    }
  };

  // Radar Chart comparing the 7 experts
  const radarIndicators = (evalResult?.expert_breakdown || experts).map((e: any) => ({
    name: e.expert_name || e.name,
    max: 1.0,
  }));

  const radarScores = evalResult
    ? evalResult.expert_breakdown.map((e: any) => e.score)
    : [0.08, 0.45, 0.30, 0.65, 0.70, 0.85, 0.60];

  const radarOption = {
    tooltip: { trigger: "item" },
    radar: {
      indicator: radarIndicators.length > 0 ? radarIndicators : [{ name: "Expert 1", max: 1 }],
      splitNumber: 4,
      axisName: { color: "#64748B", fontSize: 10 },
      splitLine: { lineStyle: { color: "#E2E8F0" } },
      splitArea: { areaStyle: { color: ["#FFFFFF", "#F8FAFC"] } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: radarScores,
            name: "Expert Risk Score",
            itemStyle: { color: "#E11D48" },
            areaStyle: { color: "rgba(225, 29, 72, 0.2)" },
          },
        ],
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Multi-Expert Detection & Transparent Risk Fusion</h1>
        <p className="text-xs text-slate-500">
          7 specialist models evaluate independent physical and statistical dimensions combined via transparent weighted consensus
        </p>
      </div>

      {/* Grid: 7 Experts List & Radar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: 7 Specialist Experts Card List */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h2 className="text-xs font-semibold text-slate-900">7 Registered Specialist Experts</h2>
              <p className="text-[10px] text-slate-400">Independent dimensional specialists with dynamic weighting</p>
            </div>
            <button
              onClick={handleSaveWeights}
              className="px-2.5 py-1 rounded bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition flex items-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5 text-teal-400" />
              <span>{weightSaved ? "Weights Calibrated!" : "Save Weights"}</span>
            </button>
          </div>

          <div className="space-y-2.5">
            {experts.map((e: any) => {
              const currentW = weights[e.name] ?? e.weight;
              return (
                <div key={e.name} className="p-3 rounded border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">{e.name}</span>
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-slate-200 text-slate-700">
                        {e.category}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">{e.description || "Specialist detection model."}</p>
                  </div>

                  {/* Weight Slider */}
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] text-slate-400 font-medium">Weight:</span>
                    <input
                      type="range"
                      min="0.5"
                      max="3.0"
                      step="0.1"
                      value={currentW}
                      onChange={(evt) => handleWeightChange(e.name, parseFloat(evt.target.value))}
                      className="w-24 accent-slate-900"
                    />
                    <span className="font-mono font-bold text-slate-800 w-8 text-right">
                      {currentW.toFixed(1)}x
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Radar Chart & Mathematical Breakdown */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 flex flex-col justify-between">
          <div>
            <h2 className="text-xs font-semibold text-slate-900">Multi-Dimensional Risk Profile</h2>
            <p className="text-[10px] text-slate-400">Radar synthesis of expert outputs</p>
          </div>

          <EChartWrapper option={radarOption} style={{ height: "260px", width: "100%" }} />

          <div className="p-3 bg-slate-50 rounded border border-slate-200 text-[11px] space-y-1">
            <span className="font-bold text-slate-800 block text-xs">Mathematical Risk Fusion</span>
            <div className="font-mono text-slate-600 text-[10px]">
              FinalScore = Σ(w_i × score_i) / Σ(w_i)
            </div>
            <p className="text-slate-500 text-[10px] mt-1">
              Zero black-box hallucinations: each decision preserves exact attribution back to individual specialist evidence.
            </p>
          </div>
        </div>
      </div>

      {/* Interactive Ad-Hoc Payload Simulation Bar */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4 text-xs">
        <div>
          <h2 className="font-semibold text-slate-900 text-sm">Interactive Multi-Expert Simulator</h2>
          <p className="text-xs text-slate-500">Test hypothetical transaction features against all 7 experts in real-time</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Amount (₹)</label>
            <input
              type="number"
              value={testAmount}
              onChange={(e) => setTestAmount(parseFloat(e.target.value) || 0)}
              className="w-full p-2 border border-slate-200 rounded text-xs font-mono"
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Velocity (tx/min)</label>
            <input
              type="number"
              step="0.5"
              value={testVelocity}
              onChange={(e) => setTestVelocity(parseFloat(e.target.value) || 0)}
              className="w-full p-2 border border-slate-200 rounded text-xs font-mono"
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Device Consistency</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={testDeviceConsistency}
              onChange={(e) => setTestDeviceConsistency(parseFloat(e.target.value) || 0)}
              className="w-full p-2 border border-slate-200 rounded text-xs font-mono"
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Network Risk (0 or 1)</label>
            <select
              value={testNetworkRisk}
              onChange={(e) => setTestNetworkRisk(parseFloat(e.target.value))}
              className="w-full p-2 border border-slate-200 rounded text-xs bg-white"
            >
              <option value={0}>0.0 (Clean Residential IP)</option>
              <option value={1}>1.0 (Untrusted VPN/Hosting)</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={isEvaluating}
          className="px-4 py-2 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition flex items-center gap-2 text-xs"
        >
          <Play className="w-3.5 h-3.5 text-teal-400" />
          <span>{isEvaluating ? "Evaluating 7 Experts..." : "Run Multi-Expert Fusion"}</span>
        </button>

        {evalResult && (
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900">Consensus Evaluation Result:</span>
              <span
                className={`px-2.5 py-1 rounded text-xs font-bold ${
                  evalResult.consensus_action === "BLOCK"
                    ? "bg-rose-100 text-rose-800"
                    : evalResult.consensus_action === "REVIEW"
                    ? "bg-amber-100 text-amber-800"
                    : "bg-teal-100 text-teal-800"
                }`}
              >
                ACTION: {evalResult.consensus_action}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2 bg-white rounded border border-slate-200">
                <span className="text-[10px] text-slate-400">Fused Risk Score</span>
                <div className="font-mono font-bold text-slate-900 text-sm">
                  {(evalResult.fused_risk_score * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-2 bg-white rounded border border-slate-200">
                <span className="text-[10px] text-slate-400">Aggregate Confidence</span>
                <div className="font-mono font-bold text-slate-900 text-sm">
                  {(evalResult.fused_confidence * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-2 bg-white rounded border border-slate-200">
                <span className="text-[10px] text-slate-400">Allow Votes</span>
                <div className="font-mono font-bold text-teal-700 text-sm">
                  {evalResult.votes?.ALLOW || 0}
                </div>
              </div>
              <div className="p-2 bg-white rounded border border-slate-200">
                <span className="text-[10px] text-slate-400">Block Votes</span>
                <div className="font-mono font-bold text-rose-700 text-sm">
                  {evalResult.votes?.BLOCK || 0}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

