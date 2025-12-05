/**
 * Offline Indicator Component
 *
 * Shows network status and offline mode information to users.
 * Appears when offline or when updates are available.
 */

'use client';

import * as React from 'react';
import { useServiceWorker } from '@/lib/hooks';
import { cn } from '@/lib/utils';

export interface OfflineIndicatorProps {
    className?: string;
}

export function OfflineIndicator({ className }: OfflineIndicatorProps): React.ReactElement | null {
    const { isOnline, updateAvailable, skipWaiting } = useServiceWorker();
    const [dismissed, setDismissed] = React.useState(false);

    // Reset dismissed state when coming back online
    React.useEffect(() => {
        if (isOnline) {
            setDismissed(false);
        }
    }, [isOnline]);

    // Don't show if online and no update, or if dismissed
    if ((isOnline && !updateAvailable) || dismissed) {
        return null;
    }

    return (
        <div
            className={cn(
                'fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-sm',
                'z-50 animate-in slide-in-from-bottom-4 duration-300',
                className
            )}
            role="status"
            aria-live="polite"
        >
            {!isOnline ? (
                // Offline notification
                <div className="bg-nexus-warning text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
                    <div className="flex-shrink-0">
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M18.364 5.636a9 9 0 010 12.728m-3.536-3.536a5 5 0 010-7.072M13 12a1 1 0 11-2 0 1 1 0 012 0z"
                            />
                            <line
                                x1="4"
                                y1="4"
                                x2="20"
                                y2="20"
                                stroke="currentColor"
                                strokeWidth={2}
                                strokeLinecap="round"
                            />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <p className="font-medium text-sm">You&apos;re offline</p>
                        <p className="text-xs opacity-90">
                            Audio will be queued and synced when you&apos;re back online.
                        </p>
                    </div>
                    <button
                        onClick={() => setDismissed(true)}
                        className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
                        aria-label="Dismiss"
                    >
                        <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>
            ) : updateAvailable ? (
                // Update available notification
                <div className="bg-nexus-primary text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
                    <div className="flex-shrink-0">
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <p className="font-medium text-sm">Update available</p>
                        <p className="text-xs opacity-90">
                            A new version of NEXUS is ready.
                        </p>
                    </div>
                    <button
                        onClick={skipWaiting}
                        className="flex-shrink-0 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                    >
                        Update
                    </button>
                </div>
            ) : null}
        </div>
    );
}

/**
 * Compact offline dot indicator for headers/status bars
 */
export function OfflineDot({ className }: { className?: string }): React.ReactElement | null {
    const { isOnline } = useServiceWorker();

    if (isOnline) {
        return null;
    }

    return (
        <span
            className={cn(
                'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full',
                'bg-warning/20 text-warning text-xs font-medium',
                className
            )}
            role="status"
        >
            <span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
            Offline
        </span>
    );
}
