"use client";

import React, { useState } from "react";
import { Play, Pause, RotateCcw, FastForward, Zap, ShieldAlert, Download, Sliders, CheckCircle2 } from "lucide-react";
import { formatCurrencyINR, formatDateTime } from "@/lib/utils";

interface SimulationStudioProps {
  simulationState: any;
  scenarios: any[];
  recentEvents: any[];
  onStartSimulation: (scenario: string, speed: number) => Promise<any>;
  onPauseSimulation: () => Promise<any>;
  onStepSimulation: (count: number, scenario: string) => Promise<any>;
  onInjectAttack: (scenario: string, tamper?: boolean) => Promise<any>;
  onResetSimulation: () => Promise<any>;
}

export function SimulationStudio({
  simulationState,
  scenarios,
  recentEvents,
  onStartSimulation,
  onPauseSimulation,
  onStepSimulation,
  onInjectAttack,
  onResetSimulation,
}: SimulationStudioProps) {
  const state = simulationState?.state || {};
  const isRunning = state.state === "RUNNING";
  const [selectedScenario, setSelectedScenario] = useState("upi_normal");
  const [speed, setSpeed] = useState<number>(1.0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setActionMessage(msg);
    setTimeout(() => setActionMessage(null), 3500);
  };

  const handleStart = async () => {
    setIsProcessing(true);
    try {
      await onStartSimulation(selectedScenario, speed);
      showNotification(`Simulation continuous stream started (${speed} tx/s)`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePause = async () => {
    setIsProcessing(true);
    try {
      await onPauseSimulation();
      showNotification("Simulation paused");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStep = async (count: number) => {
    setIsProcessing(true);
    try {
      await onStepSimulation(count, selectedScenario);
      showNotification(`Stepped ${count} transactions through detection pipeline`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleInject = async (scenarioKey: string, tamper: boolean = false) => {
    setIsProcessing(true);
    try {
      const res = await onInjectAttack(scenarioKey, tamper);
      const r = res?.result || {};
      showNotification(`Injected ${scenarioKey}: Decision = ${r.decision || "PROCESSED"}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = async () => {
    setIsProcessing(true);
    try {
      await onResetSimulation();
      showNotification("Simulation stopped and operator state reset");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Interactive Simulation Studio & Attack Injection Lab</h1>
        <p className="text-xs text-slate-500">
          Operator control panel governing streaming UPI transaction synthesis, adversary scenario injection, and real-time ledger response
        </p>
      </div>

      {actionMessage && (
        <div className="p-3 bg-teal-50 border border-teal-200 text-teal-800 rounded text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Operator Control Panel Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4 text-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-900 text-sm">Operator Control Deck</span>
            <div className="flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-700">
              <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-teal-500 animate-pulse" : "bg-slate-400"}`}></span>
              <span>STATE: {state.state || "STOPPED"}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="/api/v1/simulation/export"
              target="_blank"
              download
              className="px-3 py-1.5 rounded border border-slate-200 bg-white text-slate-700 font-medium hover:bg-slate-50 transition flex items-center gap-1.5 text-xs shadow-sm"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </a>
          </div>
        </div>

        {/* Controls Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
          {/* Active Scenario Selector */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">
              Streaming Scenario Type
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="w-full p-2 border border-slate-200 rounded text-xs bg-white text-slate-800 focus:outline-none focus:border-slate-400"
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name} ({sc.threat_level})
                </option>
              ))}
            </select>
          </div>

          {/* Speed Slider */}
          <div>
            <div className="flex justify-between text-xs text-slate-600 mb-1">
              <span>Streaming Speed:</span>
              <span className="font-mono font-bold text-slate-900">{speed.toFixed(1)} tx/sec</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.5"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-slate-900"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {isRunning ? (
              <button
                disabled={isProcessing}
                onClick={handlePause}
                className="flex-1 py-2 rounded bg-amber-600 text-white font-medium hover:bg-amber-700 transition flex items-center justify-center gap-1.5"
              >
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                disabled={isProcessing}
                onClick={handleStart}
                className="flex-1 py-2 rounded bg-teal-600 text-white font-medium hover:bg-teal-700 transition flex items-center justify-center gap-1.5 shadow-sm"
              >
                <Play className="w-4 h-4" />
                <span>Start Stream</span>
              </button>
            )}

            <button
              disabled={isProcessing}
              onClick={() => handleStep(5)}
              className="px-3 py-2 rounded border border-slate-200 bg-white text-slate-700 font-medium hover:bg-slate-50 transition flex items-center gap-1"
            >
              <FastForward className="w-3.5 h-3.5 text-slate-500" />
              <span>Step 5</span>
            </button>

            <button
              disabled={isProcessing}
              onClick={handleReset}
              className="px-3 py-2 rounded border border-slate-200 bg-white text-slate-600 font-medium hover:bg-slate-50 transition"
              title="Reset"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Adversary & Attack Injection Deck */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4 text-xs">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-amber-500" />
            <span>Adversary Attack & Anomaly Injection Lab</span>
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Trigger deterministic attack scenarios on-demand to test live security and model defenses
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Attack 1: Astronomical Amount Spike */}
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-2">
            <div>
              <span className="font-semibold text-slate-900 block text-xs">₹150k+ Amount Spike</span>
              <p className="text-[11px] text-slate-500 mt-1">Extreme value outlier exceeding 15x historical baseline.</p>
            </div>
            <button
              disabled={isProcessing}
              onClick={() => handleInject("upi_amount_spike")}
              className="w-full py-1.5 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-[11px]"
            >
              Inject Amount Spike
            </button>
          </div>

          {/* Attack 2: Cryptographic Signature Tamper */}
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-2">
            <div>
              <span className="font-semibold text-rose-700 block text-xs">Ed25519 Signature Tamper</span>
              <p className="text-[11px] text-slate-500 mt-1">Payload bit-flip resulting in cryptographic forgery rejection.</p>
            </div>
            <button
              disabled={isProcessing}
              onClick={() => handleInject("upi_tampered", true)}
              className="w-full py-1.5 rounded bg-rose-600 text-white font-medium hover:bg-rose-700 transition text-[11px]"
            >
              Inject Tampered Sig
            </button>
          </div>

          {/* Attack 3: Rapid Velocity Burst */}
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-2">
            <div>
              <span className="font-semibold text-slate-900 block text-xs">Rapid Velocity Burst</span>
              <p className="text-[11px] text-slate-500 mt-1">Simultaneous rapid succession debits within &lt;1 second.</p>
            </div>
            <button
              disabled={isProcessing}
              onClick={() => handleInject("upi_velocity_burst")}
              className="w-full py-1.5 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-[11px]"
            >
              Inject Velocity Burst
            </button>
          </div>

          {/* Attack 4: Mule Ring Aggregator */}
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-2">
            <div>
              <span className="font-semibold text-slate-900 block text-xs">Mule Ring Dispersal</span>
              <p className="text-[11px] text-slate-500 mt-1">High-risk transfer into active mule aggregation account.</p>
            </div>
            <button
              disabled={isProcessing}
              onClick={() => handleInject("upi_mule_ring")}
              className="w-full py-1.5 rounded bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-[11px]"
            >
              Inject Mule Transfer
            </button>
          </div>
        </div>
      </div>

      {/* Live Stream Terminal Output */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-2 text-xs">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <span className="font-semibold text-slate-900">Live Execution Ledger Snapshot</span>
          <span className="font-mono text-[10px] text-slate-400">
            Total generated: {state.total_generated || 0}
          </span>
        </div>

        <div className="space-y-1.5 max-h-60 overflow-y-auto font-mono text-[11px]">
          {recentEvents.length === 0 ? (
            <div className="py-8 text-center text-slate-400">Ledger empty. Start or step the simulation above.</div>
          ) : (
            recentEvents.map((ev) => {
              const action = ev.action_decision || ev.decision;
              const isBlock = action === "BLOCK" || action === "HIGH_RISK" || action === "INTEGRITY_REJECTED";
              const isReview = action === "REVIEW";
              return (
                <div
                  key={ev.event_id}
                  className="p-2 rounded bg-slate-50 border border-slate-100 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-slate-400">{formatDateTime(ev.timestamp)}</span>
                    <span className="font-bold text-slate-800">{ev.transaction_id || ev.event_id?.slice(0, 8)}</span>
                    <span className="text-slate-600">
                      {ev.sender_id} → {ev.receiver_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-900">{formatCurrencyINR(ev.amount || 0)}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isBlock
                          ? "bg-rose-100 text-rose-800"
                          : isReview
                          ? "bg-amber-100 text-amber-800"
                          : "bg-teal-100 text-teal-800"
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
    </div>
  );
}

