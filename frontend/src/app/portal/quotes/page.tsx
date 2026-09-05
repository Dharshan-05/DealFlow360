"use client";
import { useEffect, useState } from "react";
import { portalApi } from "@/lib/api.portal";
import Link from "next/link";

export default function PortalQuotes() {
    const [quotes, setQuotes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        portalApi.getQuotes().then(res => {
            setQuotes(res.data || []);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, []);

    if (loading) return <div className="p-8">Loading quotes...</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">My Quotes</h1>
                <Link href="/portal" className="text-blue-600">Back to Dashboard</Link>
            </div>
            
            <div className="bg-white border rounded shadow overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="p-4">Quote #</th>
                            <th className="p-4">Date</th>
                            <th className="p-4">Status</th>
                            <th className="p-4">Total</th>
                            <th className="p-4">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {quotes.map(q => (
                            <tr key={q.id} className="border-b">
                                <td className="p-4">{q.quotation_number}</td>
                                <td className="p-4">{new Date(q.created_at).toLocaleDateString()}</td>
                                <td className="p-4">
                                    <span className="px-2 py-1 bg-gray-100 rounded text-sm">{q.status}</span>
                                </td>
                                <td className="p-4">${parseFloat(q.total_amount).toFixed(2)}</td>
                                <td className="p-4">
                                    <Link href={`/portal/quotes/${q.id}/negotiate`} className="text-blue-600 font-semibold">
                                        View & Negotiate
                                    </Link>
                                </td>
                            </tr>
                        ))}
                        {quotes.length === 0 && (
                            <tr>
                                <td colSpan={5} className="p-4 text-center text-gray-500">No quotes found.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
