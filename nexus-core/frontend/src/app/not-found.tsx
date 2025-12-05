'use client';

import Link from 'next/link';
import { VisualButton } from '@/components/ui';

export default function NotFound() {
    return (
        <main className="min-h-screen bg-background app-grid-pattern flex items-center justify-center p-4">
            <div className="glass-card max-w-md w-full p-8 text-center space-y-6">
                <div className="w-24 h-24 bg-nexus-secondary/10 rounded-full flex items-center justify-center mx-auto animate-float">
                    <span className="text-4xl">🤔</span>
                </div>

                <div className="space-y-2">
                    <h1 className="text-2xl font-bold text-foreground">Page Not Found</h1>
                    <p className="text-muted-foreground">
                        Oops! We couldn&apos;t find the page you&apos;re looking for.
                    </p>
                </div>

                <div className="flex justify-center pt-4">
                    <Link href="/">
                        <VisualButton
                            icon={<span className="text-xl">🏠</span>}
                            label="Go Home"
                            variant="primary"
                            size="md"
                            ariaLabel="Return to home page"
                        />
                    </Link>
                </div>
            </div>
        </main>
    );
}
