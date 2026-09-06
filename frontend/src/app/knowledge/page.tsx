"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function KnowledgeBasePage() {
    const [sources, setSources] = useState<any[]>([]);
    const [name, setName] = useState('');
    const [type, setType] = useState('DOCUMENT');

    useEffect(() => {
        fetch('/api/v1/knowledge/sources', {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        })
        .then(res => res.json())
        .then(data => setSources(data || []))
        .catch(console.error);
    }, []);

    const createSource = async () => {
        const res = await fetch('/api/v1/knowledge/sources', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('token') 
            },
            body: JSON.stringify({ name, source_type: type })
        });
        const newSource = await res.json();
        setSources([...sources, newSource]);
        setName('');
    };

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <header className="mb-6">
                <h1 className="text-3xl font-bold text-gray-800">Business Knowledge Base (RAG)</h1>
                <p className="text-gray-600 mt-1">Manage documents and policies used by the AI Copilot.</p>
            </header>

            <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-8">
                <h2 className="text-xl font-semibold mb-4 text-gray-700">Add New Source</h2>
                <div className="flex gap-4">
                    <input type="text" placeholder="Source Name (e.g. Q3 Sales Policy)" className="border p-2 rounded flex-1" value={name} onChange={e => setName(e.target.value)} />
                    <select className="border p-2 rounded" value={type} onChange={e => setType(e.target.value)}>
                        <option value="DOCUMENT">Document</option>
                        <option value="URL">URL</option>
                    </select>
                    <button onClick={createSource} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Create</button>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {sources.map(s => (
                            <tr key={s.id}>
                                <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{s.name}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-gray-500">{s.source_type}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={"px-2 inline-flex text-xs leading-5 font-semibold rounded-full " + (s.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800')}>
                                        {s.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <Link href={"/knowledge/sources/" + s.id} className="text-blue-600 hover:text-blue-900">Manage Documents</Link>
                                </td>
                            </tr>
                        ))}
                        {sources.length === 0 && (
                            <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No knowledge sources found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
