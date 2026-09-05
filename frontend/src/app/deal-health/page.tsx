"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Zap,
  Filter,
  RefreshCw,
  Search,
  ChevronRight,
  BellRing,
  AlertCircle,
  BarChart3,
  HeartPulse,
} from "lucide-react";

import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { dealHealthApi } from "@/lib/api";
import {
  DealHealthAlertResponse,
  DealHealthClassification,
  DealHealthDashboardResponse,
  DealHealthPredictionResponse,
  DealHealthRecommendationResponse,
  RankedDealHealthItem,
} from "@/types/dealHealth";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";

export default function DealHealthPage() {
  const { user } = useAuth();
  const toast = useToast();

  const allowedRoles = ["Sales Representative", "Sales Manager", "Admin", "Executive"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  const [dashboard, setDashboard] = useState<DealHealthDashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Selected Deal Detail Modal
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [selectedDealHealth, setSelectedDealHealth] = useState<DealHealthPredictionResponse | null>(null);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const dash = await dealHealthApi.getDashboard();
      setDashboard(dash);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load Deal Health Dashboard metrics.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    if (hasAccess) {
      loadData();
    }
  }, [loadData, hasAccess]);

  const openDealHealthModal = async (dealId: string) => {
    setSelectedDealId(dealId);
    setModalLoading(true);
    try {
      const health = await dealHealthApi.getHealth(dealId);
      setSelectedDealHealth(health);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load deal health details.");
    } finally {
      setModalLoading(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await dealHealthApi.acknowledgeAlert(alertId);
      toast.success("Alert acknowledged successfully");
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Failed to acknowledge alert.");
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await dealHealthApi.resolveAlert(alertId);
      toast.success("Alert resolved successfully");
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Failed to resolve alert.");
    }
  };

  const getClassificationBadgeVariant = (classification: string) => {
    switch (classification) {
      case "HEALTHY":
        return "success";
      case "WATCH":
        return "secondary";
      case "AT_RISK":
        return "warning";
      case "CRITICAL":
        return "destructive";
      default:
        return "outline";
    }
  };

  if (!hasAccess) {
    return (
      <ProtectedRoute>
        <UnauthorizedState />
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <HeartPulse className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">Deal Health Engine</h1>
                <p className="text-sm text-muted-foreground">
                  Monitor deal momentum, operational health, behavioral anomalies, and automated intervention (Phases 211–230).
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={isRefreshing}
              onClick={() => {
                setIsRefreshing(true);
                loadData();
              }}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh Dashboard
            </Button>
          </div>
        </div>

        {loading ? (
          <LoadingState message="Evaluating real-time deal health and anomalies..." />
        ) : !dashboard ? (
          <EmptyState
            icon={HeartPulse}
            title="No Deal Health Data"
            description="Unable to aggregate deal health metrics. Please ensure deals exist in the system."
          />
        ) : (
          <>
            {/* KPI Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">Active Deals</span>
                <p className="text-2xl font-bold mt-2 text-foreground">{dashboard.summary.total_active_deals}</p>
                <p className="text-xs text-muted-foreground mt-1">Under evaluation</p>
              </Card>

              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">Avg Health Score</span>
                <p className="text-2xl font-bold mt-2 text-blue-600">{dashboard.summary.avg_health_score}/100</p>
                <p className="text-xs text-muted-foreground mt-1">Overall pipeline momentum</p>
              </Card>

              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">Healthy Deals</span>
                <p className="text-2xl font-bold mt-2 text-emerald-600">{dashboard.summary.healthy_deals_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Score 80–100</p>
              </Card>

              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">At-Risk Deals</span>
                <p className="text-2xl font-bold mt-2 text-amber-500">{dashboard.summary.at_risk_deals_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Score 40–59</p>
              </Card>

              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">Critical Deals</span>
                <p className="text-2xl font-bold mt-2 text-rose-600">{dashboard.summary.critical_deals_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Score 0–39</p>
              </Card>

              <Card className="p-4 bg-card border">
                <span className="text-xs font-medium text-muted-foreground uppercase">Open Alerts</span>
                <p className="text-2xl font-bold mt-2 text-purple-600">{dashboard.summary.open_alerts_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Requires intervention</p>
              </Card>
            </div>

            {/* Health Distribution & Risk Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="p-5 border lg:col-span-2">
                <h3 className="text-sm font-semibold text-foreground mb-4">Pipeline Health Distribution & Risk Averages</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-center">
                    <span className="text-xs font-semibold text-emerald-700">Healthy</span>
                    <p className="text-xl font-bold text-emerald-600 mt-1">{dashboard.health_distribution.HEALTHY || 0}</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-center">
                    <span className="text-xs font-semibold text-blue-700">Watch</span>
                    <p className="text-xl font-bold text-blue-600 mt-1">{dashboard.health_distribution.WATCH || 0}</p>
                  </div>
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-center">
                    <span className="text-xs font-semibold text-amber-700">At Risk</span>
                    <p className="text-xl font-bold text-amber-600 mt-1">{dashboard.health_distribution.AT_RISK || 0}</p>
                  </div>
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-center">
                    <span className="text-xs font-semibold text-rose-700">Critical</span>
                    <p className="text-xl font-bold text-rose-600 mt-1">{dashboard.health_distribution.CRITICAL || 0}</p>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                  <div>
                    <span className="text-xs text-muted-foreground">Avg Conversion Prob</span>
                    <p className="text-lg font-bold text-emerald-600">{(dashboard.summary.avg_conversion_probability * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Avg Stall Prob</span>
                    <p className="text-lg font-bold text-amber-600">{(dashboard.summary.avg_stall_probability * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Avg Delay Prob</span>
                    <p className="text-lg font-bold text-rose-600">{(dashboard.summary.avg_delay_probability * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </Card>

              {/* Anomaly Center */}
              <Card className="p-5 border space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">Anomaly Center</h3>
                  <Badge variant="outline">{dashboard.summary.total_anomalies_count} Detected</Badge>
                </div>
                <div className="space-y-3">
                  <div className="p-3 bg-muted/30 border rounded-lg flex items-center justify-between">
                    <span className="text-xs font-medium">Discount Anomalies</span>
                    <span className="text-xs font-bold text-amber-600">{dashboard.discount_anomalies.length} deals</span>
                  </div>
                  <div className="p-3 bg-muted/30 border rounded-lg flex items-center justify-between">
                    <span className="text-xs font-medium">Approval Bottlenecks</span>
                    <span className="text-xs font-bold text-purple-600">{dashboard.approval_bottlenecks.length} deals</span>
                  </div>
                  <div className="p-3 bg-muted/30 border rounded-lg flex items-center justify-between">
                    <span className="text-xs font-medium">Delivery Slippage Risks</span>
                    <span className="text-xs font-bold text-rose-600">{dashboard.delivery_risks.length} deals</span>
                  </div>
                  <div className="p-3 bg-muted/30 border rounded-lg flex items-center justify-between">
                    <span className="text-xs font-medium">Stalled Deals</span>
                    <span className="text-xs font-bold text-blue-600">{dashboard.stalled_deals.length} deals</span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Critical & At-Risk Deals Table */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                Critical & At-Risk Deals Attention Required
              </h3>
              <div className="border rounded-lg overflow-hidden bg-card">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/50 text-muted-foreground font-semibold uppercase border-b">
                      <tr>
                        <th className="px-4 py-3">Deal</th>
                        <th className="px-4 py-3">Customer</th>
                        <th className="px-4 py-3">Stage</th>
                        <th className="px-4 py-3 text-right">Deal Value</th>
                        <th className="px-4 py-3 text-center">Health Score</th>
                        <th className="px-4 py-3 text-center">Status</th>
                        <th className="px-4 py-3">Primary Risk Factor</th>
                        <th className="px-4 py-3 text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {[...dashboard.critical_deals, ...dashboard.at_risk_deals].length === 0 ? (
                        <tr>
                          <td colSpan={8} className="text-center py-6 text-muted-foreground">
                            No deals currently classified as Critical or At-Risk.
                          </td>
                        </tr>
                      ) : (
                        [...dashboard.critical_deals, ...dashboard.at_risk_deals].map((item) => (
                          <tr key={item.deal_id} className="hover:bg-muted/20 transition-colors">
                            <td className="px-4 py-3 font-mono font-semibold text-primary">{item.deal_code}</td>
                            <td className="px-4 py-3 font-medium">{item.customer_name}</td>
                            <td className="px-4 py-3">{item.stage}</td>
                            <td className="px-4 py-3 text-right font-semibold">${item.deal_value.toLocaleString()}</td>
                            <td className="px-4 py-3 text-center font-bold text-sm">{item.health_score}</td>
                            <td className="px-4 py-3 text-center">
                              <Badge variant={getClassificationBadgeVariant(item.classification)}>
                                {item.classification}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-muted-foreground">{item.primary_risk}</td>
                            <td className="px-4 py-3 text-center">
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-[11px]"
                                onClick={() => openDealHealthModal(item.deal_id)}
                              >
                                View Health
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Alert Center */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <BellRing className="h-4 w-4 text-purple-500" />
                Active Deal Health Alerts ({dashboard.open_alerts.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboard.open_alerts.length === 0 ? (
                  <Card className="p-4 text-center text-xs text-muted-foreground col-span-2">
                    No active deal health alerts.
                  </Card>
                ) : (
                  dashboard.open_alerts.map((alert) => (
                    <Card key={alert.id} className="p-4 border space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={alert.severity === "CRITICAL" ? "destructive" : "warning"}>
                            {alert.severity}
                          </Badge>
                          <span className="font-semibold text-xs text-foreground">{alert.title}</span>
                        </div>
                        <span className="text-[11px] text-muted-foreground font-mono">
                          Score: {alert.health_score}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">{alert.description}</p>
                      {alert.recommended_action && (
                        <p className="text-[11px] text-primary font-medium">
                          Suggested Action: {alert.recommended_action}
                        </p>
                      )}
                      <div className="flex items-center justify-end gap-2 pt-2 border-t">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-[11px]"
                          onClick={() => handleAcknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-[11px]"
                          onClick={() => handleResolveAlert(alert.id)}
                        >
                          Resolve
                        </Button>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>

            {/* Deal Health Detail Modal */}
            <Modal
              isOpen={!!selectedDealId}
              onClose={() => setSelectedDealId(null)}
              title="Deal Health Deep-Dive & Explainability"
              className="max-w-3xl"
            >
              {modalLoading ? (
                <LoadingState message="Running deterministic health evaluation..." />
              ) : selectedDealHealth ? (
                <div className="space-y-5">
                  <div className="p-4 bg-muted/30 border rounded-lg flex items-center justify-between">
                    <div>
                      <span className="text-xs text-muted-foreground uppercase">Unified Deal Health Score</span>
                      <p className="text-3xl font-extrabold text-primary">{selectedDealHealth.health_score}/100</p>
                    </div>
                    <Badge variant={getClassificationBadgeVariant(selectedDealHealth.classification)} className="text-sm px-3 py-1">
                      {selectedDealHealth.classification}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-emerald-700">Conversion Prob</span>
                      <p className="text-lg font-bold text-emerald-600">{selectedDealHealth.conversion_percentage}%</p>
                    </div>
                    <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-amber-700">Stall Risk</span>
                      <p className="text-lg font-bold text-amber-600">{selectedDealHealth.stall_percentage}% ({selectedDealHealth.stall_risk_level})</p>
                    </div>
                    <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-rose-700">Delay Risk</span>
                      <p className="text-lg font-bold text-rose-600">{selectedDealHealth.delay_percentage}% ({selectedDealHealth.delay_risk_level})</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">Primary Risk Factors:</h4>
                    {selectedDealHealth.primary_risk_factors.map((rf, i) => (
                      <div key={i} className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded text-xs text-rose-700 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        <span>{rf}</span>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">Positive Signals:</h4>
                    {selectedDealHealth.positive_factors.map((pf, i) => (
                      <div key={i} className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded text-xs text-emerald-700 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                        <span>{pf}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </Modal>
          </>
        )}
      </div>
    </ProtectedRoute>
  );
}
