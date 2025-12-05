'use client';

/**
 * AnimatedCharacter Component
 *
 * A friendly animated character that provides visual feedback.
 * Designed to be welcoming and non-intimidating for young EAL students.
 * Uses simple expressions and animations to convey state.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export type CharacterMood = 'happy' | 'thinking' | 'listening' | 'talking' | 'sleeping' | 'wave';

export interface AnimatedCharacterProps {
    mood?: CharacterMood;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
} as const;

export function AnimatedCharacter({
    mood = 'happy',
    size = 'md',
    className,
}: AnimatedCharacterProps): React.ReactElement {
    return (
        <div
            className={cn(
                'relative flex items-center justify-center',
                sizeClasses[size],
                className
            )}
            role="img"
            aria-label={`Friendly character is ${mood}`}
        >
            <svg
                viewBox="0 0 100 100"
                className="w-full h-full"
                xmlns="http://www.w3.org/2000/svg"
            >
                {/* Face background */}
                <circle
                    cx="50"
                    cy="50"
                    r="45"
                    className={cn(
                        'transition-colors duration-500',
                        mood === 'happy' && 'fill-nexus-primary',
                        mood === 'thinking' && 'fill-nexus-secondary',
                        mood === 'listening' && 'fill-nexus-success',
                        mood === 'talking' && 'fill-nexus-primary',
                        mood === 'sleeping' && 'fill-muted',
                        mood === 'wave' && 'fill-nexus-warning'
                    )}
                />

                {/* Highlight */}
                <ellipse
                    cx="35"
                    cy="35"
                    rx="15"
                    ry="10"
                    className="fill-white/30"
                    transform="rotate(-30 35 35)"
                />

                {/* Eyes */}
                {mood === 'sleeping' ? (
                    <>
                        {/* Closed eyes */}
                        <path
                            d="M 30 45 Q 35 50 40 45"
                            stroke="white"
                            strokeWidth="3"
                            fill="none"
                            strokeLinecap="round"
                        />
                        <path
                            d="M 60 45 Q 65 50 70 45"
                            stroke="white"
                            strokeWidth="3"
                            fill="none"
                            strokeLinecap="round"
                        />
                    </>
                ) : (
                    <>
                        {/* Open eyes */}
                        <circle
                            cx="35"
                            cy="45"
                            r={mood === 'listening' ? '7' : '6'}
                            className="fill-white"
                        />
                        <circle
                            cx="65"
                            cy="45"
                            r={mood === 'listening' ? '7' : '6'}
                            className="fill-white"
                        />

                        {/* Pupils */}
                        <circle
                            cx={mood === 'thinking' ? '33' : '35'}
                            cy={mood === 'thinking' ? '43' : '45'}
                            r="3"
                            className={cn(
                                'fill-gray-800',
                                mood === 'thinking' && 'animate-pulse'
                            )}
                        />
                        <circle
                            cx={mood === 'thinking' ? '63' : '65'}
                            cy={mood === 'thinking' ? '43' : '45'}
                            r="3"
                            className={cn(
                                'fill-gray-800',
                                mood === 'thinking' && 'animate-pulse'
                            )}
                        />
                    </>
                )}

                {/* Mouth */}
                {mood === 'happy' && (
                    <path
                        d="M 35 65 Q 50 80 65 65"
                        stroke="white"
                        strokeWidth="4"
                        fill="none"
                        strokeLinecap="round"
                    />
                )}
                {mood === 'thinking' && (
                    <ellipse
                        cx="50"
                        cy="68"
                        rx="5"
                        ry="4"
                        className="fill-white"
                    />
                )}
                {mood === 'listening' && (
                    <ellipse
                        cx="50"
                        cy="65"
                        rx="8"
                        ry="6"
                        className="fill-white"
                    />
                )}
                {mood === 'talking' && (
                    <ellipse
                        cx="50"
                        cy="65"
                        rx="10"
                        ry="8"
                        className="fill-white animate-pulse"
                    />
                )}
                {mood === 'sleeping' && (
                    <path
                        d="M 40 65 Q 50 70 60 65"
                        stroke="white"
                        strokeWidth="3"
                        fill="none"
                        strokeLinecap="round"
                    />
                )}
                {mood === 'wave' && (
                    <path
                        d="M 35 65 Q 50 78 65 65"
                        stroke="white"
                        strokeWidth="4"
                        fill="none"
                        strokeLinecap="round"
                    />
                )}

                {/* Blush marks for happy/wave */}
                {(mood === 'happy' || mood === 'wave') && (
                    <>
                        <ellipse cx="25" cy="55" rx="5" ry="3" className="fill-pink-300/50" />
                        <ellipse cx="75" cy="55" rx="5" ry="3" className="fill-pink-300/50" />
                    </>
                )}

                {/* Z's for sleeping */}
                {mood === 'sleeping' && (
                    <text
                        x="70"
                        y="30"
                        className="fill-white text-sm font-bold animate-bounce"
                        style={{ animationDuration: '2s' }}
                    >
                        Z
                    </text>
                )}

                {/* Sound waves for talking */}
                {mood === 'talking' && (
                    <>
                        <path
                            d="M 85 45 Q 92 50 85 55"
                            stroke="white"
                            strokeWidth="2"
                            fill="none"
                            className="animate-ping"
                            style={{ animationDuration: '1s' }}
                        />
                        <path
                            d="M 90 40 Q 100 50 90 60"
                            stroke="white"
                            strokeWidth="2"
                            fill="none"
                            className="animate-ping"
                            style={{ animationDuration: '1.5s', animationDelay: '0.3s' }}
                        />
                    </>
                )}

                {/* Hand for wave */}
                {mood === 'wave' && (
                    <g className="origin-bottom-left animate-bounce" style={{ animationDuration: '0.5s' }}>
                        <circle cx="90" cy="35" r="8" className="fill-primary" />
                        {/* Fingers */}
                        <rect x="85" y="20" width="3" height="10" rx="1.5" className="fill-primary" />
                        <rect x="89" y="18" width="3" height="12" rx="1.5" className="fill-primary" />
                        <rect x="93" y="20" width="3" height="10" rx="1.5" className="fill-primary" />
                    </g>
                )}

                {/* Listening indicators */}
                {mood === 'listening' && (
                    <>
                        <circle
                            cx="50"
                            cy="50"
                            r="48"
                            stroke="white"
                            strokeWidth="2"
                            fill="none"
                            className="animate-ping opacity-30"
                            style={{ animationDuration: '1.5s' }}
                        />
                    </>
                )}
            </svg>
        </div>
    );
}

export default AnimatedCharacter;
