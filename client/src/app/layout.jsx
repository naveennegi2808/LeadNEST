import { Inter } from 'next/font/google';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
    title: 'LeadNEST',
    description: 'GMB Scraper & WhatsApp Automation',
};

export default function RootLayout({ children }) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.className} bg-background text-foreground flex h-screen overflow-hidden`}>
                <Sidebar className="w-64 flex-shrink-0" />
                <main className="flex-1 overflow-y-auto p-8">
                    {children}
                </main>
            </body>
        </html>
    );
}
