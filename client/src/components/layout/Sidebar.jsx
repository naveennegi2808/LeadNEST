"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Search, MessageSquare, Database, Settings } from 'lucide-react';

const routes = [
    { href: '/scrape', label: 'GMB Scrape', icon: Search },
    { href: '/whatsapp', label: 'WhatsApp', icon: MessageSquare },
    { href: '/sheets', label: 'Google Sheets', icon: Database },
];

export function Sidebar({ className }) {
    const pathname = usePathname();

    return (
        <aside className={`${className} bg-card border-r border-border flex flex-col`}>
            <div className="p-6">
                <h1 className="text-xl font-bold flex items-center gap-2">
                    <span className="text-blue-500">Lead</span>NEST
                </h1>
            </div>
            <nav className="flex-1 px-4 space-y-2">
                {routes.map((route) => {
                    const active = pathname === route.href;
                    return (
                        <Link
                            key={route.href}
                            href={route.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${active
                                ? 'bg-blue-500/10 text-blue-500'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <route.icon size={20} />
                            <span className="font-medium">{route.label}</span>
                        </Link>
                    );
                })}
            </nav>
            <div className="p-4 border-t border-border mt-auto">
                <p className="text-xs text-gray-500 text-center">v1.0.0</p>
            </div>
        </aside>
    );
}
