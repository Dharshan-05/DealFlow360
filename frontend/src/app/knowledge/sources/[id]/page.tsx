"use client";
import React, { useState, useEffect } from 'react';

export default function KnowledgeSourceDetail({ params }: { params: { id: string } }) {
    const [source, setSource] = useState<any>(null);
    const [uploading, setUploading] = useState(false);

    useEffect(() => {
        fetch('/api/v1/knowledge/sources/' + params.id, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        })
        .then(res => res.json())
        .then(data => setSource(data))
        .catch(console.error);
    }, [params.id]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            await fetch('/api/v1/knowledge/sources/' + params.id + '/ingest', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') },
                body: formData
            });
            alert('File ingested successfully');
            window.location.reload();
        } catch (err) {
            console.error(err);
            alert('Upload failed');
        }
        setUploading(false);
    };

    if (!source) return <div className="p-8">Loading...</div>;

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <header className="mb-6">
                <h1 className="text-3xl font-bold text-gray-800">{source.name}</h1>
                <p className="text-gray-600 mt-1">Status: {source.status}</p>
            </header>

            <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                <h2 className="text-xl font-semibold mb-4 text-gray-700">Ingest Document</h2>
                <input type="file" accept=".txt,.pdf,.docx,.md" onChange={handleFileUpload} disabled={uploading} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                {uploading && <p className="mt-2 text-sm text-gray-500">Processing, chunking, and embedding document...</p>}
            </div>
        </div>
    );
}
