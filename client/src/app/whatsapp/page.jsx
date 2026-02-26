"use client";

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Smartphone, Terminal, QrCode } from 'lucide-react';

export default function WhatsAppPage() {
    const [running, setRunning] = useState(false);
    const [logs, setLogs] = useState([]);
    const [config, setConfig] = useState({
        limit: 50,
        message_template: ""
    });

    const endOfLogsRef = useRef(null);

    useEffect(() => {
        let interval;
        if (running) {
            interval = setInterval(async () => {
                try {
                    const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/whatsapp/status`);
                    setLogs(res.data.logs || []);
                    if (res.data.status === 'idle' && res.data.logs.some(l => l.includes('Complete') || l.includes('❌'))) {
                        setRunning(false);
                    }
                } catch (e) {
                    console.error(e);
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [running]);

    useEffect(() => {
        endOfLogsRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const handleStart = async () => {
        try {
            setRunning(true);
            setLogs(['Initializing WhatsApp Web Playwright Session...']);
            await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/whatsapp/start`, config);
        } catch (e) {
            alert("Failed to start WhatsApp automation. " + (e.response?.data?.detail || ""));
            setRunning(false);
        }
    };

    const handleChange = (e) => {
        setConfig({ ...config, [e.target.name]: e.target.value });
    };

    return (
        <div className="max-w-6xl mx-auto mt-8 flex flex-col lg:flex-row gap-8">

            {/* Settings Panel */}
            <div className="lg:w-1/3 flex flex-col gap-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">WhatsApp Auto</h1>
                    <p className="text-gray-400 mt-2 text-sm">Automate outreach directly from your connected Google Sheet.</p>
                </div>

                <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col gap-5">
                    <div className="flex items-center gap-2 pb-4 border-b border-border">
                        <Smartphone className="text-green-500" size={20} />
                        <h3 className="font-semibold">Messaging Setup</h3>
                    </div>

                    <div className="bg-green-500/10 border border-green-500/20 p-4 rounded-lg flex items-start gap-3 text-sm text-green-400">
                        <QrCode className="shrink-0 mt-0.5" size={18} />
                        <p>When you start, a browser window will open automatically. Please scan the WhatsApp Web QR Code if you haven't recently.</p>
                    </div>

                    <div className="flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                            <label className="text-sm font-medium text-gray-300">Message Template</label>
                            <span className="text-xs text-gray-500">{config.message_template.length} chars</span>
                        </div>
                        <textarea
                            name="message_template"
                            value={config.message_template}
                            onChange={handleChange}
                            disabled={running}
                            className="bg-background border border-border rounded-lg p-3 text-sm min-h-[200px] focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50 resize-y"
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Daily Send Limit (Safety)</label>
                        <input
                            type="number"
                            name="limit"
                            value={config.limit}
                            onChange={handleChange}
                            disabled={running}
                            className="bg-background border border-border rounded-lg p-2.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50"
                        />
                    </div>

                    <button
                        onClick={handleStart}
                        disabled={running}
                        className={`mt-4 w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${running
                            ? 'bg-gray-800 text-gray-400 cursor-not-allowed'
                            : 'bg-[#25D366] hover:bg-[#1DA851] text-white shadow-lg shadow-green-500/20'
                            }`}
                    >
                        <Send size={18} className={running ? "" : "fill-current"} />
                        {running ? 'Automation Running...' : 'Launch Automation'}
                    </button>
                </div>
            </div>

            {/* Terminal View */}
            <div className="lg:w-2/3 flex flex-col h-[calc(100vh-8rem)]">
                <div className="bg-[#0D1117] border border-[#30363D] rounded-xl flex-1 flex flex-col overflow-hidden shadow-xl">
                    <div className="bg-[#161B22] border-b border-[#30363D] px-4 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-300 text-sm font-mono">
                            <Terminal size={16} />
                            <span>whatsapp-service.log</span>
                        </div>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto font-mono text-sm leading-relaxed text-gray-300">
                        {logs.length === 0 ? (
                            <p className="text-gray-500 italic">No logs available. Ready to start message delivery loop.</p>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="mb-1 break-words">
                                    <span className="text-gray-600 mr-3">[{new Date().toLocaleTimeString()}]</span>
                                    <span className={
                                        log.includes('Error') || log.includes('❌') || log.includes('🛑') ? 'text-red-400' :
                                            log.includes('✅') || log.includes('🎉') ? 'text-green-400' :
                                                log.includes('🚀') ? 'text-blue-400 font-bold' :
                                                    'text-gray-300'
                                    }>
                                        {log}
                                    </span>
                                </div>
                            ))
                        )}
                        {running && (
                            <div className="mt-4 flex items-center gap-3 text-[#25D366]">
                                <div className="w-2 h-2 rounded-full bg-[#25D366] animate-ping"></div>
                                <span className="text-xs">Playwright iterating through Google Sheet...</span>
                            </div>
                        )}
                        <div ref={endOfLogsRef} />
                    </div>
                </div>
            </div>

        </div>
    );
}
