import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';

const inter = Inter({
    subsets: ['latin'],
    variable: '--font-inter',
});

export const metadata: Metadata = {
    title: 'NEXUS - Digital Para-Educator Assistant',
    description:
        'AI-powered oracy practice partner for Alberta K-12 EAL students',
    keywords: [
        'education',
        'EAL',
        'English learners',
        'oracy',
        'speaking practice',
        'Alberta curriculum',
        'AI assistant',
    ],
    authors: [{ name: 'NEXUS Team' }],
    robots: 'noindex, nofollow', // Educational tool, not public-facing
    manifest: '/manifest.json',
    appleWebApp: {
        capable: true,
        statusBarStyle: 'default',
        title: 'NEXUS',
    },
    formatDetection: {
        telephone: false,
    },
};

export const viewport: Viewport = {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false, // Prevent zoom on mobile for voice interface
    themeColor: [
        { media: '(prefers-color-scheme: light)', color: '#2563eb' },
        { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
    ],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}): React.ReactElement {
    return (
        <html lang="en" suppressHydrationWarning>
            <head>
                {/* PWA Meta Tags */}
                <link rel="apple-touch-icon" href="/icon-192.png" />
                <meta name="apple-mobile-web-app-capable" content="yes" />
                <meta name="mobile-web-app-capable" content="yes" />
            </head>
            <body
                className={`${inter.variable} font-sans antialiased bg-background text-foreground`}
            >
                {children}
            </body>
        </html>
    );
}
