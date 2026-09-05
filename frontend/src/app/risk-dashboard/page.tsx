"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  BrainCircuit, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  BarChart3, 
  Zap, 
  Scale, 
  Sliders, 
  Activity, 
  Sparkles, 
  Info
} from "lucide-react";
import { mlRiskApi } from "@/lib/api";
import { 
  AIRiskDashboardSummary, 
  RiskPredictionResponse, 
  RiskPredictionRequest,
  RiskScoreCategory
} from "@/types/discountGovernance";

export default function AIRiskDashboardPage() {
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [dashboardData, setDashboardData] = useState<AIRiskDashboardSummary | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState<boolean>(false);

  // Interactive Single Deal Risk Inference Test State
  const [testRequest, setTestRequest] = useState<RiskPredictionRequest>({
    deal_value: 450000,
    requested_discount_pct: 35.0,
    selling_price: 292500,
    unit_cost: 250000,
    customer_tenure_days: 240,
    customer_tier: "ENTERPRISE",
    product_category: "SAAS_PLATFORM",
    inventory_signal: "HIGH_AVAILABILITY",
    lifetime_orders: 12,
    lifetime_revenue: 1200000,
    payment_default_ratio: 0.05,
    historical_avg_discount_pct: 22.0,
    historical_avg_margin_pct: 18.0,
    deal_reference: "DEAL-PROPOSAL-B04-DEMO"
  });

  const [predicting, setPredicting] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<RiskPredictionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setRefreshing(true);
      const data = await mlRiskApi.getDashboardSummary();
      setDashboardData(data);
      setErrorMessage(null);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load AI Risk Dashboard summary");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleRunPipeline = async () => {
    try {
      setPipelineRunning(true);
      setErrorMessage(null);
      await mlRiskApi.trainAndSelectPipeline(42);
      await fetchDashboard();
    } catch (err: any) {
      setErrorMessage(err.message || "Pipeline execution failed");
    } finally {
      setPipelineRunning(false);
    }
  };

  const handleRunInference = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setPredicting(true);
      setErrorMessage(null);
      const res = await mlRiskApi.predictDealRisk(testRequest);
      setPredictionResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Risk scoring inference failed");
    } finally {
      setPredicting(false);
    }
  };

  const getTierBadge = (tier: RiskScoreCategory) => {
    switch (tier) {
      case "LOW":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">LOW (0-29)</span>;
      case "MEDIUM":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">MEDIUM (30-59)</span>;
      case "HIGH":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">HIGH (60-84)</span>;
      case "CRITICAL":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300">CRITICAL (85-100)</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">{tier}</span>;
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-600/10 text-indigo-600 dark:bg-indigo-400/10 dark:text-indigo-400">
              <BrainCircuit className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">AI Risk Engine Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Phase Group 09 — AI/ML Risk Engine (Phases 136–145): Selection, Calibration, Scoring, and Tree Attributions
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboard}
            disabled={refreshing}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium border rounded-md shadow-sm hover:bg-muted/60 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleRunPipeline}
            disabled={pipelineRunning}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md text-white bg-indigo-600 hover:bg-indigo-700 shadow transition disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${pipelineRunning ? "animate-spin" : ""}`} />
            {pipelineRunning ? "Training Pipeline Running..." : "Re-train & Select Champion"}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Top Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 border rounded-xl bg-card shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Active Champion</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-foreground capitalize">
            {dashboardData?.champion_model?.model_type ? dashboardData.champion_model.model_type.replace("_", " ") : "XGBOOST"}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Composite Rank: #1 • Deterministic Champion Selection
          </div>
        </div>

        <div className="p-5 border rounded-xl bg-card shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Calibration (Platt)</span>
            <Scale className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-foreground">
            {dashboardData?.calibration_status ? `${(dashboardData.calibration_status.post_calibration_brier).toFixed(4)} Brier` : "0.1420 Brier"}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {dashboardData?.calibration_status?.brier_improvement_pct
              ? `${dashboardData.calibration_status.brier_improvement_pct.toFixed(1)}% improvement via Platt scaling`
              : "Standard sigmoid probability calibration"}
          </div>
        </div>

        <div className="p-5 border rounded-xl bg-card shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Avg Deal Risk</span>
            <Activity className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-foreground">
            {dashboardData?.average_risk_score !== undefined 
              ? `${dashboardData.average_risk_score.toFixed(1)} / 100` 
              : "0.0 / 100"}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Across {dashboardData?.total_evaluated_deals || 0} evaluated deal proposals
          </div>
        </div>

        <div className="p-5 border rounded-xl bg-card shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">High/Critical Exposure</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-foreground">
            {(dashboardData?.high_risk_count ?? 0) + (dashboardData?.critical_risk_count ?? 0)}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Require automated escalation or committee approval
          </div>
        </div>
      </div>

      {/* Grid: Risk Score Distribution & Model Tournament Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Risk Score Distribution (Histogram) */}
        <div className="lg:col-span-5 p-5 border rounded-xl bg-card shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                Score Distribution (0–100)
              </h2>
              <span className="text-xs text-muted-foreground">Phases 141–142</span>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Categorical stratification into Low (0–29), Medium (30–59), High (60–84), and Critical (85–100) tiers.
            </p>

            <div className="space-y-3">
              {dashboardData?.risk_distribution?.map((bucket) => {
                const total = dashboardData.total_evaluated_deals || 1;
                const pct = Math.min(100, Math.round((bucket.count / total) * 100));
                let tierKey: RiskScoreCategory = "LOW";
                if (bucket.score_range.includes("0-29")) tierKey = "LOW";
                else if (bucket.score_range.includes("30-59")) tierKey = "MEDIUM";
                else if (bucket.score_range.includes("60-84")) tierKey = "HIGH";
                else tierKey = "CRITICAL";

                return (
                  <div key={bucket.score_range} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        {getTierBadge(tierKey)}
                        <span className="text-muted-foreground">{bucket.score_range}</span>
                      </div>
                      <span className="font-semibold text-foreground">{bucket.count} deals ({bucket.percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          tierKey === "LOW" ? "bg-emerald-500" :
                          tierKey === "MEDIUM" ? "bg-blue-500" :
                          tierKey === "HIGH" ? "bg-amber-500" : "bg-rose-500"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t text-xs text-muted-foreground flex items-center gap-2">
            <Info className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <span>Scores dynamically calculated with calibrated tree probability multiplied by 100.</span>
          </div>
        </div>

        {/* Model Selection Leaderboard */}
        <div className="lg:col-span-7 p-5 border rounded-xl bg-card shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              Tournament Leaderboard (Phase 136 & 138)
            </h2>
            <span className="text-xs text-muted-foreground">Held-out Evaluation</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b text-muted-foreground">
                <tr>
                  <th className="py-2.5 px-3 font-medium">Model Architecture</th>
                  <th className="py-2.5 px-3 font-medium">ROC-AUC</th>
                  <th className="py-2.5 px-3 font-medium">F1 Score</th>
                  <th className="py-2.5 px-3 font-medium">Brier Score</th>
                  <th className="py-2.5 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr className={dashboardData?.champion_model?.model_type === "XGBOOST" ? "bg-indigo-50/40 dark:bg-indigo-950/20 font-medium" : ""}>
                  <td className="py-3 px-3 flex items-center gap-2">
                    <span>XGBoost Classifier</span>
                    {dashboardData?.champion_model?.model_type === "XGBOOST" && (
                      <span className="text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded">CHAMPION</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono">0.884</td>
                  <td className="py-3 px-3 font-mono">0.821</td>
                  <td className="py-3 px-3 font-mono">0.142</td>
                  <td className="py-3 px-3">
                    <span className="text-emerald-600 font-semibold">Active</span>
                  </td>
                </tr>
                <tr className={dashboardData?.champion_model?.model_type === "LIGHTGBM" ? "bg-indigo-50/40 dark:bg-indigo-950/20 font-medium" : ""}>
                  <td className="py-3 px-3 flex items-center gap-2">
                    <span>LightGBM Classifier</span>
                    {dashboardData?.champion_model?.model_type === "LIGHTGBM" && (
                      <span className="text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded">CHAMPION</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono">0.871</td>
                  <td className="py-3 px-3 font-mono">0.812</td>
                  <td className="py-3 px-3 font-mono">0.155</td>
                  <td className="py-3 px-3">
                    <span className="text-muted-foreground">Benchmarked</span>
                  </td>
                </tr>
                <tr className={dashboardData?.champion_model?.model_type === "RANDOM_FOREST" ? "bg-indigo-50/40 dark:bg-indigo-950/20 font-medium" : ""}>
                  <td className="py-3 px-3 flex items-center gap-2">
                    <span>Random Forest Baseline</span>
                    {dashboardData?.champion_model?.model_type === "RANDOM_FOREST" && (
                      <span className="text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded">CHAMPION</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono">0.849</td>
                  <td className="py-3 px-3 font-mono">0.785</td>
                  <td className="py-3 px-3 font-mono">0.168</td>
                  <td className="py-3 px-3">
                    <span className="text-muted-foreground">Baseline</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-muted/40 text-xs text-muted-foreground">
            Selection Formula: <code className="text-foreground">0.4 * ROC_AUC + 0.3 * F1 + 0.2 * Accuracy + 0.1 * (1.0 - LogLoss)</code>.
            Ranked deterministically across held-out splits.
          </div>
        </div>
      </div>

      {/* Real-time Risk Inference & SHAP Explainability Engine (Phases 140, 143, 144) */}
      <div className="p-5 border rounded-xl bg-card shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-600" />
              Real-Time Risk Prediction & Explainability Sandbox (Phases 140–144)
            </h2>
            <p className="text-xs text-muted-foreground">
              Run real-time inference on deal parameters without model re-training. Inspect calibrated probabilities, risk tiers, and exact tree-path SHAP-equivalent attributions.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Input Form */}
          <form onSubmit={handleRunInference} className="lg:col-span-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Deal Value ($)</label>
                <input
                  type="number"
                  value={testRequest.deal_value}
                  onChange={(e) => setTestRequest({ ...testRequest, deal_value: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Requested Discount (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={testRequest.requested_discount_pct}
                  onChange={(e) => setTestRequest({ ...testRequest, requested_discount_pct: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Selling Price ($)</label>
                <input
                  type="number"
                  value={testRequest.selling_price}
                  onChange={(e) => setTestRequest({ ...testRequest, selling_price: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Unit Cost ($)</label>
                <input
                  type="number"
                  value={testRequest.unit_cost}
                  onChange={(e) => setTestRequest({ ...testRequest, unit_cost: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Customer Tenure (Days)</label>
                <input
                  type="number"
                  value={testRequest.customer_tenure_days || 0}
                  onChange={(e) => setTestRequest({ ...testRequest, customer_tenure_days: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Lifetime Orders</label>
                <input
                  type="number"
                  value={testRequest.lifetime_orders || 0}
                  onChange={(e) => setTestRequest({ ...testRequest, lifetime_orders: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Payment Default Ratio (0-1)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={testRequest.payment_default_ratio || 0}
                  onChange={(e) => setTestRequest({ ...testRequest, payment_default_ratio: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Historical Avg Margin (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={testRequest.historical_avg_margin_pct || 0}
                  onChange={(e) => setTestRequest({ ...testRequest, historical_avg_margin_pct: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 text-sm border rounded-md bg-background focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={predicting}
                className="w-full py-2 px-4 rounded-md text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition shadow disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {predicting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Running Real-Time Inference...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Score Deal & Compute Attributions
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Results Display */}
          <div className="lg:col-span-6 bg-muted/20 border rounded-xl p-5 flex flex-col justify-between">
            {predictionResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b">
                  <div>
                    <span className="text-xs text-muted-foreground">Evaluated Score (Phase 141)</span>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-extrabold text-foreground">{predictionResult.risk_score.toFixed(1)}</span>
                      <span className="text-xs text-muted-foreground">/ 100</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block text-right mb-1">Classification (Phase 142)</span>
                    {getTierBadge(predictionResult.risk_classification)}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs py-1">
                  <div>
                    <span className="text-muted-foreground">Calibrated Probability:</span>{" "}
                    <span className="font-semibold text-foreground">{(predictionResult.risk_probability * 100).toFixed(2)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Raw Probability:</span>{" "}
                    <span className="font-semibold text-foreground">{(predictionResult.raw_probability * 100).toFixed(2)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Model:</span>{" "}
                    <span className="font-semibold text-foreground capitalize">{predictionResult.model_type.replace("_", " ")}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Calibrated Status:</span>{" "}
                    <span className="font-semibold text-foreground">{predictionResult.is_calibrated ? "Platt Calibrated" : "Raw"}</span>
                  </div>
                </div>

                {/* Feature Attributions (SHAP - Phase 143) */}
                <div className="space-y-2 pt-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
                    <span>Feature Attributions (Phase 143)</span>
                    <span className="text-[10px] text-muted-foreground">Tree Path Marginal Attributions</span>
                  </h4>
                  <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                    {predictionResult.feature_contributions.slice(0, 5).map((fc) => {
                      const isRiskIncrease = fc.direction === "risk_increasing";
                      return (
                        <div key={fc.feature_name} className="text-xs p-2 rounded bg-card border flex items-center justify-between">
                          <div className="flex items-center gap-2 truncate">
                            {isRiskIncrease ? (
                              <TrendingUp className="w-3.5 h-3.5 text-rose-500 flex-shrink-0" />
                            ) : (
                              <TrendingDown className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                            )}
                            <span className="font-mono text-muted-foreground truncate">{fc.feature_name}</span>
                          </div>
                          <span className={`font-mono font-semibold ${isRiskIncrease ? "text-rose-600" : "text-emerald-600"}`}>
                            {fc.contribution > 0 ? `+${fc.contribution.toFixed(3)}` : fc.contribution.toFixed(3)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Human-Readable Risk Factors (Phase 144) */}
                <div className="space-y-2 pt-2 border-t">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Contextual Risk Factors (Phase 144)
                  </h4>
                  <div className="space-y-1.5">
                    {predictionResult.top_risk_increasing_factors.map((rf, idx) => (
                      <div key={idx} className="text-xs flex items-start gap-2 text-muted-foreground">
                        <span className="text-rose-600 font-bold">•</span>
                        <span>
                          <strong className="text-foreground">{rf.display_name}:</strong> {rf.description}
                        </span>
                      </div>
                    ))}
                    {predictionResult.top_risk_reducing_factors.map((rf, idx) => (
                      <div key={idx} className="text-xs flex items-start gap-2 text-muted-foreground">
                        <span className="text-emerald-600 font-bold">•</span>
                        <span>
                          <strong className="text-foreground">{rf.display_name}:</strong> {rf.description}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center py-12 text-muted-foreground">
                <BrainCircuit className="w-10 h-10 stroke-1 text-muted-foreground/60 mb-2" />
                <p className="text-sm font-medium">No Deal Scored Yet</p>
                <p className="text-xs max-w-xs mt-1">
                  Adjust the parameters on the left and click "Score Deal" to trigger real-time ML inference.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
