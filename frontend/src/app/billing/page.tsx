
"use client";

import React, { useEffect, useState } from "react";
import { fetchBillingDashboard } from "@/lib/api";

export default function AdminBillingDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetchBillingDashboard().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8">Loading dashboard...</div>;

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">G15 Billing & Subscriptions</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-6 border rounded-lg bg-card shadow-sm">
          <p className="text-sm text-muted-foreground font-medium">Monthly Recurring Revenue (MRR)</p>
          <p className="text-3xl font-bold mt-2">${data.mrr}</p>
        </div>
        <div className="p-6 border rounded-lg bg-card shadow-sm">
          <p className="text-sm text-muted-foreground font-medium">Annual Recurring Revenue (ARR)</p>
          <p className="text-3xl font-bold mt-2">${data.arr}</p>
        </div>
        <div className="p-6 border rounded-lg bg-card shadow-sm">
          <p className="text-sm text-muted-foreground font-medium">Active Subscriptions</p>
          <p className="text-3xl font-bold mt-2">{data.active_subscriptions}</p>
        </div>
        <div className="p-6 border rounded-lg bg-card shadow-sm">
          <p className="text-sm text-muted-foreground font-medium">Pending Payments</p>
          <p className="text-3xl font-bold mt-2">{data.pending_payments_count}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold text-lg">Recurring Revenue</h2>
          <p className="text-2xl font-bold text-blue-600">${data.recurring_revenue}</p>
        </div>
        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold text-lg">One-Time Revenue</h2>
          <p className="text-2xl font-bold text-green-600">${data.one_time_revenue}</p>
        </div>
        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold text-lg">Hybrid Total</h2>
          <p className="text-2xl font-bold text-purple-600">${data.hybrid_revenue}</p>
        </div>
      </div>
    </div>
  );
}
