'use client';

/**
 * ConnectionStatus Component
 *
 * Displays the current WebSocket connection status with visual indicator.
 * Shows reconnection attempt count during reconnection.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useSessionStore, type ConnectionStatus as ConnectionStatusType, type SessionState } from '@/lib/store/useSessionStore';

// === Types ===

export interface ConnectionStatusProps {
    className?: string;
    showLabel?: boolean;
}

// === Status Configuration ===

const statusConfig: Record<
    ConnectionStatusType,
    { color: string; label: string; animate?: boolean }
> = {
    disconnected: { color: 'bg-gray-400', label: 'Disconnected' },
    connecting: { color: 'bg-nexus-warning', label: 'Connecting...', animate: true },
    connected: { color: 'bg-nexus-success', label: 'Connected' },
    reconnecting: { color: 'bg-nexus-warning', label: 'Reconnecting...', animate: true },
    error: { color: 'bg-nexus-error', label: 'Error' },
};

// === Component ===

export function ConnectionStatus({
    className,
    showLabel = true,
}: ConnectionStatusProps): React.ReactElement {
    const status = useSessionStore((state: SessionState) => state.connectionStatus);
    const reconnectAttempt = useSessionStore((state: SessionState) => state.reconnectAttempt);
    const maxReconnectAttempts = useSessionStore((state: SessionState) => state.maxReconnectAttempts);
    const error = useSessionStore((state: SessionState) => state.error);

    const config = statusConfig[status];

    // Build label with reconnect attempt info
    let displayLabel = config.label;
    if (status === 'reconnecting' && reconnectAttempt > 0) {
        displayLabel = `Reconnecting (${reconnectAttempt}/${maxReconnectAttempts})...`;
    } else if (status === 'error' && error) {
        // Truncate error message for display
        displayLabel = error.length > 30 ? `${error.slice(0, 27)}...` : error;
    }

    return (
        <div className={cn('flex items-center gap-2', className)}>
            {/* Status dot */}
            <div className="relative">
                <div
                    className={cn(
                        'w-2.5 h-2.5 rounded-full',
                        config.color
                    )}
                />
                {config.animate && (
                    <div
                        className={cn(
                            'absolute inset-0 w-2.5 h-2.5 rounded-full animate-ping',
                            config.color,
                            'opacity-75'
                        )}
                    />
                )}
            </div>

            {/* Status label */}
            {showLabel && (
                <span
                    className={cn(
                        'text-xs',
                        status === 'error' ? 'text-destructive' : 'text-muted-foreground'
                    )}
                    title={status === 'error' && error ? error : undefined}
                >
                    {displayLabel}
                </span>
            )}
        </div>
    );
}

export default ConnectionStatus;
