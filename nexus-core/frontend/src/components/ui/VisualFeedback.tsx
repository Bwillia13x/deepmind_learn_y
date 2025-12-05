'use client';

/**
 * VisualFeedback Component
 *
 * Provides immediate visual feedback for children's actions.
 * Uses colors, animations, and icons to communicate success/error without text.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export type FeedbackType = 'success' | 'error' | 'warning' | 'info' | 'celebration';

export interface VisualFeedbackProps {
    /** Type of feedback to display */
    type: FeedbackType;
    /** Whether the feedback is visible */
    visible: boolean;
    /** Size of the feedback indicator */
    size?: 'sm' | 'md' | 'lg';
    /** Animation style */
    animation?: 'bounce' | 'pulse' | 'shake' | 'none';
    /** Additional CSS classes */
    className?: string;
    /** Duration before auto-hide (ms), 0 = no auto-hide */
    autoHideDuration?: number;
    /** Callback when feedback should hide */
    onHide?: () => void;
}

const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
} as const;

const animationClasses = {
    bounce: 'animate-bounce',
    pulse: 'animate-pulse',
    shake: 'animate-shake',
    none: '',
} as const;

const bgClasses = {
    success: 'bg-nexus-success/20',
    error: 'bg-nexus-error/20',
    warning: 'bg-nexus-warning/20',
    info: 'bg-nexus-primary/20',
    celebration: 'bg-gradient-to-br from-pink-200 via-purple-200 to-yellow-200',
} as const;

function SuccessIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('text-nexus-success', className)}
        >
            <path d="M20 6L9 17l-5-5" />
        </svg>
    );
}

function ErrorIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('text-nexus-error', className)}
        >
            <path d="M18 6L6 18M6 6l12 12" />
        </svg>
    );
}

function WarningIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('text-nexus-warning', className)}
        >
            <path d="M12 9v4M12 17h.01" />
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
    );
}

function InfoIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('text-primary', className)}
        >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4M12 8h.01" />
        </svg>
    );
}

function CelebrationIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            viewBox="0 0 100 100"
            className={className}
        >
            {/* Star */}
            <path
                d="M50 10L61 40H91L67 58L78 88L50 70L22 88L33 58L9 40H39L50 10Z"
                fill="gold"
                stroke="orange"
                strokeWidth="2"
            />
            {/* Sparkles */}
            <circle cx="25" cy="25" r="3" fill="pink" className="animate-ping" />
            <circle cx="75" cy="25" r="3" fill="cyan" className="animate-ping" />
            <circle cx="25" cy="75" r="3" fill="lime" className="animate-ping" />
            <circle cx="75" cy="75" r="3" fill="purple" className="animate-ping" />
        </svg>
    );
}

export function VisualFeedback({
    type,
    visible,
    size = 'md',
    animation = 'bounce',
    className,
    autoHideDuration = 2000,
    onHide,
}: VisualFeedbackProps): React.ReactElement | null {
    const [isVisible, setIsVisible] = React.useState(visible);

    React.useEffect(() => {
        setIsVisible(visible);

        if (visible && autoHideDuration > 0 && onHide) {
            const timer = setTimeout(() => {
                setIsVisible(false);
                onHide();
            }, autoHideDuration);

            return () => clearTimeout(timer);
        }

        return undefined;
    }, [visible, autoHideDuration, onHide]);

    if (!isVisible) {
        return null;
    }

    const iconSizeClass = size === 'sm' ? 'w-8 h-8' : size === 'md' ? 'w-12 h-12' : 'w-16 h-16';

    const icons: Record<FeedbackType, React.ReactElement> = {
        success: <SuccessIcon className={iconSizeClass} />,
        error: <ErrorIcon className={iconSizeClass} />,
        warning: <WarningIcon className={iconSizeClass} />,
        info: <InfoIcon className={iconSizeClass} />,
        celebration: <CelebrationIcon className={iconSizeClass} />,
    };

    return (
        <div
            role="status"
            aria-live="polite"
            className={cn(
                'flex items-center justify-center rounded-full',
                sizeClasses[size],
                bgClasses[type],
                animationClasses[animation],
                'transition-all duration-300',
                className
            )}
        >
            {icons[type]}
        </div>
    );
}

export default VisualFeedback;
