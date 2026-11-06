"use client";

import React from "react";
import { Settings, ShieldCheck, Database, HardDrive, Key, ExternalLink, CheckCircle } from "lucide-react";

interface DataSettingsProps {
  systemHealth: any;
  keyStatus: any;
  dbStats: any;
}

export function DataSettings({ systemHealth, keyStatus, dbStats }: DataSettingsProps) {
  const counts = dbStats?.counts || {};

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">Data & System Infrastructure Settings</h1>
        <p className="text-xs text-slate-500">
          Hardware deployment status, SQLite storage metrics, cryptographic key registry, and dataset provenance
        </p>
      </div>

      {/* Grid: 3 Infrastructure Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: System Health */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="font-semibold text-slate-900 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              <span>Platform Health</span>
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
              {systemHealth?.status?.toUpperCase() || "HEALTHY"}
            </span>
          </div>
          <div className="space-y-2 text-slate-600">
            <div className="flex justify-between">
              <span>Environment:</span>
              <span className="font-semibold text-slate-800">Production / SOC Lab</span>
            </div>
            <div className="flex justify-between">
              <span>Architecture:</span>
              <span className="font-semibold text-slate-800">CPU-First Local Windows</span>
            </div>
            <div className="flex justify-between">
              <span>Database Connection:</span>
              <span className="font-bold text-teal-700">ONLINE</span>
            </div>
            <div className="flex justify-between">
              <span>FastAPI Endpoints:</span>
              <span className="font-bold text-slate-800">10 Routers Mounted</span>
            </div>
          </div>
        </div>

        {/* Card 2: Cryptographic Security */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="font-semibold text-slate-900 flex items-center gap-1.5">
              <Key className="w-4 h-4 text-slate-600" />
              <span>Cryptographic Registry</span>
            </h2>
            <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
              Ed25519
            </span>
          </div>
          <div className="space-y-2 text-slate-600">
            <div className="flex justify-between">
              <span>Default Key ID:</span>
              <span className="font-mono font-bold text-slate-800 text-[11px] truncate max-w-[150px]">
                {keyStatus?.default_key_id}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Public Key Present:</span>
              <span className="font-bold text-teal-700">{keyStatus?.public_key_present ? "YES" : "NO"}</span>
            </div>
            <div className="flex justify-between">
              <span>Private Key Present:</span>
              <span className="font-bold text-teal-700">{keyStatus?.private_key_present ? "YES" : "NO"}</span>
            </div>
            <div className="flex justify-between">
              <span>Replay Cache Window:</span>
              <span className="font-mono font-semibold text-slate-800">300 seconds</span>
            </div>
          </div>
        </div>

        {/* Card 3: SQLite Storage Volume */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="font-semibold text-slate-900 flex items-center gap-1.5">
              <HardDrive className="w-4 h-4 text-blue-600" />
              <span>Storage Footprint</span>
            </h2>
            <span className="font-mono text-[10px] font-bold text-slate-700">
              {dbStats?.size_mb || 0} MB
            </span>
          </div>
          <div className="space-y-2 text-slate-600">
            <div className="flex justify-between">
              <span>Database Engine:</span>
              <span className="font-semibold text-slate-800">SQLite 3 (WAL mode)</span>
            </div>
            <div className="flex justify-between">
              <span>File:</span>
              <span className="font-mono text-[10px] text-slate-700 truncate max-w-[170px]">
                driftguard.db
              </span>
            </div>
            <div className="flex justify-between">
              <span>Total Transactions:</span>
              <span className="font-mono font-bold text-slate-900">{counts.events?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Predictions:</span>
              <span className="font-mono font-bold text-slate-900">{counts.predictions?.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Table Storage Breakdown */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
        <h2 className="font-semibold text-slate-900 text-xs border-b border-slate-100 pb-2">
          SQLite Table Row Distribution & Audit Logs
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 text-center">
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">events</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.events || 0}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">predictions</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.predictions || 0}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">integrity_logs</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.integrity_logs || 0}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">replay_cache</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.replay_cache || 0}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">drift_events</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.drift_events || 0}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-100">
            <span className="text-[10px] text-slate-400 font-bold uppercase">model_versions</span>
            <div className="text-base font-bold font-mono text-slate-900 mt-1">{counts.model_versions || 0}</div>
          </div>
        </div>
      </div>

      {/* Dataset & MCP Provenance */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3 text-xs">
        <h2 className="font-semibold text-slate-900 text-xs border-b border-slate-100 pb-2">
          Dataset Provenance & Kaggle MCP Integration
        </h2>
        <div className="space-y-2 text-slate-600">
          <p>
            Supervised fraud detection is benchmarked using the authentic <strong>IEEE-CIS Fraud Detection</strong> dataset (downloaded via Kaggle MCP / API credentials to <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-800">data/raw/ieee_cis/</code>).
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
            <div className="p-2.5 rounded bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-800 block text-[11px]">Training Split:</span>
              <span className="text-[10px] text-slate-500">70,000 chronological transactions (TransactionDT)</span>
            </div>
            <div className="p-2.5 rounded bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-800 block text-[11px]">Holdout Validation:</span>
              <span className="text-[10px] text-slate-500">15,000 uncorrupted holdout transactions (ROC-AUC: 0.8954)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

