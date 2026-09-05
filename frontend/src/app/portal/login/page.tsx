"use client";
import { useState } from "react";
import { portalApi } from "@/lib/api.portal";
import { setAccessToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function PortalLoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Using URLSearchParams for form-urlencoded token endpoint if standard
            const res = await portalApi.login({ email, password });
            if (res.data?.access_token) {
                setAccessToken(res.data.access_token);
                router.push("/portal");
            } else {
                setError("Login failed");
            }
        } catch (err: any) {
            setError(err.message || "Invalid credentials");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full bg-white p-8 border rounded shadow">
                <h2 className="text-2xl font-bold mb-6">Customer Portal Login</h2>
                {error && <div className="mb-4 text-red-600 bg-red-100 p-2 rounded">{error}</div>}
                <form onSubmit={handleLogin}>
                    <div className="mb-4">
                        <label className="block mb-1">Email</label>
                        <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full border p-2 rounded" required />
                    </div>
                    <div className="mb-6">
                        <label className="block mb-1">Password</label>
                        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} className="w-full border p-2 rounded" required />
                    </div>
                    <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">Login</button>
                </form>
            </div>
        </div>
    );
}
