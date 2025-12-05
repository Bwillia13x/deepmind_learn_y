'use client';

/**
 * ProgressIndicator Component
 *
 * Visual progress feedback designed for young learners.
 * Shows progress through icons, colors, and animations rather than numbers.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ProgressIndicatorProps {
    /** Current progress (0-100) */
    value: number;
    /** Show as steps (discrete) or smooth progress */
    variant?: 'smooth' | 'steps';
    /** Number of steps (only for steps variant) */
    steps?: number;
    /** Size variant */
    size?: 'sm' | 'md' | 'lg';
    /** Show celebration animation when complete */
    celebrateOnComplete?: boolean;
    /** Custom colors */
    color?: 'primary' | 'success' | 'secondary';
    /** Additional CSS classes */
    className?: string;
    /** Accessibility label */
    ariaLabel?: string;
}

const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
} as const;

const colorClasses = {
    primary: 'bg-nexus-primary',
    success: 'bg-nexus-success',
    secondary: 'bg-nexus-secondary',
} as const;

export function ProgressIndicator({
    value,
    variant = 'smooth',
    steps = 5,
    size = 'md',
    celebrateOnComplete = true,
    color = 'primary',
    className,
    ariaLabel = 'Progress',
}: ProgressIndicatorProps): React.ReactElement {
    const clampedValue = Math.max(0, Math.min(100, value));
    const isComplete = clampedValue >= 100;

    if (variant === 'steps') {
        const completedSteps = Math.floor((clampedValue / 100) * steps);

        return (
            <div
                role="progressbar"
                aria-valuenow={clampedValue}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={ariaLabel}
                className={cn('flex gap-2', className)}
            >
                {Array.from({ length: steps }).map((_, index) => (
                    <div
                        key={index}
                        className={cn(
                            'flex-1 rounded-full transition-all duration-300',
                            sizeClasses[size],
                            index < completedSteps
                                ? colorClasses[color]
                                : 'bg-muted',
                            index < completedSteps && 'scale-110',
                            isComplete && celebrateOnComplete && 'animate-bounce'
                        )}
                    />
                ))}
            </div>
        );
    }

    return (
        <div
            role="progressbar"
            aria-valuenow={clampedValue}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={ariaLabel}
            className={cn(
                'relative w-full rounded-full bg-muted overflow-hidden',
                sizeClasses[size],
                className
            )}
        >
            <div
                className={cn(
                    'h-full rounded-full transition-all duration-500 ease-out',
                    colorClasses[color],
                    isComplete && celebrateOnComplete && 'animate-pulse'
                )}
                style={{ width: `${clampedValue}%` }}
            />

            {/* Celebration sparkles when complete */}
            {isComplete && celebrateOnComplete && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-white/30" />
                </div>
            )}
        </div>
    );
}

export default ProgressIndicator;
