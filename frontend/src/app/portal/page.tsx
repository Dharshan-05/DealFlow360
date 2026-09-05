"use client";
import { useEffect, useState } from "react";
import { portalApi } from "@/lib/api.portal";
import Link from "next/link";

export default function PortalDashboard() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        portalApi.getDashboard().then(res => {
            setData(res.data);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, []);

    if (loading) return <div className="p-8">Loading dashboard...</div>;
    if (!data) return <div className="p-8">Error loading dashboard</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold mb-8">Welcome, {data.customer.name}</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="border p-6 rounded shadow bg-white">
                    <h3 className="text-gray-500 font-semibold mb-2">Total Quotes</h3>
                    <div className="text-3xl font-bold">{data.total_quotes}</div>
                </div>
                <div className="border p-6 rounded shadow bg-white">
                    <h3 className="text-gray-500 font-semibold mb-2">Pending Action</h3>
                    <div className="text-3xl font-bold">{data.pending_quotes}</div>
                </div>
                <div className="border p-6 rounded shadow bg-white">
                    <h3 className="text-gray-500 font-semibold mb-2">Unread Notifications</h3>
                    <div className="text-3xl font-bold">{data.unread_notifications}</div>
                </div>
            </div>

            <div className="flex gap-4">
                <Link href="/portal/quotes" className="bg-blue-600 text-white px-4 py-2 rounded">
                    View My Quotes
                </Link>
                <Link href="/portal/billing" className="bg-gray-200 text-gray-800 px-4 py-2 rounded">
                    Billing Portal
                </Link>
            </div>
        </div>
    );
}
