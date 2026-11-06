"use client";

import React from "react";
import {
  LayoutDashboard,
  Activity,
  FileSearch,
  Network,
  Cpu,
  ShieldAlert,
  Microscope,
  GitCompare,
  Sliders,
  Crosshair,
  Settings,
} from "lucide-react";

export type NavTab =
  | "command_centre"
  | "live_transactions"
  | "fraud_investigations"
  | "entity_intelligence"
  | "multi_expert"
  | "adaptive_response"
  | "model_observatory"
  | "drift_analytics"
  | "simulation_studio"
  | "moving_target_observatory"
  | "data_settings";

interface SidebarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  pendingReviewsCount?: number;
}

const NAV_ITEMS: { id: NavTab; label: string; icon: React.ComponentType<{ className?: string }>; badgeKey?: "reviews"; badgeColor?: string }[] = [
  { id: "command_centre", label: "Command Centre", icon: LayoutDashboard },
  { id: "moving_target_observatory", label: "Moving Target Lab", icon: Crosshair },
  { id: "live_transactions", label: "Live Transactions", icon: Activity },
  { id: "fraud_investigations", label: "Fraud Investigations", icon: FileSearch, badgeKey: "reviews" },
  { id: "drift_analytics", label: "Drift Analytics", icon: GitCompare },
  { id: "multi_expert", label: "Multi-Expert Detection", icon: Cpu },
  { id: "entity_intelligence", label: "Entity Intelligence", icon: Network },
  { id: "adaptive_response", label: "Adaptive Response", icon: ShieldAlert },
  { id: "simulation_studio", label: "Simulation Studio", icon: Sliders },
  { id: "model_observatory", label: "Model Observatory", icon: Microscope },
  { id: "data_settings", label: "Data & System Settings", icon: Settings },
];

export function Sidebar({ activeTab, onTabChange, pendingReviewsCount = 0 }: SidebarProps) {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between shrink-0 h-[calc(100vh-3.5rem)] sticky top-14">
      <div className="p-3 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Intelligence Modules
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const isMovingTarget = item.id === "moving_target_observatory";
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                isActive
                  ? "bg-slate-900 text-white shadow-sm"
                  : isMovingTarget
                  ? "text-indigo-700 bg-indigo-50/60 hover:bg-indigo-50 font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 ${
                    isActive
                      ? "text-indigo-400"
                      : isMovingTarget
                      ? "text-indigo-600"
                      : "text-slate-400"
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badgeKey === "reviews" && pendingReviewsCount > 0 && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isActive ? "bg-amber-400 text-slate-900" : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {pendingReviewsCount}
                </span>
              )}
              {isMovingTarget && !isActive && (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-indigo-100 text-indigo-700 uppercase">
                  Primary
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Modern Status Footer */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50 space-y-1.5">
        <div className="text-[11px] text-slate-500 flex justify-between items-center">
          <span>SHIFT Detection</span>
          <span className="font-semibold text-emerald-600 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
            7 Experts Active
          </span>
        </div>
        <div className="text-[10px] text-slate-400 flex justify-between items-center">
          <span>Drift Strategy</span>
          <span className="font-mono text-indigo-600 font-semibold">ADWIN + PSI</span>
        </div>
      </div>
    </aside>
  );
}

