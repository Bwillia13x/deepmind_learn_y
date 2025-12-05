'use client';

/**
 * VoiceOrb Component
 *
 * The central animated orb interface for voice interaction.
 * Visual states: idle, listening, processing, speaking, error.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useSessionStore, type SessionState } from '@/lib/store/useSessionStore';

// === Types ===

export type OrbState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceOrbProps {
    state?: OrbState;
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    onClick?: () => void;
    className?: string;
}

// === Size Mappings ===

const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-36 h-36',
    lg: 'w-48 h-48',
} as const;

const innerSizeClasses = {
    sm: 'w-20 h-20',
    md: 'w-28 h-28',
    lg: 'w-40 h-40',
} as const;

// === State Color Mappings ===

const stateColors = {
    idle: {
        outer: 'bg-nexus-primary/20',
        inner: 'bg-nexus-primary/40',
        core: 'bg-nexus-primary',
    },
    listening: {
        outer: 'bg-nexus-success/30',
        inner: 'bg-nexus-success/50',
        core: 'bg-nexus-success',
    },
    processing: {
        outer: 'bg-nexus-secondary/30',
        inner: 'bg-nexus-secondary/50',
        core: 'bg-nexus-secondary',
    },
    speaking: {
        outer: 'bg-nexus-primary/40',
        inner: 'bg-nexus-primary/60',
        core: 'bg-nexus-primary',
    },
    error: {
        outer: 'bg-nexus-error/30',
        inner: 'bg-nexus-error/50',
        core: 'bg-nexus-error',
    },
} as const;

// === Animation Classes ===

const animationClasses = {
    idle: 'animate-float',
    listening: 'animate-pulse-ring',
    processing: 'animate-spin',
    speaking: 'animate-speak-wave',
    error: 'animate-shake',
} as const;

// === Component ===

export function VoiceOrb({
    state: propState,
    size = 'md',
    disabled = false,
    onClick,
    className,
}: VoiceOrbProps): React.ReactElement {
    // Get state from store if not provided via props
    const storeState = useSessionStore((s: SessionState): OrbState => {
        if (s.connectionStatus === 'error') return 'error';
        if (s.isAISpeaking) return 'speaking';
        if (s.isMicOn) return 'listening';
        if (s.connectionStatus === 'connected') return 'processing';
        return 'idle';
    });

    const state: OrbState = propState ?? storeState;
    const colors = stateColors[state];
    const animation = animationClasses[state];

    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className={cn(
                'relative flex items-center justify-center rounded-full transition-all duration-300',
                'focus:outline-none focus:ring-4 focus:ring-primary/30',
                'hover:scale-105 active:scale-95',
                disabled && 'opacity-50 cursor-not-allowed hover:scale-100 active:scale-100',
                sizeClasses[size],
                colors.outer,
                animation,
                className
            )}
            aria-label={`Voice assistant - ${state}`}
        >
            {/* Middle Ring */}
            <div
                className={cn(
                    'absolute rounded-full transition-all duration-300',
                    innerSizeClasses[size],
                    colors.inner,
                    state === 'listening' && 'animate-ping'
                )}
            />

            {/* Core */}
            <div
                className={cn(
                    'relative rounded-full transition-all duration-300',
                    size === 'sm' && 'w-12 h-12',
                    size === 'md' && 'w-16 h-16',
                    size === 'lg' && 'w-24 h-24',
                    colors.core,
                    'shadow-lg shadow-primary/30'
                )}
            >
                {/* Icon based on state */}
                <div className="absolute inset-0 flex items-center justify-center text-white">
                    {state === 'idle' && <MicrophoneIcon className="w-6 h-6" />}
                    {state === 'listening' && <WaveformIcon className="w-6 h-6" />}
                    {state === 'processing' && <SpinnerIcon className="w-6 h-6 animate-spin" />}
                    {state === 'speaking' && <SpeakerIcon className="w-6 h-6" />}
                    {state === 'error' && <ExclamationIcon className="w-6 h-6" />}
                </div>
            </div>

            {/* Pulse rings for listening state */}
            {state === 'listening' && (
                <>
                    <div
                        className={cn(
                            'absolute rounded-full border-2 border-success/30 animate-ping',
                            sizeClasses[size]
                        )}
                        style={{ animationDuration: '1.5s' }}
                    />
                    <div
                        className={cn(
                            'absolute rounded-full border-2 border-success/20 animate-ping',
                            sizeClasses[size]
                        )}
                        style={{ animationDuration: '2s', animationDelay: '0.5s' }}
                    />
                </>
            )}
        </button>
    );
}

// === Icons ===

function MicrophoneIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 1 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v1a7 7 0 0 1-14 0v-1a1 1 0 1 1 2 0v1a5 5 0 0 0 10 0v-1a1 1 0 1 1 2 0Z" />
            <path d="M12 19a1 1 0 0 1 1 1v2a1 1 0 1 1-2 0v-2a1 1 0 0 1 1-1Z" />
        </svg>
    );
}

function WaveformIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path d="M3 12h2v4H3v-4Zm4-6h2v16H7V6Zm4-4h2v24h-2V2Zm4 4h2v16h-2V6Zm4 6h2v4h-2v-4Z" />
        </svg>
    );
}

function SpinnerIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={className}
        >
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
    );
}

function SpeakerIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path d="M11 5 6 9H2v6h4l5 4V5Zm5.54 3.46a5 5 0 0 1 0 7.07l-1.41-1.41a3 3 0 0 0 0-4.24l1.41-1.42Zm2.83-2.83a9 9 0 0 1 0 12.73l-1.41-1.41a7 7 0 0 0 0-9.9l1.41-1.42Z" />
        </svg>
    );
}

function ExclamationIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path
                fillRule="evenodd"
                d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm0 8.625a1.125 1.125 0 0 1 1.125 1.125v3.75a1.125 1.125 0 0 1-2.25 0v-3.75A1.125 1.125 0 0 1 12 10.875Zm0-4.875a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25Z"
                clipRule="evenodd"
            />
        </svg>
    );
}

export default VoiceOrb;
