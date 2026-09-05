"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Briefcase,
  TrendingUp,
  DollarSign,
  Percent,
  Layers,
  Search,
  Filter,
  RefreshCw,
  Plus,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  Send,
  FileText,
  Activity,
  ArrowRight,
} from "lucide-react";

import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { dealsApi } from "@/lib/api";
import {
  DealDashboardResponse,
  DealDetail,
  DealMarginResponse,
  DealProbabilityResponse,
  DealStage,
  DealSummary,
  DealTimelineEvent,
  StageForecastItem,
} from "@/types/deal";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Modal } from "@/components/ui/modal";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";

export default function DealsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const allowedRoles = ["Sales Representative", "Sales Manager", "Admin", "Executive"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  // Dashboard & List State
  const [dashboard, setDashboard] = useState<DealDashboardResponse | null>(null);
  const [deals, setDeals] = useState<DealSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [stageFilter, setStageFilter] = useState<string>("ALL");

  // Selected Deal Detail Modal
  const [selectedDeal, setSelectedDeal] = useState<DealDetail | null>(null);
  const [dealLoading, setDealLoading] = useState<boolean>(false);
  const [probabilityData, setProbabilityData] = useState<DealProbabilityResponse | null>(null);
  const [marginData, setMarginData] = useState<DealMarginResponse | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<DealTimelineEvent[]>([]);
  const [activeDetailTab, setActiveDetailTab] = useState<"overview" | "products" | "probability" | "timeline">("overview");

  // Stage Transition State
  const [transitioningStage, setTransitioningStage] = useState<boolean>(false);
  const [stageReason, setStageReason] = useState<string>("");

  // Activity Log State
  const [activityTitle, setActivityTitle] = useState<string>("");
  const [activityType, setActivityType] = useState<string>("NOTE");
  const [activityNotes, setActivityNotes] = useState<string>("");
  const [submittingActivity, setSubmittingActivity] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const [dashRes, listRes] = await Promise.all([
        dealsApi.getDashboard().catch(() => null),
        dealsApi.listDeals({
          stage: stageFilter === "ALL" ? undefined : stageFilter,
          search: searchTerm || undefined,
        }),
      ]);
      if (dashRes) setDashboard(dashRes);
      setDeals(listRes || []);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load deal pipeline data.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [stageFilter, searchTerm, toast]);

  useEffect(() => {
    if (hasAccess) {
      loadData();
    }
  }, [loadData, hasAccess]);

  const openDealDetail = async (dealId: string) => {
    setDealLoading(true);
    try {
      const [detail, prob, margin, timeline] = await Promise.all([
        dealsApi.getDeal(dealId),
        dealsApi.getProbability(dealId).catch(() => null),
        dealsApi.getMargin(dealId).catch(() => null),
        dealsApi.getTimeline(dealId).catch(() => []),
      ]);
      setSelectedDeal(detail);
      setProbabilityData(prob);
      setMarginData(margin);
      setTimelineEvents(timeline);
      setActiveDetailTab("overview");
    } catch (err: any) {
      toast.error(err?.message || "Failed to load deal details.");
    } finally {
      setDealLoading(false);
    }
  };

  const handleStageTransition = async (newStage: DealStage) => {
    if (!selectedDeal) return;
    setTransitioningStage(true);
    try {
      const updated = await dealsApi.updateStage(selectedDeal.id, {
        stage: newStage,
        reason: stageReason || undefined,
      });
      setSelectedDeal(updated);
      setStageReason("");
      toast.success(`Deal transitioned to ${newStage}`);
      loadData();
      // refresh probability and timeline
      const [prob, timeline] = await Promise.all([
        dealsApi.getProbability(selectedDeal.id).catch(() => null),
        dealsApi.getTimeline(selectedDeal.id).catch(() => []),
      ]);
      setProbabilityData(prob);
      setTimelineEvents(timeline);
    } catch (err: any) {
      toast.error(err?.message || "Failed to transition deal stage.");
    } finally {
      setTransitioningStage(false);
    }
  };

  const handleLogActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeal || !activityTitle) return;
    setSubmittingActivity(true);
    try {
      await dealsApi.logActivity(selectedDeal.id, {
        activity_type: activityType as any,
        title: activityTitle,
        description: activityNotes || undefined,
      });
      toast.success("Activity logged successfully");
      setActivityTitle("");
      setActivityNotes("");
      const timeline = await dealsApi.getTimeline(selectedDeal.id);
      setTimelineEvents(timeline);
    } catch (err: any) {
      toast.error(err?.message || "Failed to log activity.");
    } finally {
      setSubmittingActivity(false);
    }
  };

  const getStageBadgeVariant = (stage: string) => {
    switch (stage) {
      case "CLOSED_WON":
        return "success";
      case "CLOSED_LOST":
        return "destructive";
      case "NEGOTIATION":
        return "warning";
      case "PROPOSAL":
        return "default";
      case "QUALIFIED":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getMarginBadgeVariant = (risk?: string) => {
    switch (risk) {
      case "HEALTHY":
        return "success";
      case "MODERATE":
        return "default";
      case "THIN":
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
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <Briefcase className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">Deal Pipeline & Management</h1>
                <p className="text-sm text-muted-foreground">
                  Continuous deal velocity, margin governance, deterministic win probability, and unified timelines (Phases 206–215).
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
              Refresh
            </Button>
          </div>
        </div>

        {/* Executive KPI Overview (Phase 215) */}
        {dashboard && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="p-4 bg-card border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground uppercase">Pipeline Value</span>
                <DollarSign className="h-4 w-4 text-primary" />
              </div>
              <p className="text-2xl font-bold mt-2 text-foreground">
                ${Number(dashboard.pipeline_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{dashboard.open_deals} open deals in pipeline</p>
            </Card>

            <Card className="p-4 bg-card border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground uppercase">Expected Revenue</span>
                <TrendingUp className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="text-2xl font-bold mt-2 text-foreground">
                ${Number(dashboard.expected_revenue || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-muted-foreground mt-1">Weighted probability forecast</p>
            </Card>

            <Card className="p-4 bg-card border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground uppercase">Win Rate</span>
                <Percent className="h-4 w-4 text-blue-500" />
              </div>
              <p className="text-2xl font-bold mt-2 text-foreground">{dashboard.win_rate.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                {dashboard.won_deals} won / {dashboard.won_deals + dashboard.lost_deals} resolved
              </p>
            </Card>

            <Card className="p-4 bg-card border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground uppercase">Average Deal Size</span>
                <Layers className="h-4 w-4 text-purple-500" />
              </div>
              <p className="text-2xl font-bold mt-2 text-foreground">
                ${Number(dashboard.average_deal_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-muted-foreground mt-1">Across all {dashboard.total_deals} deals</p>
            </Card>

            <Card className="p-4 bg-card border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground uppercase">Active Velocity</span>
                <Activity className="h-4 w-4 text-amber-500" />
              </div>
              <p className="text-2xl font-bold mt-2 text-foreground">{dashboard.recent_activities.length}</p>
              <p className="text-xs text-muted-foreground mt-1">Recent sales touchpoints</p>
            </Card>
          </div>
        )}

        {/* Pipeline Stage Distribution (Phase 212 & 215) */}
        {dashboard && dashboard.deals_by_stage && (
          <Card className="p-5 border">
            <h3 className="text-sm font-semibold text-foreground mb-3">Pipeline Stage Distribution</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {dashboard.deals_by_stage.map((stg: StageForecastItem) => (
                <div key={stg.stage} className="p-3 bg-muted/40 rounded-lg border">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold">{stg.stage}</span>
                    <Badge variant={getStageBadgeVariant(stg.stage)} className="text-[10px] py-0 px-1.5">
                      {stg.deal_count}
                    </Badge>
                  </div>
                  <p className="text-sm font-bold text-foreground">
                    ${Number(stg.total_value || 0).toLocaleString(undefined, { minimumFractionDigits: 0 })}
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Wtd: ${Number(stg.weighted_value || 0).toLocaleString(undefined, { minimumFractionDigits: 0 })}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Filters & Actions */}
        <Card className="p-4 border">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search deals by code, customer, or title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Select
                value={stageFilter}
                onChange={(e) => setStageFilter(e.target.value)}
                className="w-full sm:w-44"
              >
                <option value="ALL">All Stages</option>
                <option value="NEW">NEW</option>
                <option value="QUALIFIED">QUALIFIED</option>
                <option value="PROPOSAL">PROPOSAL</option>
                <option value="NEGOTIATION">NEGOTIATION</option>
                <option value="CLOSED_WON">CLOSED WON</option>
                <option value="CLOSED_LOST">CLOSED LOST</option>
              </Select>
            </div>
          </div>
        </Card>

        {/* Deals Listing Table */}
        {loading ? (
          <LoadingState message="Loading commercial deals pipeline..." />
        ) : deals.length === 0 ? (
          <EmptyState
            icon={Briefcase}
            title="No Deals Found"
            description={
              searchTerm || stageFilter !== "ALL"
                ? "No deals matched your selected filter criteria."
                : "No deals have been created yet. Convert accepted quotations or create deals to populate pipeline."
            }
          />
        ) : (
          <div className="border rounded-lg overflow-hidden bg-card">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-xs font-semibold text-muted-foreground uppercase border-b">
                  <tr>
                    <th className="px-4 py-3">Deal Code</th>
                    <th className="px-4 py-3">Title & Customer</th>
                    <th className="px-4 py-3">Stage</th>
                    <th className="px-4 py-3 text-right">Deal Value</th>
                    <th className="px-4 py-3 text-center">Probability</th>
                    <th className="px-4 py-3 text-right">Expected Revenue</th>
                    <th className="px-4 py-3 text-right">Margin %</th>
                    <th className="px-4 py-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {deals.map((deal) => (
                    <tr
                      key={deal.id}
                      className="hover:bg-muted/20 transition-colors cursor-pointer"
                      onClick={() => openDealDetail(deal.id)}
                    >
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-primary">
                        {deal.deal_code}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">{deal.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {deal.customer_name || "Direct Customer"}
                          {deal.quotation_number && ` • Quote: ${deal.quotation_number}`}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={getStageBadgeVariant(deal.stage)}>{deal.stage}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">
                        ${Number(deal.deal_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="inline-flex items-center gap-1 font-semibold text-xs">
                          <span>{deal.probability}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600 font-semibold">
                        ${Number(deal.expected_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`font-semibold text-xs ${
                            Number(deal.margin_percentage) < 10
                              ? "text-rose-500"
                              : Number(deal.margin_percentage) < 25
                              ? "text-amber-500"
                              : "text-emerald-600"
                          }`}
                        >
                          {Number(deal.margin_percentage).toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDealDetail(deal.id)}
                          className="h-8 px-2 text-xs"
                        >
                          View Detail <ChevronRight className="h-3 w-3 ml-1" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Detailed Deal Inspection Modal */}
        <Modal
          isOpen={!!selectedDeal}
          onClose={() => setSelectedDeal(null)}
          title={selectedDeal ? `${selectedDeal.deal_code} — ${selectedDeal.title}` : "Deal Details"}
          className="max-w-4xl"
        >
          {dealLoading ? (
            <LoadingState message="Loading detailed deal metrics..." />
          ) : selectedDeal ? (
            <div className="space-y-6">
              {/* Header Overview Banner */}
              <div className="p-4 bg-muted/30 border rounded-lg flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant={getStageBadgeVariant(selectedDeal.stage)} className="text-xs px-2 py-0.5">
                      {selectedDeal.stage}
                    </Badge>
                    <Badge variant="outline" className="text-xs font-mono">
                      Status: {selectedDeal.status}
                    </Badge>
                    {marginData && (
                      <Badge variant={getMarginBadgeVariant(marginData.margin_risk)} className="text-xs">
                        Margin: {marginData.margin_risk}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Rep: {selectedDeal.sales_rep_name || "Assigned Rep"} • Customer: {selectedDeal.customer_name || "Direct Customer"}
                  </p>
                </div>

                <div className="flex items-center gap-4 text-right">
                  <div>
                    <span className="text-xs text-muted-foreground">Deal Value</span>
                    <p className="text-xl font-bold text-foreground">
                      ${Number(selectedDeal.deal_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Probability</span>
                    <p className="text-xl font-bold text-blue-600">{selectedDeal.probability}%</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Expected Rev</span>
                    <p className="text-xl font-bold text-emerald-600">
                      ${Number(selectedDeal.expected_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              </div>

              {/* Stage Transition Control */}
              {selectedDeal.stage !== "CLOSED_WON" && (
                <div className="p-4 bg-card border rounded-lg flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-foreground">Transition Stage:</span>
                    <Input
                      placeholder="Transition reason / rationale..."
                      value={stageReason}
                      onChange={(e) => setStageReason(e.target.value)}
                      className="h-8 text-xs w-64"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedDeal.stage === "NEW" && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={transitioningStage}
                        onClick={() => handleStageTransition("QUALIFIED")}
                      >
                        Advance to Qualified
                      </Button>
                    )}
                    {selectedDeal.stage === "QUALIFIED" && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={transitioningStage}
                        onClick={() => handleStageTransition("PROPOSAL")}
                      >
                        Advance to Proposal
                      </Button>
                    )}
                    {selectedDeal.stage === "PROPOSAL" && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={transitioningStage}
                        onClick={() => handleStageTransition("NEGOTIATION")}
                      >
                        Advance to Negotiation
                      </Button>
                    )}
                    {selectedDeal.stage === "NEGOTIATION" && (
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={transitioningStage}
                        onClick={() => handleStageTransition("CLOSED_WON")}
                      >
                        Mark as WON
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="destructive"
                      disabled={transitioningStage}
                      onClick={() => handleStageTransition("CLOSED_LOST")}
                    >
                      Mark as LOST
                    </Button>
                  </div>
                </div>
              )}

              {/* Tabs Navigation */}
              <div className="flex border-b text-sm font-medium">
                <button
                  onClick={() => setActiveDetailTab("overview")}
                  className={`pb-2 px-3 border-b-2 transition-colors ${
                    activeDetailTab === "overview"
                      ? "border-primary text-primary font-semibold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Financial Breakdown
                </button>
                <button
                  onClick={() => setActiveDetailTab("products")}
                  className={`pb-2 px-3 border-b-2 transition-colors ${
                    activeDetailTab === "products"
                      ? "border-primary text-primary font-semibold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Line Products ({selectedDeal.products.length})
                </button>
                <button
                  onClick={() => setActiveDetailTab("probability")}
                  className={`pb-2 px-3 border-b-2 transition-colors ${
                    activeDetailTab === "probability"
                      ? "border-primary text-primary font-semibold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Probability Signals
                </button>
                <button
                  onClick={() => setActiveDetailTab("timeline")}
                  className={`pb-2 px-3 border-b-2 transition-colors ${
                    activeDetailTab === "timeline"
                      ? "border-primary text-primary font-semibold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Timeline & Activities
                </button>
              </div>

              {/* Tab 1: Financial Breakdown */}
              {activeDetailTab === "overview" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-muted/20 border rounded-lg">
                      <span className="text-xs text-muted-foreground">Gross Subtotal</span>
                      <p className="text-lg font-bold">${Number(selectedDeal.subtotal).toFixed(2)}</p>
                    </div>
                    <div className="p-3 bg-muted/20 border rounded-lg">
                      <span className="text-xs text-muted-foreground">Total Discount</span>
                      <p className="text-lg font-bold text-amber-600">-${Number(selectedDeal.discount_amount).toFixed(2)}</p>
                    </div>
                    <div className="p-3 bg-muted/20 border rounded-lg">
                      <span className="text-xs text-muted-foreground">Sales Tax</span>
                      <p className="text-lg font-bold">${Number(selectedDeal.tax_amount).toFixed(2)}</p>
                    </div>
                    <div className="p-3 bg-muted/20 border rounded-lg">
                      <span className="text-xs text-muted-foreground">Total Cost Basis</span>
                      <p className="text-lg font-bold">${Number(selectedDeal.total_cost).toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-emerald-700">Gross Profit</span>
                      <p className="text-2xl font-bold text-emerald-600">
                        ${Number(selectedDeal.gross_profit).toFixed(2)}
                      </p>
                    </div>
                    <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-blue-700">Gross Margin %</span>
                      <p className="text-2xl font-bold text-blue-600">
                        {Number(selectedDeal.margin_percentage).toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {selectedDeal.notes && (
                    <div className="p-3 bg-muted/30 border rounded-lg">
                      <span className="text-xs font-semibold text-muted-foreground">Deal Notes:</span>
                      <p className="text-xs text-foreground mt-1">{selectedDeal.notes}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Line Products */}
              {activeDetailTab === "products" && (
                <div className="space-y-4">
                  {selectedDeal.products.length === 0 ? (
                    <p className="text-xs text-muted-foreground py-4 text-center">
                      No explicit product line items linked to this deal.
                    </p>
                  ) : (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-muted/50 border-b font-semibold text-muted-foreground">
                          <tr>
                            <th className="px-3 py-2">Product</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-right">Unit Price</th>
                            <th className="px-3 py-2 text-right">Disc %</th>
                            <th className="px-3 py-2 text-right">Subtotal</th>
                            <th className="px-3 py-2 text-right">Total</th>
                            <th className="px-3 py-2 text-right">Profit</th>
                            <th className="px-3 py-2 text-right">Margin %</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {selectedDeal.products.map((p) => (
                            <tr key={p.id}>
                              <td className="px-3 py-2 font-medium">
                                {p.product_name || "Catalog Product"}
                                {p.product_sku && <span className="text-muted-foreground ml-1">({p.product_sku})</span>}
                              </td>
                              <td className="px-3 py-2 text-right font-mono">{Number(p.quantity).toFixed(2)}</td>
                              <td className="px-3 py-2 text-right">${Number(p.unit_price).toFixed(2)}</td>
                              <td className="px-3 py-2 text-right text-amber-600">{Number(p.discount_percent).toFixed(1)}%</td>
                              <td className="px-3 py-2 text-right">${Number(p.subtotal).toFixed(2)}</td>
                              <td className="px-3 py-2 text-right font-semibold">${Number(p.total_amount).toFixed(2)}</td>
                              <td className="px-3 py-2 text-right text-emerald-600">${Number(p.gross_profit).toFixed(2)}</td>
                              <td className="px-3 py-2 text-right font-semibold">{Number(p.margin_percentage).toFixed(2)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Probability Engine Breakdown */}
              {activeDetailTab === "probability" && (
                <div className="space-y-4">
                  {probabilityData ? (
                    <>
                      <div className="p-4 bg-muted/20 border rounded-lg flex items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold text-muted-foreground">Deterministic Probability</span>
                          <p className="text-3xl font-extrabold text-blue-600">{probabilityData.probability}%</p>
                        </div>
                        <p className="text-xs text-muted-foreground max-w-sm">{probabilityData.explanation}</p>
                      </div>

                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">Signal Factors:</h4>
                        {probabilityData.factors.map((f, i) => (
                          <div
                            key={i}
                            className="p-2.5 bg-card border rounded-lg flex items-center justify-between text-xs"
                          >
                            <div>
                              <span className="font-semibold text-foreground">{f.factor}</span>
                              <p className="text-muted-foreground mt-0.5">{f.description}</p>
                            </div>
                            <span
                              className={`font-bold font-mono px-2 py-0.5 rounded ${
                                f.impact_pct > 0
                                  ? "bg-emerald-500/10 text-emerald-600"
                                  : f.impact_pct < 0
                                  ? "bg-rose-500/10 text-rose-600"
                                  : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {f.impact_pct > 0 ? `+${f.impact_pct}%` : `${f.impact_pct}%`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p className="text-xs text-muted-foreground py-4 text-center">Probability signals unavailable.</p>
                  )}
                </div>
              )}

              {/* Tab 4: Unified Timeline & Activity Logging */}
              {activeDetailTab === "timeline" && (
                <div className="space-y-6">
                  {/* Log Activity Form */}
                  <form onSubmit={handleLogActivity} className="p-4 bg-muted/30 border rounded-lg space-y-3">
                    <span className="text-xs font-semibold text-foreground">Log New Activity / Note:</span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <Select
                        value={activityType}
                        onChange={(e) => setActivityType(e.target.value)}
                        className="text-xs h-9"
                      >
                        <option value="NOTE">Note</option>
                        <option value="CALL">Sales Call</option>
                        <option value="EMAIL">Email Sent</option>
                        <option value="MEETING">Meeting</option>
                        <option value="TASK">Task Completed</option>
                        <option value="FOLLOW_UP">Follow Up</option>
                      </Select>
                      <Input
                        placeholder="Activity Title..."
                        value={activityTitle}
                        onChange={(e) => setActivityTitle(e.target.value)}
                        required
                        className="text-xs h-9 sm:col-span-2"
                      />
                    </div>
                    <Input
                      placeholder="Details / outcome / next steps (optional)..."
                      value={activityNotes}
                      onChange={(e) => setActivityNotes(e.target.value)}
                      className="text-xs h-9"
                    />
                    <div className="flex justify-end">
                      <Button size="sm" type="submit" disabled={submittingActivity} className="text-xs gap-1.5">
                        <Send className="h-3 w-3" /> Log Activity
                      </Button>
                    </div>
                  </form>

                  {/* Unified Timeline Stream */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">Unified Timeline Stream</h4>
                    {timelineEvents.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">No timeline events recorded.</p>
                    ) : (
                      <div className="relative pl-6 space-y-4 border-l-2 border-muted ml-2">
                        {timelineEvents.map((ev) => (
                          <div key={ev.event_id} className="relative group">
                            <div className="absolute -left-[31px] top-1 h-4 w-4 rounded-full bg-primary/20 border-2 border-primary" />
                            <div className="p-3 bg-card border rounded-lg text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-foreground">{ev.title}</span>
                                <span className="text-[10px] text-muted-foreground">
                                  {new Date(ev.timestamp).toLocaleString()}
                                </span>
                              </div>
                              {ev.description && <p className="text-muted-foreground">{ev.description}</p>}
                              <div className="flex items-center gap-2 pt-1 text-[10px] text-muted-foreground">
                                <Badge variant="outline" className="text-[9px] py-0 px-1">
                                  {ev.source}
                                </Badge>
                                <span>Actor: {ev.actor_name || "System"}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
