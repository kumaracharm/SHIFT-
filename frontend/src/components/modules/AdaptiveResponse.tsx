"use client";

import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, Sliders, Plus, CheckCircle, Ban, ListFilter } from "lucide-react";

interface AdaptiveResponseProps {
  policies: any[];
  watchlist: any[];
  onSimulatePolicy: (blockThresh: number, reviewThresh: number) => Promise<any>;
  onAddToWatchlist: (entityId: string, type: string, reason: string) => Promise<any>;
}

export function AdaptiveResponse({
  policies,
  watchlist,
  onSimulatePolicy,
  onAddToWatchlist,
}: AdaptiveResponseProps) {
  // Simulator State
  const [blockThresh, setBlockThresh] = useState<number>(0.65);
  const [reviewThresh, setReviewThresh] = useState<number>(0.35);
  const [simResult, setSimResult] = useState<any | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Watchlist form
  const [newEntityId, setNewEntityId] = useState("");
  const [newType, setNewType] = useState("BLOCKLIST");
  const [newReason, setNewReason] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const res = await onSimulatePolicy(blockThresh, reviewThresh);
      setSimResult(res?.simulation || null);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleAddWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEntityId) return;
    setIsAdding(true);
    try {
      await onAddToWatchlist(newEntityId, newType, newReason);
      setNewEntityId("");
      setNewReason("");
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Adaptive Response & Policy Governance</h1>
        <p className="text-xs text-slate-500">
          Enforced autonomous remediation rules, statutory threshold simulator, and entity allowlisting/blocklisting
        </p>
      </div>

      {/* Grid: Policies Left, Simulator Right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Autonomous Policies */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h2 className="text-xs font-semibold text-slate-900">Enforced Autonomous Policies</h2>
              <p className="text-[10px] text-slate-400">Rules executed on every streaming transaction</p>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
              4 Active
            </span>
          </div>

          <div className="space-y-2.5">
            {policies.map((p) => {
              const isBlock = p.action === "BLOCK";
              return (
                <div key={p.id} className="p-3 rounded border border-slate-200 bg-slate-50/50 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                        {p.id}
                      </span>
                      <span className="font-semibold text-slate-900">{p.name}</span>
                    </div>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isBlock
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {p.action}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600">{p.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* What-If Policy Simulation Studio */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-4 text-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
              <div>
                <h2 className="text-xs font-semibold text-slate-900">What-If Threshold Simulator</h2>
                <p className="text-[10px] text-slate-400">Test impact on historical volume before deploying</p>
              </div>
              <Sliders className="w-4 h-4 text-slate-400" />
            </div>

            {/* Slider Controls */}
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Auto-Block Risk Cutoff:</span>
                  <span className="font-mono font-bold text-rose-600">{(blockThresh * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.50"
                  max="0.95"
                  step="0.05"
                  value={blockThresh}
                  onChange={(e) => setBlockThresh(parseFloat(e.target.value))}
                  className="w-full accent-rose-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Manual Review Cutoff:</span>
                  <span className="font-mono font-bold text-amber-600">{(reviewThresh * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.20"
                  max="0.55"
                  step="0.05"
                  value={reviewThresh}
                  onChange={(e) => setReviewThresh(parseFloat(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="w-full py-2 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-xs flex items-center justify-center gap-1.5"
              >
                <span>{isSimulating ? "Simulating..." : "Simulate Historical Impact"}</span>
              </button>
            </div>
          </div>

          {/* Simulation Output Card */}
          {simResult && (
            <div className="p-3 bg-slate-50 rounded border border-slate-200 space-y-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase">
                Projected Volume Breakdown ({simResult.total_tested} events tested)
              </span>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 bg-white rounded border border-slate-100">
                  <span className="text-[10px] text-teal-700 font-bold">ALLOW</span>
                  <div className="text-base font-bold text-slate-900 font-mono">
                    {simResult.allow_percentage}%
                  </div>
                  <span className="text-[10px] text-slate-400">{simResult.projected_allow} tx</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-100">
                  <span className="text-[10px] text-amber-700 font-bold">REVIEW</span>
                  <div className="text-base font-bold text-slate-900 font-mono">
                    {simResult.review_percentage}%
                  </div>
                  <span className="text-[10px] text-slate-400">{simResult.projected_review} tx</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-100">
                  <span className="text-[10px] text-rose-700 font-bold">BLOCK</span>
                  <div className="text-base font-bold text-slate-900 font-mono">
                    {simResult.block_percentage}%
                  </div>
                  <span className="text-[10px] text-slate-400">{simResult.projected_block} tx</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Entity Watchlist / Allowlist & Blocklist */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-4 text-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Entity Watchlist (Allowlist & Blocklist)</h2>
            <p className="text-[11px] text-slate-500">Autonomous override registries for verified accounts and confirmed adversaries</p>
          </div>

          {/* Add Entry Form */}
          <form onSubmit={handleAddWatchlist} className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              placeholder="Entity ID (USER_xxx / MERCHANT_xxx)"
              value={newEntityId}
              onChange={(e) => setNewEntityId(e.target.value)}
              className="p-1.5 border border-slate-200 rounded text-xs w-48 font-mono"
            />
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
              className="p-1.5 border border-slate-200 rounded text-xs bg-white"
            >
              <option value="BLOCKLIST">Blocklist (Quarantine)</option>
              <option value="ALLOWLIST">Allowlist (Trusted VIP)</option>
            </select>
            <input
              type="text"
              placeholder="Reason / ticket reference"
              value={newReason}
              onChange={(e) => setNewReason(e.target.value)}
              className="p-1.5 border border-slate-200 rounded text-xs w-48"
            />
            <button
              type="submit"
              disabled={isAdding || !newEntityId}
              className="px-3 py-1.5 bg-slate-900 text-white rounded font-medium hover:bg-slate-800 transition flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </form>
        </div>

        {/* Watchlist Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-semibold uppercase text-[10px]">
                <th className="py-2 px-3">Entity ID</th>
                <th className="py-2 px-3">List Type</th>
                <th className="py-2 px-3">Forensic Justification</th>
                <th className="py-2 px-3">Added Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {watchlist.map((w, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">{w.entity_id}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        w.type === "BLOCKLIST"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-teal-50 text-teal-700 border border-teal-200"
                      }`}
                    >
                      {w.type}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-600">{w.reason}</td>
                  <td className="py-2 px-3 font-mono text-[10px] text-slate-400">{w.added_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

