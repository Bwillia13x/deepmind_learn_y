import { LoadingSpinner } from '@/components/ui';

export default function Loading() {
    return (
        <main className="min-h-screen bg-background app-grid-pattern flex items-center justify-center">
            <div className="glass-card p-8 flex flex-col items-center gap-4">
                <LoadingSpinner size="lg" variant="orbit" color="primary" />
                <p className="text-muted-foreground font-medium animate-pulse">Loading NEXUS...</p>
            </div>
        </main>
    );
}
