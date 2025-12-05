'use client';

import { useEffect } from 'react';
import { VisualButton } from '@/components/ui';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error(error);
    }, [error]);

    return (
        <main className="min-h-screen bg-background app-grid-pattern flex items-center justify-center p-4">
            <div className="glass-card max-w-md w-full p-8 text-center space-y-6 border-nexus-error/30">
                <div className="w-24 h-24 bg-nexus-error/10 rounded-full flex items-center justify-center mx-auto animate-shake">
                    <span className="text-4xl">😕</span>
                </div>

                <div className="space-y-2">
                    <h1 className="text-2xl font-bold text-foreground">Something went wrong!</h1>
                    <p className="text-muted-foreground">
                        Don&apos;t worry, we can try again.
                    </p>
                </div>

                <div className="flex justify-center pt-4">
                    <VisualButton
                        icon={<span className="text-xl">↻</span>}
                        label="Try Again"
                        variant="secondary"
                        size="md"
                        onClick={reset}
                        ariaLabel="Try again"
                    />
                </div>
            </div>
        </main>
    );
}
