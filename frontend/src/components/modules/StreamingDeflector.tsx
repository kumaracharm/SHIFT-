"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  Sliders,
  ArrowDownRight,
  ArrowRight,
  Radio,
  Lock,
  RotateCcw,
  AlertTriangle,
} from "lucide-react";
import { formatCurrencyINR } from "@/lib/utils";

interface StreamItem {
  id: string;
  txId: string;
  amount: number;
  sender: string;
  receiver: string;
  riskScore: number;
  anomalyScore: number;
  isFraud: boolean;
  reason?: string;
  timestamp: string;
}

export function StreamingDeflector() {
  const [isRodActive, setIsRodActive] = useState<boolean>(false);
  const [autoDeflect, setAutoDeflect] = useState<boolean>(true);
  const [animatingTx, setAnimatingTx] = useState<StreamItem | null>(null);
  const [animationPhase, setAnimationPhase] = useState<"idle" | "incoming" | "deflecting" | "passing">("idle");
  const [deflectedItems, setDeflectedItems] = useState<StreamItem[]>([
    {
      id: "def_01",
      txId: "UPI-20261106-99042",
      amount: 85000,
      sender: "USER_1042",
      receiver: "MERCHANT_MULE_99",
      riskScore: 0.94,
      anomalyScore: 0.88,
      isFraud: true,
      reason: "High-Value Spike +4.8σ Deflected by Rod",
      timestamp: new Date(Date.now() - 45000).toLocaleTimeString(),
    },
    {
      id: "def_02",
      txId: "UPI-20261106-99043",
      amount: 4999,
      sender: "USER_8821",
      receiver: "UNKNOWN_VPA_77",
      riskScore: 0.89,
      anomalyScore: 0.82,
      isFraud: true,
      reason: "Sub-Second Velocity Burst Deflected",
      timestamp: new Date(Date.now() - 15000).toLocaleTimeString(),
    },
  ]);
  const [cleanItems, setCleanItems] = useState<StreamItem[]>([
    {
      id: "cln_01",
      txId: "UPI-20261106-11029",
      amount: 850,
      sender: "USER_4012",
      receiver: "SWIGGY_BLR",
      riskScore: 0.04,
      anomalyScore: 0.06,
      isFraud: false,
      reason: "Clean P2M Transfer Verified",
      timestamp: new Date(Date.now() - 30000).toLocaleTimeString(),
    },
    {
      id: "cln_02",
      txId: "UPI-20261106-11030",
      amount: 1420,
      sender: "USER_5590",
      receiver: "AMAZON_PAY",
      riskScore: 0.05,
      anomalyScore: 0.08,
      isFraud: false,
      reason: "Trusted Device & Network",
      timestamp: new Date(Date.now() - 10000).toLocaleTimeString(),
    },
  ]);

  // Handle injected attack triggering the sliding rod
  const triggerDeflection = (type: "amount_spike" | "velocity_burst" | "tampered_sig" | "clean") => {
    let newItem: StreamItem;
    const now = new Date().toLocaleTimeString();

    if (type === "amount_spike") {
      newItem = {
        id: `tx_${Date.now()}`,
        txId: `UPI-20261106-${Math.floor(10000 + Math.random() * 90000)}`,
        amount: Math.floor(75000 + Math.random() * 20000),
        sender: "USER_SUSPECT_01",
        receiver: "MULE_ACCOUNT_44",
        riskScore: 0.96,
        anomalyScore: 0.91,
        isFraud: true,
        reason: "Massive ₹85k Outlier Deflected by Rod",
        timestamp: now,
      };
    } else if (type === "velocity_burst") {
      newItem = {
        id: `tx_${Date.now()}`,
        txId: `UPI-20261106-${Math.floor(10000 + Math.random() * 90000)}`,
        amount: 4999,
        sender: "USER_BOTNET_19",
        receiver: "GATEWAY_CARD_TEST",
        riskScore: 0.91,
        anomalyScore: 0.85,
        isFraud: true,
        reason: "Sub-Second Burst (>8 tx/min) Intercepted",
        timestamp: now,
      };
    } else if (type === "tampered_sig") {
      newItem = {
        id: `tx_${Date.now()}`,
        txId: `UPI-20261106-${Math.floor(10000 + Math.random() * 90000)}`,
        amount: 32500,
        sender: "USER_MITM_09",
        receiver: "OFFSHORE_VPA_12",
        riskScore: 1.0,
        anomalyScore: 0.98,
        isFraud: true,
        reason: "Ed25519 Cryptographic Signature Failed",
        timestamp: now,
      };
    } else {
      newItem = {
        id: `tx_${Date.now()}`,
        txId: `UPI-20261106-${Math.floor(10000 + Math.random() * 90000)}`,
        amount: Math.floor(350 + Math.random() * 1200),
        sender: `USER_${Math.floor(1000 + Math.random() * 9000)}`,
        receiver: "RELIANCE_RETAIL",
        riskScore: 0.02,
        anomalyScore: 0.05,
        isFraud: false,
        reason: "Legitimate Verified Merchant Payment",
        timestamp: now,
      };
    }

    setAnimatingTx(newItem);
    setAnimationPhase("incoming");

    // If it's fraudulent and auto-deflect is on, slide down the mechanical rod!
    if (newItem.isFraud && autoDeflect) {
      setTimeout(() => {
        setIsRodActive(true);
        setAnimationPhase("deflecting");
      }, 500);

      setTimeout(() => {
        setDeflectedItems((prev) => [newItem, ...prev.slice(0, 9)]);
        setAnimationPhase("idle");
        // Keep rod active briefly then return
        setTimeout(() => setIsRodActive(false), 800);
      }, 1600);
    } else {
      // Clean transaction flows straight through
      setTimeout(() => {
        setIsRodActive(false);
        setAnimationPhase("passing");
      }, 500);

      setTimeout(() => {
        setCleanItems((prev) => [newItem, ...prev.slice(0, 9)]);
        setAnimationPhase("idle");
      }, 1400);
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs space-y-5">
      {/* Top Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              Streaming Fraud Deflector &amp; Mechanical Diverter Track
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-rose-50 text-rose-700 border border-rose-200 uppercase">
                Physical Metaphor
              </span>
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Watch transactions flow through the main channel. When fraudulent data is detected, the mechanical rod slides down and deflects it into the detention branch.
          </p>
        </div>

        {/* Rod Mode Switch */}
        <div className="flex items-center gap-3 shrink-0">
          <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer select-none">
            <span className="font-medium text-slate-700">Auto AI Deflect</span>
            <input
              type="checkbox"
              checked={autoDeflect}
              onChange={(e) => setAutoDeflect(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300"
            />
          </label>

          <button
            onClick={() => setIsRodActive(!isRodActive)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition border shadow-2xs ${
              isRodActive
                ? "bg-rose-600 text-white border-rose-700 animate-pulse"
                : "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>{isRodActive ? "Deflector Gate: ENGAGED" : "Slide Deflector Rod"}</span>
          </button>
        </div>
      </div>

      {/* Interactive Trigger Buttons (Inject Fraud Scenarios) */}
      <div className="flex flex-wrap items-center gap-2 bg-slate-50/80 p-2.5 rounded-lg border border-slate-200/80">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1 flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          Simulate Ingestion:
        </span>
        <button
          onClick={() => triggerDeflection("clean")}
          className="px-2.5 py-1 rounded bg-white hover:bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200 transition shadow-2xs"
        >
          Normal ₹850 (Clean Flow)
        </button>
        <button
          onClick={() => triggerDeflection("amount_spike")}
          className="px-2.5 py-1 rounded bg-white hover:bg-rose-50 text-rose-700 text-xs font-semibold border border-rose-200 transition shadow-2xs"
        >
          Inject ₹85,000 Spike (Slide Rod)
        </button>
        <button
          onClick={() => triggerDeflection("velocity_burst")}
          className="px-2.5 py-1 rounded bg-white hover:bg-amber-50 text-amber-700 text-xs font-semibold border border-amber-200 transition shadow-2xs"
        >
          Inject Velocity Burst (Slide Rod)
        </button>
        <button
          onClick={() => triggerDeflection("tampered_sig")}
          className="px-2.5 py-1 rounded bg-white hover:bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-200 transition shadow-2xs"
        >
          Inject Bad Signature (Slide Rod)
        </button>
      </div>

      {/* Visual Conveyor & Sliding Diverter Track */}
      <div className="relative bg-slate-950 rounded-xl p-6 overflow-hidden border border-slate-800 text-white min-h-[170px] flex flex-col justify-between shadow-inner">
        {/* Track Markings */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-16 border-y border-dashed border-slate-700/60 pointer-events-none" />

        {/* Main Conveyor Line */}
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 z-10">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
              Primary Ingestion Stream
            </span>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <div className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Straight Track &rarr; Settled Ledger</span>
            </div>
            <div className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span>Diverted Track &#8600; Detention Branch</span>
            </div>
          </div>
        </div>

        {/* Central Moving Track Area with Sliding Mechanical Rod */}
        <div className="relative h-20 flex items-center my-2">
          {/* Incoming Transaction Token Animation */}
          {animatingTx && (
            <div
              className={`absolute top-1/2 -translate-y-1/2 z-20 transition-all duration-700 ease-out flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono text-xs font-bold shadow-lg ${
                animatingTx.isFraud
                  ? "bg-rose-600 text-white ring-2 ring-rose-400"
                  : "bg-emerald-600 text-white ring-2 ring-emerald-400"
              }`}
              style={{
                left:
                  animationPhase === "incoming"
                    ? "20%"
                    : animationPhase === "deflecting"
                    ? "55%"
                    : animationPhase === "passing"
                    ? "85%"
                    : "5%",
                transform:
                  animationPhase === "deflecting"
                    ? "translateY(35px) rotate(18deg)"
                    : "translateY(-50%)",
                opacity: animationPhase === "idle" ? 0 : 1,
              }}
            >
              <span>{animatingTx.txId}</span>
              <span className="bg-black/30 px-1.5 py-0.2 rounded text-[10px]">
                {formatCurrencyINR(animatingTx.amount)}
              </span>
              {animatingTx.isFraud ? (
                <ShieldAlert className="w-3.5 h-3.5 text-rose-200" />
              ) : (
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-200" />
              )}
            </div>
          )}

          {/* THE PHYSICAL SLIDING ROD / DEFLECTOR GATE */}
          <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-16 flex flex-col items-center justify-center z-10 pointer-events-none">
            {/* Top Actuator Cylinder */}
            <div
              className={`w-10 h-3 rounded-t-sm transition-colors duration-300 border-x border-t ${
                isRodActive
                  ? "bg-rose-500 border-rose-300 shadow-md shadow-rose-500/50"
                  : "bg-slate-700 border-slate-500"
              }`}
            />

            {/* The Mechanical Sliding Rod Blade */}
            <div
              className={`w-2.5 rounded-full transition-all duration-500 ease-in-out border ${
                isRodActive
                  ? "h-16 bg-gradient-to-b from-rose-400 via-rose-500 to-amber-400 border-rose-300 shadow-lg shadow-rose-500/80 rotate-12"
                  : "h-3 bg-slate-600 border-slate-400 opacity-60"
              }`}
            />

            {/* Rod Status Tag */}
            <div className="mt-1 text-[9px] font-mono uppercase font-bold tracking-wider">
              {isRodActive ? (
                <span className="text-rose-400 animate-pulse">GATE: CLOSED</span>
              ) : (
                <span className="text-slate-500">GATE: OPEN</span>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Legend */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 z-10">
          <span className="flex items-center gap-1 font-mono">
            &larr; Stream Ingested
          </span>
          <span className="font-mono text-center text-slate-500">
            [Mechanical Intercept Zone: Anomaly &gt; 0.70 &rarr; Auto Deflection]
          </span>
          <span className="flex items-center gap-1 font-mono">
            Output Streams &rarr;
          </span>
        </div>
      </div>

      {/* Two Real Live Branches: Clean Flow vs Quarantined Fraud */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Branch A: Clean / Verified Ledger */}
        <div className="bg-emerald-50/40 border border-emerald-200/80 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Branch A: Legitimate Verified Stream
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-emerald-100 text-emerald-800">
                {cleanItems.length} Settled
              </span>
            </div>
            <div className="divide-y divide-emerald-100/80 text-xs">
              {cleanItems.map((item) => (
                <div key={item.id} className="py-2 flex items-center justify-between">
                  <div>
                    <div className="font-mono font-semibold text-slate-800 flex items-center gap-1.5">
                      <span>{item.txId}</span>
                      <span className="text-slate-400 font-normal">({item.sender} &rarr; {item.receiver})</span>
                    </div>
                    <div className="text-[11px] text-emerald-700 mt-0.5">{item.reason}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-slate-900">{formatCurrencyINR(item.amount)}</div>
                    <div className="text-[10px] text-emerald-600 font-semibold uppercase">STATUS: VERIFIED</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-3 mt-2 border-t border-emerald-200/60 text-[11px] text-emerald-700/80 flex justify-between">
            <span>Passes straight through primary pipeline</span>
            <span className="font-mono">Normal Settlement</span>
          </div>
        </div>

        {/* Branch B: Quarantined & Deflected Fraud Branch */}
        <div className="bg-rose-50/40 border border-rose-200/80 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                Branch B: Quarantined Fraud Detention Branch
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-rose-100 text-rose-800">
                {deflectedItems.length} Deflected
              </span>
            </div>
            <div className="divide-y divide-rose-100/80 text-xs">
              {deflectedItems.map((item) => (
                <div key={item.id} className="py-2 flex items-center justify-between">
                  <div>
                    <div className="font-mono font-bold text-rose-950 flex items-center gap-1.5">
                      <span>{item.txId}</span>
                      <span className="text-rose-600 text-[10px] font-semibold bg-rose-100 px-1 py-0.2 rounded">
                        DEFLECTED
                      </span>
                    </div>
                    <div className="text-[11px] text-rose-700 font-medium mt-0.5">{item.reason}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-rose-900">{formatCurrencyINR(item.amount)}</div>
                    <div className="text-[10px] text-rose-700 font-bold uppercase tracking-wider">
                      INTERCEPTED (ROD ENGAGED)
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-3 mt-2 border-t border-rose-200/60 text-[11px] text-rose-700/80 flex justify-between">
            <span>Intercepted &amp; diverted away from core banking rail</span>
            <span className="font-mono font-bold">Detained in Review Queue</span>
          </div>
        </div>
      </div>
    </div>
  );
}

