'use client';

/**
 * AudioVisualizer Component
 *
 * Displays a visual representation of audio levels.
 * Uses Web Audio API to analyze microphone input.
 * Child-friendly with smooth animations and calming colors.
 */

import * as React from 'react';
import { cn } from '@/lib/utils/cn';
import { useSessionStore, type SessionState } from '@/lib/store/useSessionStore';

export interface AudioVisualizerProps {
    /** Number of bars to display */
    bars?: number;
    /** Height of the visualizer in pixels */
    height?: number;
    /** Visual variant */
    variant?: 'bars' | 'wave' | 'circle';
    /** Color theme */
    color?: 'primary' | 'success' | 'secondary';
    /** Whether the visualizer is active */
    active?: boolean;
    /** Additional CSS classes */
    className?: string;
}

const colorClasses = {
    primary: 'bg-nexus-primary',
    success: 'bg-nexus-success',
    secondary: 'bg-nexus-secondary',
} as const;

export function AudioVisualizer({
    bars = 5,
    height = 60,
    variant = 'bars',
    color = 'primary',
    active: propActive,
    className,
}: AudioVisualizerProps): React.ReactElement {
    const [levels, setLevels] = React.useState<number[]>(Array(bars).fill(0));
    const isMicOn = useSessionStore((state: SessionState) => state.isMicOn);
    const isAISpeaking = useSessionStore((state: SessionState) => state.isAISpeaking);

    const isActive = propActive ?? (isMicOn || isAISpeaking);

    // Simulate audio levels when active (for demo purposes)
    // In production, this would connect to actual audio analysis
    React.useEffect(() => {
        if (!isActive) {
            setLevels(Array(bars).fill(0));
            return;
        }

        const interval = setInterval(() => {
            setLevels(
                Array(bars)
                    .fill(0)
                    .map(() => Math.random() * 0.7 + 0.1)
            );
        }, 100);

        return () => clearInterval(interval);
    }, [isActive, bars]);

    if (variant === 'circle') {
        return (
            <div
                className={cn(
                    'relative flex items-center justify-center',
                    className
                )}
                style={{ width: height, height }}
                role="img"
                aria-label={isActive ? 'Audio active' : 'Audio inactive'}
            >
                {levels.map((level, i) => {
                    const size = height * (0.5 + level * 0.5);
                    const rotation = (i * 360) / bars;
                    return (
                        <div
                            key={i}
                            className={cn(
                                'absolute rounded-full transition-all duration-100',
                                colorClasses[color],
                                isActive ? 'opacity-60' : 'opacity-20'
                            )}
                            style={{
                                width: size,
                                height: size,
                                transform: `rotate(${rotation}deg)`,
                            }}
                        />
                    );
                })}
            </div>
        );
    }

    if (variant === 'wave') {
        return (
            <svg
                className={cn('w-full', className)}
                height={height}
                viewBox={`0 0 ${bars * 20} ${height}`}
                role="img"
                aria-label={isActive ? 'Audio active' : 'Audio inactive'}
            >
                <path
                    d={levels
                        .map((level, i) => {
                            const x = i * 20 + 10;
                            const y = height / 2 - level * (height / 2 - 4);
                            return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
                        })
                        .join(' ')}
                    fill="none"
                    className={cn(
                        'transition-all duration-100',
                        isActive
                            ? color === 'primary'
                                ? 'stroke-primary'
                                : color === 'success'
                                    ? 'stroke-success'
                                    : 'stroke-secondary'
                            : 'stroke-muted'
                    )}
                    strokeWidth="3"
                    strokeLinecap="round"
                />
            </svg>
        );
    }

    // Default: bars
    return (
        <div
            className={cn('flex items-end justify-center gap-1', className)}
            style={{ height }}
            role="img"
            aria-label={isActive ? 'Audio active' : 'Audio inactive'}
        >
            {levels.map((level, i) => (
                <div
                    key={i}
                    className={cn(
                        'w-2 rounded-full transition-all duration-100',
                        colorClasses[color],
                        isActive ? 'opacity-80' : 'opacity-20'
                    )}
                    style={{
                        height: `${Math.max(8, level * height)}px`,
                        animationDelay: `${i * 50}ms`,
                    }}
                />
            ))}
        </div>
    );
}

export default AudioVisualizer;
