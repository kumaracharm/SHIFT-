"use client";

import React, { useState } from "react";
import { Search, Filter, ShieldCheck, ShieldAlert, ArrowUpDown, X, ExternalLink } from "lucide-react";
import { formatCurrencyINR, formatDateTime } from "@/lib/utils";
import { StreamingDeflector } from "@/components/modules/StreamingDeflector";

interface LiveTransactionsProps {
  transactions: any[];
  total: number;
  selectedEventId: string | null;
  selectedTransactionDetail: any | null;
  onSelectTransaction: (id: string | null) => void;
  onFilterChange: (filters: { action?: string; search?: string }) => void;
}

export function LiveTransactions({
  transactions,
  total,
  selectedEventId,
  selectedTransactionDetail,
  onSelectTransaction,
  onFilterChange,
}: LiveTransactionsProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [actionFilter, setActionFilter] = useState("ALL");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({
      action: actionFilter === "ALL" ? undefined : actionFilter,
      search: searchTerm || undefined,
    });
  };

  const handleActionChange = (action: string) => {
    setActionFilter(action);
    onFilterChange({
      action: action === "ALL" ? undefined : action,
      search: searchTerm || undefined,
    });
  };

  const detail = selectedTransactionDetail;

  return (
    <div className="space-y-6">
      {/* Visual Streaming Sorter & Sliding Mechanical Deflector Gate */}
      <StreamingDeflector />

      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">Live Transaction Stream</h1>
          <p className="text-xs text-slate-500">Real-time ledger of verified UPI events and multi-expert scoring ({total} total)</p>
        </div>

        {/* Search & Filters */}
        <div className="flex items-center gap-2">
          {/* Action Filter Pills */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-md border border-slate-200 text-xs">
            {["ALL", "ALLOW", "REVIEW", "BLOCK"].map((act) => (
              <button
                key={act}
                onClick={() => handleActionChange(act)}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  actionFilter === act
                    ? "bg-white text-slate-900 shadow-sm font-semibold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {act}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search ID, sender, receiver..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-md border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-slate-400 w-56"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </form>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-4">Timestamp</th>
                <th className="py-2.5 px-4">Transaction ID</th>
                <th className="py-2.5 px-4">Parties</th>
                <th className="py-2.5 px-4">Location</th>
                <th className="py-2.5 px-4 text-right">Amount (INR)</th>
                <th className="py-2.5 px-4 text-center">Integrity</th>
                <th className="py-2.5 px-4 text-center">Fraud Prob</th>
                <th className="py-2.5 px-4 text-center">Anomaly</th>
                <th className="py-2.5 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No transactions match the selected filters.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => {
                  const isSelected = tx.event_id === selectedEventId;
                  const isBlock = tx.action_decision === "BLOCK" || tx.decision === "INTEGRITY_REJECTED";
                  const isReview = tx.action_decision === "REVIEW";
                  return (
                    <tr
                      key={tx.event_id}
                      onClick={() => onSelectTransaction(tx.event_id)}
                      className={`cursor-pointer transition hover:bg-slate-50/80 ${
                        isSelected ? "bg-slate-100/70 font-medium" : ""
                      }`}
                    >
                      <td className="py-2.5 px-4 font-mono text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDateTime(tx.timestamp)}
                      </td>
                      <td className="py-2.5 px-4 font-mono font-semibold text-slate-900">
                        {tx.transaction_id || tx.event_id.slice(0, 10)}
                      </td>
                      <td className="py-2.5 px-4 text-slate-700">
                        <div className="font-semibold text-slate-900">{tx.sender_id || "N/A"}</div>
                        <div className="text-[10px] text-slate-400">→ {tx.receiver_id || "N/A"}</div>
                      </td>
                      <td className="py-2.5 px-4 text-slate-600">{tx.location || "Bengaluru"}</td>
                      <td className="py-2.5 px-4 text-right font-mono font-bold text-slate-900">
                        {formatCurrencyINR(tx.amount || 0)}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            tx.integrity_status === "VALID"
                              ? "text-teal-700 bg-teal-50 border border-teal-200"
                              : "text-rose-700 bg-rose-50 border border-rose-200"
                          }`}
                        >
                          {tx.integrity_status === "VALID" ? "VALID" : "REJECTED"}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono">
                        <span
                          className={`font-semibold ${
                            tx.fraud_probability >= 0.70
                              ? "text-rose-600"
                              : tx.fraud_probability >= 0.35
                              ? "text-amber-600"
                              : "text-slate-600"
                          }`}
                        >
                          {(tx.fraud_probability * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono text-slate-600">
                        {Number(tx.anomaly_score).toFixed(2)}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            isBlock
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : isReview
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : "bg-teal-50 text-teal-700 border border-teal-200"
                          }`}
                        >
                          {isBlock ? "BLOCK" : isReview ? "REVIEW" : "ALLOW"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-Over Inspection Drawer */}
      {selectedEventId && detail && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-white border-l border-slate-200 shadow-2xl z-50 flex flex-col justify-between">
          {/* Drawer Header */}
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {detail.transaction_id || detail.event_id}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    detail.action_decision === "BLOCK"
                      ? "bg-rose-50 text-rose-700 border border-rose-200"
                      : detail.action_decision === "REVIEW"
                      ? "bg-amber-50 text-amber-700 border border-amber-200"
                      : "bg-teal-50 text-teal-700 border border-teal-200"
                  }`}
                >
                  {detail.action_decision}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">Verified forensic dossier</p>
            </div>
            <button
              onClick={() => onSelectTransaction(null)}
              className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/50 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="p-4 overflow-y-auto space-y-4 flex-1 text-xs">
            {/* Core Summary Cards */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Amount</span>
                <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                  {formatCurrencyINR(detail.amount || 0)}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Fraud Risk</span>
                <div className="text-lg font-bold font-mono text-rose-600 mt-0.5">
                  {(detail.fraud_probability * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Cryptographic Verification */}
            <div className="p-3 rounded border border-slate-200 bg-white">
              <h3 className="font-semibold text-slate-900 text-xs mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <span>Cryptographic & Integrity Verification</span>
              </h3>
              <div className="space-y-1.5 text-[11px] font-mono text-slate-600">
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Integrity Status:</span>
                  <span className="font-bold text-teal-700">{detail.integrity_status || "VALID"}</span>
                </div>
                <div className="flex justify-between truncate">
                  <span className="text-slate-400 font-sans">Key ID:</span>
                  <span>{detail.key_id}</span>
                </div>
                <div className="flex justify-between truncate">
                  <span className="text-slate-400 font-sans">Nonce:</span>
                  <span>{detail.nonce}</span>
                </div>
                <div>
                  <span className="text-slate-400 font-sans block mb-1">Ed25519 Signature:</span>
                  <div className="p-2 bg-slate-50 rounded font-mono text-[10px] text-slate-700 break-all select-all border border-slate-100">
                    {detail.signature}
                  </div>
                </div>
              </div>
            </div>

            {/* Evidence Items */}
            {detail.evidence && detail.evidence.length > 0 && (
              <div className="p-3 rounded border border-slate-200 bg-white">
                <h3 className="font-semibold text-slate-900 text-xs mb-2">Evidence & Contributing Factors</h3>
                <div className="space-y-2">
                  {detail.evidence.map((ev: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-slate-50 border border-slate-100">
                      <div className="flex items-center justify-between text-[10px] font-semibold text-slate-600">
                        <span>{ev.factor}</span>
                        <span className={ev.severity === "CRITICAL" ? "text-rose-600" : "text-amber-600"}>
                          {ev.severity}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-700 mt-1">{ev.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw JSON Payload */}
            <div>
              <span className="font-semibold text-slate-900 text-xs block mb-1">Raw Event Payload</span>
              <pre className="p-3 rounded bg-slate-900 text-slate-200 font-mono text-[10px] overflow-x-auto max-h-48">
                {JSON.stringify(detail.payload, null, 2)}
              </pre>
            </div>
          </div>

          {/* Drawer Footer Actions */}
          <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-[11px] text-slate-500 font-mono">Event ID: {detail.event_id?.slice(0, 12)}</span>
            <button
              onClick={() => onSelectTransaction(null)}
              className="px-3 py-1.5 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-xs"
            >
              Close Dossier
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

