"use client";

import React, { useState, useEffect } from 'react';

export default function AICommandCenter() {
    const [status, setStatus] = useState<any>(null);
    const [usage, setUsage] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/ai/status', {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        })
        .then(res => res.json())
        .then(data => setStatus(data))
        .catch(console.error);

        fetch('/api/v1/ai/usage', {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        })
        .then(res => res.json())
        .then(data => setUsage(data))
        .catch(console.error);
    }, []);

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">AI Command Center</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-700">System Status</h2>
                    {status ? (
                        <ul className="space-y-3">
                            <li className="flex justify-between">
                                <span className="text-gray-500">Service Status</span>
                                <span className="font-medium text-green-600">{status.status}</span>
                            </li>
                            <li className="flex justify-between">
                                <span className="text-gray-500">LLM Provider</span>
                                <span className="font-medium text-gray-800">{status.provider}</span>
                            </li>
                            <li className="flex justify-between">
                                <span className="text-gray-500">Active Model</span>
                                <span className="font-medium text-blue-600">{status.model}</span>
                            </li>
                        </ul>
                    ) : (
                        <p className="text-gray-400">Loading status...</p>
                    )}
                </div>

                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-700">Usage Analytics</h2>
                    {usage ? (
                        <div className="text-center py-4">
                            <p className="text-sm text-gray-500 uppercase tracking-wide">Total Tokens Consumed</p>
                            <p className="text-4xl font-bold text-gray-800 mt-2">{usage.total_tokens.toLocaleString()}</p>
                        </div>
                    ) : (
                        <p className="text-gray-400">Loading usage data...</p>
                    )}
                </div>

                <div className="bg-white p-6 rounded-lg shadow border border-gray-200 md:col-span-2">
                    <h2 className="text-xl font-semibold mb-4 text-gray-700">Security & Guardrails</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
                            <p className="font-semibold text-green-800">RBAC Enforced</p>
                            <p className="text-xs text-green-600 mt-1">Active</p>
                        </div>
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-center">
                            <p className="font-semibold text-blue-800">Prompt Injection Filter</p>
                            <p className="text-xs text-blue-600 mt-1">Active</p>
                        </div>
                        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg text-center">
                            <p className="font-semibold text-purple-800">Tenant Isolation</p>
                            <p className="text-xs text-purple-600 mt-1">Active</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
