'use client';

/**
 * LatencyIndicator Component
 *
 * Displays real-time response latency metrics.
 * Child-friendly with color-coded feedback (green = fast, yellow = ok, red = slow).
 */

import * as React from 'react';
import { cn } from '@/lib/utils/cn';
import { useSessionStore, type SessionState, type LatencyMetric } from '@/lib/store/useSessionStore';

export interface LatencyIndicatorProps {
    /** Override latency value (ms) - if not provided, uses store */
    latency?: number;
    /** Show numeric value */
    showValue?: boolean;
    /** Size variant */
    size?: 'sm' | 'md' | 'lg';
    /** Additional CSS classes */
    className?: string;
}

const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
} as const;

const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
} as const;

function getLatencyStatus(latencyMs: number): {
    color: string;
    label: string;
    textColor: string;
} {
    if (latencyMs < 200) {
        return {
            color: 'bg-nexus-success',
            label: 'Fast',
            textColor: 'text-nexus-success',
        };
    }
    if (latencyMs < 500) {
        return {
            color: 'bg-nexus-warning',
            label: 'Good',
            textColor: 'text-nexus-warning',
        };
    }
    return {
        color: 'bg-nexus-error',
        label: 'Slow',
        textColor: 'text-nexus-error',
    };
}

export function LatencyIndicator({
    latency: propLatency,
    showValue = true,
    size = 'md',
    className,
}: LatencyIndicatorProps): React.ReactElement {
    const latencyMetrics = useSessionStore((state: SessionState) => state.latencyMetrics);

    // Get the most recent latency value
    const latency = propLatency ?? (latencyMetrics.length > 0
        ? latencyMetrics[latencyMetrics.length - 1].value
        : 0);

    const { color, label, textColor } = getLatencyStatus(latency);

    // Calculate average latency for tooltip
    const avgLatency = latencyMetrics.length > 0
        ? Math.round(
            latencyMetrics.reduce((sum: number, m: LatencyMetric) => sum + m.value, 0) / latencyMetrics.length
        )
        : 0;

    if (latency === 0) {
        return (
            <div
                className={cn(
                    'flex items-center gap-2',
                    textSizeClasses[size],
                    'text-muted-foreground',
                    className
                )}
            >
                <div className={cn('rounded-full bg-muted animate-pulse', sizeClasses[size])} />
                {showValue && <span>Waiting...</span>}
            </div>
        );
    }

    return (
        <div
            className={cn(
                'flex items-center gap-2',
                textSizeClasses[size],
                className
            )}
            title={`Average: ${avgLatency}ms`}
        >
            <div
                className={cn(
                    'rounded-full transition-colors duration-300',
                    sizeClasses[size],
                    color
                )}
            />
            {showValue && (
                <span className={cn('font-mono', textColor)}>
                    {Math.round(latency)}ms
                </span>
            )}
            <span className="text-muted-foreground text-xs">
                ({label})
            </span>
        </div>
    );
}

/**
 * LatencyGraph Component
 *
 * Shows a mini sparkline graph of recent latency values.
 */
export interface LatencyGraphProps {
    /** Width of the graph */
    width?: number;
    /** Height of the graph */
    height?: number;
    /** Number of points to show */
    points?: number;
    /** Additional CSS classes */
    className?: string;
}

export function LatencyGraph({
    width = 100,
    height = 30,
    points = 20,
    className,
}: LatencyGraphProps): React.ReactElement {
    const latencyMetrics = useSessionStore((state: SessionState) => state.latencyMetrics);

    // Get last N points
    const data = latencyMetrics.slice(-points);

    if (data.length < 2) {
        return (
            <div
                className={cn('flex items-center justify-center text-muted-foreground text-xs', className)}
                style={{ width, height }}
            >
                No data yet
            </div>
        );
    }

    // Calculate min/max for scaling
    const values = data.map((m: LatencyMetric) => m.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    // Build SVG path
    const pathPoints = data.map((metric: LatencyMetric, i: number) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((metric.value - min) / range) * (height - 4) - 2;
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    // Determine color based on average
    const avg = values.reduce((a: number, b: number) => a + b, 0) / values.length;
    const strokeColor = avg < 200 ? 'stroke-success' : avg < 500 ? 'stroke-warning' : 'stroke-destructive';

    return (
        <svg
            width={width}
            height={height}
            className={cn('overflow-visible', className)}
            role="img"
            aria-label={`Latency graph, average ${Math.round(avg)}ms`}
        >
            <path
                d={pathPoints}
                fill="none"
                className={cn('transition-colors duration-300', strokeColor)}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            {/* Latest point dot */}
            {data.length > 0 && (
                <circle
                    cx={width}
                    cy={height - ((data[data.length - 1].value - min) / range) * (height - 4) - 2}
                    r="3"
                    className={cn('fill-current', strokeColor.replace('stroke-', 'text-'))}
                />
            )}
        </svg>
    );
}

export default LatencyIndicator;
