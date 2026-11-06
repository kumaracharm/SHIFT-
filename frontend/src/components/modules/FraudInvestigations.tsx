"use client";

import React, { useState } from "react";
import { FileSearch, CheckCircle, Ban, AlertCircle, Clock, ShieldAlert, Send } from "lucide-react";
import { formatCurrencyINR, formatDateTime } from "@/lib/utils";

interface FraudInvestigationsProps {
  cases: any[];
  onTakeAction: (eventId: string, action: string, notes: string) => Promise<void>;
  onSelectTransaction: (id: string) => void;
}

export function FraudInvestigations({ cases, onTakeAction, onSelectTransaction }: FraudInvestigationsProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(cases[0]?.event_id || null);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const activeCase = cases.find((c) => c.event_id === selectedCaseId) || cases[0];

  const handleAction = async (action: string) => {
    if (!activeCase) return;
    setIsSubmitting(true);
    try {
      await onTakeAction(activeCase.event_id, action, notes);
      setActionSuccess(`Action '${action}' applied successfully to ${activeCase.case_id}`);
      setNotes("");
      setTimeout(() => setActionSuccess(null), 4000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Fraud Investigations & Forensic Dossiers</h1>
        <p className="text-xs text-slate-500">Forensic review queue for flagged anomalies, rule violations, and high-risk UPI transfers</p>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-teal-50 border border-teal-200 text-teal-800 rounded text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-teal-600" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Grid: Cases Queue Left, Dossier Details Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Investigation Cases Queue */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <span className="font-semibold text-slate-900 text-xs">Active Investigation Queue</span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold">
              {cases.length} cases
            </span>
          </div>

          <div className="space-y-2 overflow-y-auto max-h-[600px]">
            {cases.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">Zero active review cases.</div>
            ) : (
              cases.map((c) => {
                const isSelected = c.event_id === activeCase?.event_id;
                const isCritical = c.system_action === "BLOCK";
                return (
                  <div
                    key={c.event_id}
                    onClick={() => setSelectedCaseId(c.event_id)}
                    className={`p-3 rounded border cursor-pointer transition text-xs ${
                      isSelected
                        ? "border-slate-900 bg-slate-50 shadow-sm"
                        : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-slate-900">{c.case_id}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isCritical
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {c.analyst_status || c.system_action}
                      </span>
                    </div>

                    <div className="mt-1.5 flex justify-between items-center">
                      <span className="text-slate-600 text-[11px]">
                        {c.sender_id} → {c.receiver_id}
                      </span>
                      <span className="font-mono font-bold text-slate-900">
                        {formatCurrencyINR(c.amount || 0)}
                      </span>
                    </div>

                    <div className="mt-2 text-[10px] text-slate-400 flex justify-between items-center">
                      <span>{c.evidence_count} evidence items</span>
                      <span>{formatDateTime(c.timestamp)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Detailed Dossier & Remediation Panel */}
        <div className="lg:col-span-2 space-y-4">
          {activeCase ? (
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-5 text-xs">
              {/* Dossier Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold font-mono text-slate-900">{activeCase.case_id}</span>
                    <span className="text-slate-400 font-mono text-xs">({activeCase.transaction_id})</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Assigned: <span className="font-semibold text-slate-700">{activeCase.assigned_analyst}</span> • Opened: {formatDateTime(activeCase.timestamp)}
                  </p>
                </div>
                <button
                  onClick={() => onSelectTransaction(activeCase.event_id)}
                  className="px-2.5 py-1 text-xs rounded border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium"
                >
                  View Full Transaction →
                </button>
              </div>

              {/* Subject & Score Cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Transaction Value</span>
                  <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
                    {formatCurrencyINR(activeCase.amount || 0)}
                  </div>
                  <span className="text-[10px] text-slate-500">Method: UPI</span>
                </div>
                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Supervised Probability</span>
                  <div className="text-base font-bold font-mono text-rose-600 mt-0.5">
                    {(activeCase.fraud_probability * 100).toFixed(1)}%
                  </div>
                  <span className="text-[10px] text-slate-500">IEEE-CIS Model</span>
                </div>
                <div className="p-3 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Anomaly Score</span>
                  <div className="text-base font-bold font-mono text-amber-600 mt-0.5">
                    {Number(activeCase.anomaly_score).toFixed(2)}
                  </div>
                  <span className="text-[10px] text-slate-500">River Half-Space Trees</span>
                </div>
              </div>

              {/* Evidence Breakdown */}
              <div className="space-y-2">
                <h3 className="font-semibold text-slate-900 text-xs">Key Risk Evidence & Detection Triggers</h3>
                <div className="space-y-1.5">
                  {activeCase.evidence_summary && activeCase.evidence_summary.length > 0 ? (
                    activeCase.evidence_summary.map((evText: string, i: number) => (
                      <div key={i} className="p-2.5 rounded bg-slate-50 border border-slate-100 flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                        <span className="text-slate-700 text-xs">{evText}</span>
                      </div>
                    ))
                  ) : (
                    <div className="p-2.5 rounded bg-slate-50 text-slate-400 text-xs">
                      Elevated statistical risk detected across multi-expert consensus.
                    </div>
                  )}
                </div>
              </div>

              {/* Analyst Action Decision Panel */}
              <div className="p-4 rounded-lg bg-slate-50/75 border border-slate-200 space-y-3">
                <h3 className="font-semibold text-slate-900 text-xs flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-slate-700" />
                  <span>Analyst Adjudication & Remediation Response</span>
                </h3>

                <textarea
                  rows={2}
                  placeholder="Enter forensic investigation notes or statutory justification..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full p-2.5 rounded border border-slate-200 bg-white text-xs text-slate-900 focus:outline-none focus:border-slate-400"
                />

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleAction("APPROVE_ALLOW")}
                    className="px-3 py-1.5 rounded bg-teal-600 text-white font-medium hover:bg-teal-700 transition flex items-center gap-1.5"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Approve (Allow)</span>
                  </button>

                  <button
                    disabled={isSubmitting}
                    onClick={() => handleAction("CONFIRM_FRAUD_BLOCK")}
                    className="px-3 py-1.5 rounded bg-rose-600 text-white font-medium hover:bg-rose-700 transition flex items-center gap-1.5"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Confirm Fraud (Block)</span>
                  </button>

                  <button
                    disabled={isSubmitting}
                    onClick={() => handleAction("ESCALATE_TIER2")}
                    className="px-3 py-1.5 rounded border border-slate-300 bg-white text-slate-700 font-medium hover:bg-slate-100 transition"
                  >
                    Escalate to Tier 2
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-12 text-center text-slate-400 text-xs">
              Select an investigation case from the queue to view full forensic telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

