"use client";

import React, { useState, useEffect } from "react";
import { Shield, Radio, ExternalLink, Zap } from "lucide-react";

interface HeaderProps {
  onQuickInject?: () => void;
  isStreaming?: boolean;
}

export function Header({ onQuickInject, isStreaming = false }: HeaderProps) {
  const [timeUtc, setTimeUtc] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeUtc(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand Identity */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-slate-950 via-slate-900 to-indigo-900 flex items-center justify-center text-white shadow-sm ring-1 ring-slate-800/20">
          <Shield className="w-4 h-4 text-indigo-400" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-900 tracking-tight text-base font-sans">
              SHIFT
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-indigo-50 text-indigo-700 border border-indigo-200/60 tracking-wide uppercase">
              Adaptive Intelligence
            </span>
          </div>
          <p className="text-[10px] text-slate-500 font-medium">
            Streaming Fraud &amp; Moving-Target Threat Tracking
          </p>
        </div>
      </div>

      {/* Real-time Status and Actions */}
      <div className="flex items-center gap-4">
        {/* UTC Clock */}
        <div className="text-xs font-mono text-slate-500 hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          <span>{timeUtc}</span>
        </div>

        {/* Quick Scenario Inject Button */}
        {onQuickInject && (
          <button
            onClick={onQuickInject}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 transition shadow-xs"
          >
            <Zap className="w-3.5 h-3.5 text-amber-300" />
            <span>Simulate Anomaly</span>
          </button>
        )}

        {/* API Docs Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-md hover:bg-slate-100 transition border border-transparent hover:border-slate-200"
        >
          <span>API Docs</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>
      </div>
    </header>
  );
}

