
"use client";

import React from "react";

export default function CustomerBillingPortal() {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Your Subscriptions & Billing</h1>
      
      <div className="border rounded-lg p-6 bg-card">
        <h2 className="text-xl font-semibold mb-4">Current Subscription</h2>
        <div className="flex justify-between items-center pb-4 border-b">
          <div>
            <p className="font-medium text-lg">Pro Monthly Plan</p>
            <p className="text-sm text-muted-foreground">Next billing date: 15-Oct-2026</p>
          </div>
          <div className="text-right">
            <p className="font-bold text-xl">$100.00 <span className="text-sm font-normal">/ mo</span></p>
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Active
            </span>
          </div>
        </div>
        
        <div className="pt-4 flex gap-3">
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
            Upgrade Plan
          </button>
          <button className="px-4 py-2 border rounded-md text-sm font-medium hover:bg-muted">
            Manage Payment Methods
          </button>
          <button className="px-4 py-2 text-red-600 border border-red-200 rounded-md text-sm font-medium hover:bg-red-50 ml-auto">
            Cancel Subscription
          </button>
        </div>
      </div>
      
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Invoices</h2>
        <div className="border rounded-lg divide-y">
          {[
            { id: "INV-001", date: "15-Sep-2026", amount: "$100.00", status: "Paid" },
            { id: "INV-002", date: "15-Aug-2026", amount: "$100.00", status: "Paid" },
          ].map((inv) => (
            <div key={inv.id} className="p-4 flex justify-between items-center">
              <div>
                <p className="font-medium">{inv.id}</p>
                <p className="text-sm text-muted-foreground">{inv.date}</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="font-medium">{inv.amount}</p>
                <span className="text-sm text-green-600 font-medium">{inv.status}</span>
                <button className="text-sm text-blue-600 hover:underline">Download PDF</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
