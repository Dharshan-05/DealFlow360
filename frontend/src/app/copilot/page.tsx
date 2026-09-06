"use client";

import React, { useState } from 'react';

export default function CopilotPage() {
    const [message, setMessage] = useState('');
    const [chat, setChat] = useState<{role: string, content: string}[]>([]);
    const [loading, setLoading] = useState(false);
    const [actionPreview, setActionPreview] = useState<any>(null);

    const handleSend = async () => {
        if (!message.trim()) return;
        
        const newChat = [...chat, { role: 'user', content: message }];
        setChat(newChat);
        setMessage('');
        setLoading(true);

        try {
            const res = await fetch('/api/v1/ai/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token') // Mock token
                },
                body: JSON.stringify({ message: message })
            });
            const data = await res.json();
            
            setChat([...newChat, { role: 'assistant', content: data.answer }]);
            if (data.requires_confirmation) {
                setActionPreview(data.action_preview);
            }
        } catch (err) {
            setChat([...newChat, { role: 'assistant', content: 'Error communicating with AI.' }]);
        }
        setLoading(false);
    };

    const confirmAction = async () => {
        if (!actionPreview) return;
        try {
            const res = await fetch('/api/v1/ai/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: JSON.stringify({
                    conversation_id: "123", // mock
                    tool_name: actionPreview.tool_name,
                    arguments: actionPreview.arguments,
                    confirmed: true
                })
            });
            const data = await res.json();
            setChat([...chat, { role: 'assistant', content: 'Action Confirmed: ' + data.answer }]);
            setActionPreview(null);
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="flex flex-col h-screen p-4 bg-gray-50">
            <header className="mb-4">
                <h1 className="text-2xl font-bold text-gray-800">DealFlow360 AI Copilot</h1>
                <p className="text-sm text-gray-500">Your intelligent sales assistant</p>
            </header>

            <div className="flex-1 bg-white rounded-lg shadow p-4 overflow-y-auto mb-4 border border-gray-200">
                {chat.map((msg, idx) => (
                    <div key={idx} className={"mb-4 " + (msg.role === 'user' ? 'text-right' : 'text-left')}>
                        <div className={"inline-block p-3 rounded-lg " + (msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800')}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {loading && <div className="text-gray-500 italic">AI is thinking...</div>}
                
                {actionPreview && (
                    <div className="mt-4 p-4 border border-yellow-400 bg-yellow-50 rounded-lg">
                        <h3 className="font-bold text-yellow-800">Confirmation Required</h3>
                        <p className="text-sm text-yellow-700">The AI wants to perform: <strong>{actionPreview.tool_name}</strong></p>
                        <pre className="text-xs bg-yellow-100 p-2 mt-2 rounded">{JSON.stringify(actionPreview.arguments, null, 2)}</pre>
                        <div className="mt-3 flex gap-2">
                            <button onClick={confirmAction} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Confirm & Execute</button>
                            <button onClick={() => setActionPreview(null)} className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400">Cancel</button>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex gap-2">
                <input 
                    type="text" 
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                    placeholder="Ask about a deal, request a risk analysis, or get next best actions..."
                />
                <button 
                    onClick={handleSend}
                    disabled={loading}
                    className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                    Send
                </button>
            </div>
        </div>
    );
}
