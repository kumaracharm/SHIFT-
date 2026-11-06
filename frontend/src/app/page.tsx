"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/common/Header";
import { Sidebar, NavTab } from "@/components/common/Sidebar";
import { CommandCentre } from "@/components/modules/CommandCentre";
import { LiveTransactions } from "@/components/modules/LiveTransactions";
import { FraudInvestigations } from "@/components/modules/FraudInvestigations";
import { EntityIntelligence } from "@/components/modules/EntityIntelligence";
import { MultiExpertDetection } from "@/components/modules/MultiExpertDetection";
import { AdaptiveResponse } from "@/components/modules/AdaptiveResponse";
import { ModelObservatory } from "@/components/modules/ModelObservatory";
import { DriftAnalytics } from "@/components/modules/DriftAnalytics";
import { SimulationStudio } from "@/components/modules/SimulationStudio";
import { DataSettings } from "@/components/modules/DataSettings";
import { MovingTargetObservatory } from "@/components/modules/MovingTargetObservatory";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/useWebSocket";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>("command_centre");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [liveStreamEvents, setLiveStreamEvents] = useState<any[]>([]);
  const [txFilters, setTxFilters] = useState<{ action?: string; search?: string }>({});

  const queryClient = useQueryClient();

  // Connect to live WebSocket stream
  const { isConnected, lastMessage } = useWebSocket("ws://127.0.0.1:8000/ws/v1/events");

  // When a new transaction arrives via WebSocket, prepend to liveStreamEvents and invalidate queries
  useEffect(() => {
    if (lastMessage && lastMessage.type === "NEW_TRANSACTION") {
      const newTx = lastMessage.data;
      setLiveStreamEvents((prev) => [newTx, ...prev.slice(0, 49)]);
      queryClient.invalidateQueries({ queryKey: ["overviewSummary"] });
      queryClient.invalidateQueries({ queryKey: ["overviewTrends"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    }
  }, [lastMessage, queryClient]);

  // Queries
  const { data: summaryData } = useQuery({
    queryKey: ["overviewSummary"],
    queryFn: api.getOverviewSummary,
    refetchInterval: 3000,
  });

  const { data: trendsData } = useQuery({
    queryKey: ["overviewTrends"],
    queryFn: api.getOverviewTrends,
    refetchInterval: 5000,
  });

  const { data: alertsData } = useQuery({
    queryKey: ["overviewAlerts"],
    queryFn: () => api.getOverviewAlerts(10),
    refetchInterval: 4000,
  });

  const { data: txData } = useQuery({
    queryKey: ["transactions", txFilters],
    queryFn: () => api.getTransactions({ limit: 50, ...txFilters }),
    refetchInterval: 3000,
  });

  const { data: txDetailData } = useQuery({
    queryKey: ["transactionDetail", selectedEventId],
    queryFn: () => (selectedEventId ? api.getTransactionDetail(selectedEventId) : null),
    enabled: !!selectedEventId,
  });

  const { data: casesData } = useQuery({
    queryKey: ["cases"],
    queryFn: api.getCases,
    refetchInterval: 4000,
  });

  const { data: graphData } = useQuery({
    queryKey: ["entityGraph"],
    queryFn: () => api.getEntityGraph(60),
  });

  const { data: expertsData } = useQuery({
    queryKey: ["expertsStatus"],
    queryFn: api.getExpertsStatus,
  });

  const { data: policiesData } = useQuery({
    queryKey: ["policies"],
    queryFn: api.getPolicies,
  });

  const { data: watchlistData } = useQuery({
    queryKey: ["watchlist"],
    queryFn: api.getWatchlist,
  });

  const { data: benchmarkData } = useQuery({
    queryKey: ["benchmark"],
    queryFn: api.getBenchmark,
  });

  const { data: modelHistoryData } = useQuery({
    queryKey: ["modelHistory"],
    queryFn: api.getModelHistory,
  });

  const { data: driftSummaryData } = useQuery({
    queryKey: ["driftSummary"],
    queryFn: api.getDriftSummary,
    refetchInterval: 5000,
  });

  const { data: featureDriftData } = useQuery({
    queryKey: ["featureDrift"],
    queryFn: api.getFeatureDrift,
    refetchInterval: 5000,
  });

  const { data: driftEventsData } = useQuery({
    queryKey: ["driftEvents"],
    queryFn: () => api.getDriftEvents(20),
  });

  const { data: simStateData } = useQuery({
    queryKey: ["simState"],
    queryFn: api.getSimulationState,
    refetchInterval: 2000,
  });

  const { data: scenariosData } = useQuery({
    queryKey: ["scenarios"],
    queryFn: api.getScenarios,
  });

  const { data: healthData } = useQuery({
    queryKey: ["systemHealth"],
    queryFn: api.getSystemHealth,
  });

  const { data: keyData } = useQuery({
    queryKey: ["systemKeys"],
    queryFn: api.getKeys,
  });

  const { data: dbStatsData } = useQuery({
    queryKey: ["systemDbStats"],
    queryFn: api.getDbStats,
    refetchInterval: 5000,
  });

  // Merge live WebSocket events into recent stream
  const allRecentTransactions = [
    ...liveStreamEvents,
    ...(txData?.data || []),
  ].filter(
    (item, index, self) =>
      index === self.findIndex((t) => t.event_id === item.event_id)
  );

  const pendingReviewsCount =
    casesData?.cases?.filter((c: any) => c.analyst_status?.includes("OPEN") || c.system_action === "REVIEW")
      ?.length || 0;

  // Header quick injection handler
  const handleQuickInject = async () => {
    await api.injectAttack("upi_amount_spike", false);
    queryClient.invalidateQueries({ queryKey: ["overviewSummary"] });
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col font-sans">
      {/* Universal Top Header */}
      <Header
        onQuickInject={handleQuickInject}
        isStreaming={isConnected || simStateData?.state?.state === "RUNNING"}
      />

      <div className="flex flex-1">
        {/* Left Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          pendingReviewsCount={pendingReviewsCount}
        />

        {/* Dynamic Main Workspace Container */}
        <main className="flex-1 p-6 overflow-x-hidden max-w-7xl">
          {activeTab === "command_centre" && (
            <CommandCentre
              summary={summaryData}
              trends={trendsData}
              alerts={alertsData?.data || []}
              recentEvents={allRecentTransactions}
              onSelectTransaction={(id) => {
                setSelectedEventId(id);
                setActiveTab("live_transactions");
              }}
              onNavigateToTab={setActiveTab}
            />
          )}

          {activeTab === "live_transactions" && (
            <LiveTransactions
              transactions={txData?.data || []}
              total={txData?.total || 0}
              selectedEventId={selectedEventId}
              selectedTransactionDetail={txDetailData?.data || null}
              onSelectTransaction={setSelectedEventId}
              onFilterChange={setTxFilters}
            />
          )}

          {activeTab === "fraud_investigations" && (
            <FraudInvestigations
              cases={casesData?.cases || []}
              onTakeAction={async (eventId, action, notes) => {
                await api.submitCaseAction(eventId, action, notes);
                queryClient.invalidateQueries({ queryKey: ["cases"] });
              }}
              onSelectTransaction={(id) => {
                setSelectedEventId(id);
                setActiveTab("live_transactions");
              }}
            />
          )}

          {activeTab === "entity_intelligence" && (
            <EntityIntelligence
              graphData={
                graphData || {
                  nodes: [],
                  links: [],
                  categories: [],
                }
              }
            />
          )}

          {activeTab === "multi_expert" && (
            <MultiExpertDetection
              statusData={expertsData}
              onUpdateWeights={async (weights) => {
                const res = await api.updateExpertWeights(weights);
                queryClient.invalidateQueries({ queryKey: ["expertsStatus"] });
                return res;
              }}
              onEvaluatePayload={api.evaluateTransaction}
            />
          )}

          {activeTab === "adaptive_response" && (
            <AdaptiveResponse
              policies={policiesData?.policies || []}
              watchlist={watchlistData?.watchlist || []}
              onSimulatePolicy={api.simulatePolicy}
              onAddToWatchlist={async (id, type, reason) => {
                const res = await api.addToWatchlist(id, type, reason);
                queryClient.invalidateQueries({ queryKey: ["watchlist"] });
                return res;
              }}
            />
          )}

          {activeTab === "model_observatory" && (
            <ModelObservatory
              benchmarkData={benchmarkData}
              modelHistory={modelHistoryData?.models || []}
            />
          )}

          {activeTab === "drift_analytics" && (
            <DriftAnalytics
              driftSummary={driftSummaryData}
              featureDrift={featureDriftData?.features || []}
              driftEvents={driftEventsData?.events || []}
            />
          )}

          {activeTab === "simulation_studio" && (
            <SimulationStudio
              simulationState={simStateData}
              scenarios={scenariosData?.scenarios || []}
              recentEvents={allRecentTransactions}
              onStartSimulation={async (sc, sp) => {
                const res = await api.startSimulation(sc, sp);
                queryClient.invalidateQueries({ queryKey: ["simState"] });
                return res;
              }}
              onPauseSimulation={async () => {
                const res = await api.pauseSimulation();
                queryClient.invalidateQueries({ queryKey: ["simState"] });
                return res;
              }}
              onStepSimulation={async (cnt, sc) => {
                const res = await api.stepSimulation(cnt, sc);
                queryClient.invalidateQueries({ queryKey: ["simState"] });
                queryClient.invalidateQueries({ queryKey: ["transactions"] });
                return res;
              }}
              onInjectAttack={async (sc, tamper) => {
                const res = await api.injectAttack(sc, tamper);
                queryClient.invalidateQueries({ queryKey: ["simState"] });
                queryClient.invalidateQueries({ queryKey: ["transactions"] });
                return res;
              }}
              onResetSimulation={async () => {
                const res = await api.resetSimulation();
                queryClient.invalidateQueries({ queryKey: ["simState"] });
                return res;
              }}
            />
          )}

          {activeTab === "moving_target_observatory" && (
            <MovingTargetObservatory />
          )}

          {activeTab === "data_settings" && (
            <DataSettings
              systemHealth={healthData}
              keyStatus={keyData}
              dbStats={dbStatsData}
            />
          )}
        </main>
      </div>
    </div>
  );
}

