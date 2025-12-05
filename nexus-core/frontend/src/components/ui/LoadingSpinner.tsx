'use client';

/**
 * LoadingSpinner Component
 *
 * Child-friendly loading indicators with playful animations.
 * Uses visual metaphors that children understand (bouncing dots, spinning stars).
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export type SpinnerVariant = 'dots' | 'star' | 'bounce' | 'pulse' | 'orbit';

export interface LoadingSpinnerProps {
    /** Visual variant of the spinner */
    variant?: SpinnerVariant;
    /** Size of the spinner */
    size?: 'sm' | 'md' | 'lg' | 'xl';
    /** Color theme */
    color?: 'primary' | 'secondary' | 'success' | 'white';
    /** Additional CSS classes */
    className?: string;
    /** Accessibility label */
    ariaLabel?: string;
}

const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
} as const;

const colorClasses = {
    primary: 'text-nexus-primary',
    secondary: 'text-nexus-secondary',
    success: 'text-nexus-success',
    white: 'text-white',
} as const;

function DotsSpinner({ className, color }: { className: string; color: string }): React.ReactElement {
    return (
        <div className={cn('flex items-center justify-center gap-1', className)}>
            <span
                className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    color === 'white' ? 'bg-white' : 'bg-current'
                )}
                style={{ animationDelay: '0ms' }}
            />
            <span
                className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    color === 'white' ? 'bg-white' : 'bg-current'
                )}
                style={{ animationDelay: '150ms' }}
            />
            <span
                className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    color === 'white' ? 'bg-white' : 'bg-current'
                )}
                style={{ animationDelay: '300ms' }}
            />
        </div>
    );
}

function StarSpinner({ className }: { className: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 50 50"
            className={cn('animate-spin', className)}
        >
            <path
                d="M25 5L30 20H45L33 28L38 43L25 33L12 43L17 28L5 20H20L25 5Z"
                fill="currentColor"
            />
        </svg>
    );
}

function BounceSpinner({ className }: { className: string }): React.ReactElement {
    return (
        <div className={cn('flex items-end justify-center gap-1', className)}>
            <div
                className="w-3 h-3 rounded-full bg-current animate-bounce"
                style={{ animationDuration: '600ms', animationDelay: '0ms' }}
            />
            <div
                className="w-4 h-4 rounded-full bg-current animate-bounce"
                style={{ animationDuration: '600ms', animationDelay: '100ms' }}
            />
            <div
                className="w-3 h-3 rounded-full bg-current animate-bounce"
                style={{ animationDuration: '600ms', animationDelay: '200ms' }}
            />
        </div>
    );
}

function PulseSpinner({ className }: { className: string }): React.ReactElement {
    return (
        <div className={cn('relative', className)}>
            <div className="absolute inset-0 rounded-full bg-current opacity-25 animate-ping" />
            <div className="relative rounded-full bg-current w-full h-full opacity-75" />
        </div>
    );
}

function OrbitSpinner({ className }: { className: string }): React.ReactElement {
    return (
        <div className={cn('relative', className)}>
            {/* Center dot */}
            <div className="absolute inset-1/3 rounded-full bg-current" />
            {/* Orbiting dot */}
            <div
                className="absolute w-3 h-3 rounded-full bg-current animate-spin"
                style={{
                    top: '0',
                    left: '50%',
                    marginLeft: '-6px',
                    animationDuration: '1s',
                    transformOrigin: '6px calc(50% + 6px)',
                }}
            />
        </div>
    );
}

export function LoadingSpinner({
    variant = 'dots',
    size = 'md',
    color = 'primary',
    className,
    ariaLabel = 'Loading',
}: LoadingSpinnerProps): React.ReactElement {
    const spinnerClasses = cn(
        sizeClasses[size],
        colorClasses[color],
        className
    );

    const variants: Record<SpinnerVariant, React.ReactElement> = {
        dots: <DotsSpinner className={spinnerClasses} color={color} />,
        star: <StarSpinner className={spinnerClasses} />,
        bounce: <BounceSpinner className={spinnerClasses} />,
        pulse: <PulseSpinner className={spinnerClasses} />,
        orbit: <OrbitSpinner className={spinnerClasses} />,
    };

    return (
        <div
            role="status"
            aria-label={ariaLabel}
            className="inline-flex items-center justify-center"
        >
            {variants[variant]}
            <span className="sr-only">{ariaLabel}</span>
        </div>
    );
}

export default LoadingSpinner;
