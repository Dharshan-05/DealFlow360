"use client";
import { useEffect, useState } from "react";
import { portalApi } from "@/lib/api.portal";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

export default function PortalNegotiate() {
    const params = useParams();
    const router = useRouter();
    const [quote, setQuote] = useState<any>(null);
    const [comment, setComment] = useState("");
    const [reqType, setReqType] = useState("REQUEST_DISCOUNT");
    const [targetVal, setTargetVal] = useState("");
    const [msg, setMsg] = useState("");

    useEffect(() => {
        if (params.id) {
            portalApi.getQuote(params.id as string).then(res => {
                setQuote(res.data);
            });
        }
    }, [params.id]);

    const handleComment = async () => {
        if (!comment) return;
        await portalApi.addComment(quote.id, comment);
        setComment("");
        // refresh
        const res = await portalApi.getQuote(quote.id);
        setQuote(res.data);
    };

    const handleNegotiate = async () => {
        await portalApi.requestNegotiation(quote.id, {
            request_type: reqType,
            requested_value: targetVal,
            current_value: reqType === 'REQUEST_DISCOUNT' ? quote.overall_discount_percent : quote.total_amount,
            customer_message: msg
        });
        alert("Negotiation request submitted!");
        // refresh
        const res = await portalApi.getQuote(quote.id);
        setQuote(res.data);
    };

    const handleAccept = async () => {
        if (confirm("Are you sure you want to accept this quote?")) {
            await portalApi.acceptQuote(quote.id);
            alert("Quote accepted!");
            router.push("/portal/quotes");
        }
    };

    if (!quote) return <div className="p-8">Loading quote...</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <Link href="/portal/quotes" className="text-blue-600 mb-4 inline-block">&larr; Back to Quotes</Link>
            
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Quote {quote.quotation_number}</h1>
                <div className="flex gap-2">
                    {quote.status === "SENT" && (
                        <>
                            <button onClick={handleAccept} className="bg-green-600 text-white px-4 py-2 rounded">Accept Quote</button>
                        </>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <div className="bg-white border rounded shadow p-6 mb-6">
                        <h2 className="text-lg font-bold mb-4">Quote Details</h2>
                        <div className="flex justify-between mb-2"><span>Subtotal:</span> <span>${quote.subtotal}</span></div>
                        <div className="flex justify-between mb-2"><span>Discount:</span> <span>-${quote.total_discount}</span></div>
                        <div className="flex justify-between mb-2"><span>Tax:</span> <span>${quote.tax_amount}</span></div>
                        <div className="flex justify-between font-bold text-lg border-t pt-2 mt-2">
                            <span>Total:</span> <span>${quote.total_amount}</span>
                        </div>
                    </div>

                    {quote.status === "SENT" && (
                        <div className="bg-white border rounded shadow p-6">
                            <h2 className="text-lg font-bold mb-4">Request Change (Negotiation)</h2>
                            <div className="mb-4">
                                <label className="block mb-1 text-sm">Type</label>
                                <select value={reqType} onChange={e=>setReqType(e.target.value)} className="w-full border p-2 rounded">
                                    <option value="REQUEST_DISCOUNT">Request Better Discount</option>
                                    <option value="REQUEST_QUANTITY">Request Quantity Change</option>
                                    <option value="REQUEST_DELIVERY">Request Faster Delivery</option>
                                </select>
                            </div>
                            <div className="mb-4">
                                <label className="block mb-1 text-sm">Requested Value (e.g., "15%" or "$900")</label>
                                <input type="text" value={targetVal} onChange={e=>setTargetVal(e.target.value)} className="w-full border p-2 rounded" />
                            </div>
                            <div className="mb-4">
                                <label className="block mb-1 text-sm">Message</label>
                                <textarea value={msg} onChange={e=>setMsg(e.target.value)} className="w-full border p-2 rounded" rows={3}></textarea>
                            </div>
                            <button onClick={handleNegotiate} className="bg-blue-600 text-white px-4 py-2 rounded w-full">Submit Request</button>
                        </div>
                    )}
                </div>

                <div>
                    <div className="bg-white border rounded shadow p-6">
                        <h2 className="text-lg font-bold mb-4">Comments & History</h2>
                        <div className="mb-4 max-h-64 overflow-y-auto space-y-4">
                            {quote.comments?.map((c: any) => (
                                <div key={c.id} className="bg-gray-50 p-3 rounded">
                                    <div className="text-xs text-gray-500 mb-1">{new Date(c.created_at).toLocaleString()}</div>
                                    <div>{c.comment}</div>
                                </div>
                            ))}
                            {(!quote.comments || quote.comments.length === 0) && <div className="text-gray-500">No comments yet.</div>}
                        </div>
                        
                        <div className="flex gap-2">
                            <input 
                                type="text" 
                                value={comment} 
                                onChange={e=>setComment(e.target.value)} 
                                placeholder="Add a comment..."
                                className="flex-1 border p-2 rounded"
                            />
                            <button onClick={handleComment} className="bg-gray-800 text-white px-4 py-2 rounded">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
