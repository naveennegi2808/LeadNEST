"use client";

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Play, Square, Settings, Terminal } from 'lucide-react';

export default function ScrapePage() {
    const [running, setRunning] = useState(false);
    const [logs, setLogs] = useState([]);
    const [leadCount, setLeadCount] = useState(0);
    const [config, setConfig] = useState({
        keywords: '',
        relevanceKeywords: '',
        city: '',
        country: '',
        limit: 50
    });

    const endOfLogsRef = useRef(null);

    useEffect(() => {
        let interval;
        if (running) {
            interval = setInterval(async () => {
                try {
                    const res = await axios.get('http://localhost:8000/api/scrape/status');
                    setLogs(res.data.logs || []);
                    if (res.data.status === 'idle' && res.data.logs.some(l => l.includes('Done!'))) {
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

    useEffect(() => {
        const fetchLeadCount = async () => {
            try {
                const res = await axios.get('http://localhost:8000/api/auth/status/leads');
                setLeadCount(res.data.count);
            } catch (e) {
                // Ignore silent fail
            }
        };
        fetchLeadCount();
        const countInterval = setInterval(fetchLeadCount, 3000);
        return () => clearInterval(countInterval);
    }, []);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await axios.get('http://localhost:8000/api/scrape/status');
                if (res.data.status === 'running') {
                    setRunning(true);
                    setLogs(res.data.logs || []);
                }
            } catch (e) {
                console.error(e);
            }
        };
        fetchStatus();
    }, []);

    const handleStart = async () => {
        try {
            setRunning(true);
            setLogs(['Starting scraper service...']);
            await axios.post('http://localhost:8000/api/scrape/start', config);
        } catch (e) {
            alert("Failed to start scraper. Check backend is running.");
            setRunning(false);
        }
    };

    const handleStop = async () => {
        try {
            await axios.post('http://localhost:8000/api/scrape/stop');
            setRunning(false);
            setLogs(prev => [...prev, '🛑 Scraping manually stopped by user.']);
        } catch (e) {
            console.error(e);
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
                    <h1 className="text-3xl font-bold tracking-tight">Scraper Setup</h1>
                    <p className="text-gray-400 mt-2 text-sm">Configure your Google Maps lead generation.</p>
                </div>

                <div className="bg-blue-600/10 border border-blue-500/20 rounded-xl p-6 flex items-center justify-between shadow-sm">
                    <div>
                        <h3 className="text-sm font-medium text-blue-400">Total Live Leads in Sheet</h3>
                        <p className="text-xs text-gray-500 mt-1">Updates automatically</p>
                    </div>
                    <div className="text-4xl font-bold text-white tracking-tight">{leadCount}</div>
                </div>

                <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col gap-5">
                    <div className="flex items-center gap-2 pb-4 border-b border-border">
                        <Settings className="text-blue-500" size={20} />
                        <h3 className="font-semibold">Target Parameters</h3>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Target Keywords (comma separated)</label>
                        <textarea
                            name="keywords"
                            value={config.keywords}
                            onChange={handleChange}
                            disabled={running}
                            className="bg-background border border-border rounded-lg p-3 text-sm min-h-[80px] focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Website Relevance Keywords</label>
                        <p className="text-xs text-gray-500 mb-1">Only save leads if their website contains at least one of these words.</p>
                        <textarea
                            name="relevanceKeywords"
                            value={config.relevanceKeywords}
                            onChange={handleChange}
                            disabled={running}
                            className="bg-background border border-border rounded-lg p-3 text-sm min-h-[80px] focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 text-gray-400"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-gray-300">City</label>
                            <input
                                type="text"
                                name="city"
                                value={config.city}
                                onChange={handleChange}
                                disabled={running}
                                className="bg-background border border-border rounded-lg p-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                            />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-gray-300">Country</label>
                            <input
                                type="text"
                                name="country"
                                value={config.country}
                                onChange={handleChange}
                                disabled={running}
                                className="bg-background border border-border rounded-lg p-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                            />
                        </div>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Max Results to Scrape</label>
                        <input
                            type="number"
                            name="limit"
                            value={config.limit}
                            onChange={handleChange}
                            disabled={running}
                            className="bg-background border border-border rounded-lg p-2.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                        />
                    </div>

                    <button
                        onClick={running ? handleStop : handleStart}
                        className={`mt-4 w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${running
                            ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/20'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20'
                            }`}
                    >
                        {running ? (
                            <>
                                <Square size={18} className="fill-current" />
                                Stop Scraping
                            </>
                        ) : (
                            <>
                                <Play size={18} className="fill-current" />
                                Start Scraping
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Terminal View */}
            <div className="lg:w-2/3 flex flex-col h-[calc(100vh-8rem)]">
                <div className="bg-[#0D1117] border border-[#30363D] rounded-xl flex-1 flex flex-col overflow-hidden shadow-xl">
                    <div className="bg-[#161B22] border-b border-[#30363D] px-4 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-300 text-sm font-mono">
                            <Terminal size={16} />
                            <span>scraper-service.log</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                        </div>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto font-mono text-sm leading-relaxed text-gray-300">
                        {logs.length === 0 ? (
                            <p className="text-gray-500 italic">No logs available. Ready to start.</p>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="mb-1 break-words">
                                    <span className={
                                        log.includes('Error') || log.includes('❌') ? 'text-red-400' :
                                            log.includes('✅') || log.includes('Done!') ? 'text-green-400' :
                                                log.includes('═══') ? 'text-purple-400 font-bold' :
                                                    'text-gray-300'
                                    }>
                                        {log}
                                    </span>
                                </div>
                            ))
                        )}
                        {running && (
                            <div className="mt-4 flex items-center gap-3 text-blue-400">
                                <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
                                <span className="text-xs">Processing via browser cluster...</span>
                            </div>
                        )}
                        <div ref={endOfLogsRef} />
                    </div>
                </div>
            </div>
        </div>
    );
}
