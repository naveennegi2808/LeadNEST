"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useSearchParams } from 'next/navigation';
import { Database, Link as LinkIcon, AlertCircle, FileSpreadsheet, ExternalLink } from 'lucide-react';

export default function SheetsPage() {
    const searchParams = useSearchParams();
    const [loading, setLoading] = useState(false);
    const [connected, setConnected] = useState(false);
    const [sheetUrl, setSheetUrl] = useState(null);

    useEffect(() => {
        // Check URL params for immediate post-oauth redirect feedback
        if (searchParams.get('status') === 'success') {
            setConnected(true);
        }

        // Fetch actual backend status on mount to persist connection state across reloads
        const checkStatus = async () => {
            try {
                const res = await axios.get('http://localhost:8000/api/auth/status');
                if (res.data.authenticated) {
                    setConnected(true);
                }
            } catch (err) {
                console.error("Failed to check auth status", err);
            }
        };
        checkStatus();
    }, [searchParams]);

    const handleConnect = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/api/auth/url');
            if (res.data.url) {
                window.location.href = res.data.url;
            }
        } catch (err) {
            console.error(err);
            alert("Failed to connect to backend. Please ensure Python server is running on port 8000.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto mt-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold tracking-tight">Google Sheets Integration</h1>
                <p className="text-gray-400 mt-2">Connect your account to save scraped leads dynamically.</p>
            </div>

            <div className="bg-card border border-border rounded-xl p-8 shadow-sm">
                <div className="flex items-start gap-6">
                    <div className={`p-4 rounded-xl ${connected ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'}`}>
                        <FileSpreadsheet size={32} />
                    </div>

                    <div className="flex-1">
                        <h2 className="text-xl font-semibold mb-2">
                            {connected ? 'Status: Connected' : 'Google Account Not Connected'}
                        </h2>
                        <p className="text-gray-400 mb-6 max-w-2xl">
                            By connecting your Google account, the application will automatically create a new spreadsheet named "GMB Scraper Results" in your Drive to store all generated leads.
                        </p>

                        {connected && sheetUrl ? (
                            <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <Database className="text-green-500" size={20} />
                                    <span className="text-sm font-medium">Active Sheet: GMB Scraper Results</span>
                                </div>
                                <a
                                    href={sheetUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                >
                                    <span>Open Sheet</span>
                                    <ExternalLink size={16} />
                                </a>
                            </div>
                        ) : (
                            <button
                                onClick={handleConnect}
                                disabled={loading}
                                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
                            >
                                <LinkIcon size={18} />
                                {loading ? 'Generating Link...' : 'Connect Google Account'}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            <div className="mt-8 bg-orange-500/5 border border-orange-500/20 rounded-xl p-6 flex gap-4">
                <AlertCircle className="text-orange-500 shrink-0 mt-0.5" />
                <div>
                    <h4 className="font-semibold text-orange-500 mb-1">Prerequisite Setup Required</h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                        If this is your first time setting up the app, you must create Google OAuth 2.0 Client credentials in your Google Cloud Console and place the <code className="bg-black/20 px-1 py-0.5 rounded text-orange-400">client_secret.json</code> file in the backend <code className="bg-black/20 px-1 py-0.5 rounded text-orange-400">/server</code> folder.
                    </p>
                </div>
            </div>
        </div>
    );
}
