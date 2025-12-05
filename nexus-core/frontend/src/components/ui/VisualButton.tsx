'use client';

/**
 * VisualButton Component
 *
 * A large, accessible button designed for children and EAL students.
 * Features large touch targets, clear icons, and visual feedback.
 * Minimizes reliance on text for navigation.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface VisualButtonProps {
    /** Icon component to display */
    icon: React.ReactNode;
    /** Optional label text (shown below icon) */
    label?: string;
    /** Color variant */
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'ghost';
    /** Size variant */
    size?: 'sm' | 'md' | 'lg' | 'xl';
    /** Disabled state */
    disabled?: boolean;
    /** Loading state - shows spinner */
    loading?: boolean;
    /** Click handler */
    onClick?: () => void;
    /** Additional CSS classes */
    className?: string;
    /** Accessibility label (required for screen readers) */
    ariaLabel: string;
}

const sizeClasses = {
    sm: 'w-16 h-16 p-3',
    md: 'w-20 h-20 p-4',
    lg: 'w-28 h-28 p-5',
    xl: 'w-36 h-36 p-6',
} as const;

const iconSizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
    xl: 'w-18 h-18',
} as const;

const variantClasses = {
    primary: 'bg-nexus-primary hover:bg-nexus-primary/90 text-white shadow-lg shadow-nexus-primary/25',
    secondary: 'bg-nexus-secondary hover:bg-nexus-secondary/90 text-white shadow-lg shadow-nexus-secondary/25',
    success: 'bg-nexus-success hover:bg-nexus-success/90 text-white shadow-lg shadow-nexus-success/25',
    warning: 'bg-nexus-warning hover:bg-nexus-warning/90 text-white shadow-lg shadow-nexus-warning/25',
    ghost: 'bg-muted hover:bg-muted/80 text-muted-foreground',
} as const;

export function VisualButton({
    icon,
    label,
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    onClick,
    className,
    ariaLabel,
}: VisualButtonProps): React.ReactElement {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled || loading}
            aria-label={ariaLabel}
            aria-busy={loading}
            className={cn(
                'relative flex flex-col items-center justify-center rounded-2xl',
                'transition-all duration-200 ease-out',
                'focus:outline-none focus:ring-4 focus:ring-offset-2',
                'active:scale-95',
                sizeClasses[size],
                variantClasses[variant],
                disabled && 'opacity-50 cursor-not-allowed',
                loading && 'cursor-wait',
                className
            )}
        >
            {/* Icon container */}
            <div className={cn('flex items-center justify-center', iconSizes[size])}>
                {loading ? (
                    <LoadingSpinner className={iconSizes[size]} />
                ) : (
                    icon
                )}
            </div>

            {/* Optional label */}
            {label && !loading && (
                <span className="mt-1 text-xs font-medium truncate max-w-full px-1">
                    {label}
                </span>
            )}

            {/* Ripple effect on press */}
            <span className="absolute inset-0 rounded-2xl overflow-hidden">
                <span className="absolute inset-0 bg-white/20 opacity-0 active:opacity-100 transition-opacity" />
            </span>
        </button>
    );
}

function LoadingSpinner({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            className={cn('animate-spin', className)}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
        >
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
            />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
        </svg>
    );
}

export default VisualButton;
