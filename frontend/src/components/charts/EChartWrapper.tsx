"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Dynamically import ReactECharts with SSR disabled
const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface EChartWrapperProps {
  option: any;
  style?: React.CSSProperties;
  className?: string;
  onEvents?: Record<string, (param: any) => void>;
}

export function EChartWrapper({ option, style = { height: "300px", width: "100%" }, className, onEvents }: EChartWrapperProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        style={style}
        className={`flex items-center justify-center bg-slate-50 border border-slate-100 rounded text-slate-400 text-xs ${className}`}
      >
        Loading visualization...
      </div>
    );
  }

  return (
    <div className={className}>
      <ReactECharts
        option={option}
        style={style}
        onEvents={onEvents}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}

