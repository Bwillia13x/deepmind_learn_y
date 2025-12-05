'use client';

/**
 * TranscriptPanel Component
 *
 * Displays the conversation transcript between student and AI.
 * Auto-scrolls to latest message with visual distinction between speakers.
 */

import * as React from 'react';
import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { useSessionStore, type SessionState, type TranscriptEntry } from '@/lib/store/useSessionStore';

// === Types ===

export interface TranscriptPanelProps {
    className?: string;
    maxHeight?: string;
    showTimestamps?: boolean;
}

// === Component ===

export function TranscriptPanel({
    className,
    maxHeight = '400px',
    showTimestamps = false,
}: TranscriptPanelProps): React.ReactElement {
    const scrollRef = useRef<HTMLDivElement>(null);
    const transcript = useSessionStore((state: SessionState) => state.transcript);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [transcript]);

    if (transcript.length === 0) {
        return (
            <div
                className={cn(
                    'flex items-center justify-center p-8 text-muted-foreground',
                    className
                )}
            >
                <p className="text-sm italic">
                    Start speaking to begin the conversation...
                </p>
            </div>
        );
    }

    return (
        <div
            ref={scrollRef}
            className={cn(
                'overflow-y-auto p-4 space-y-4 scroll-smooth',
                className
            )}
            style={{ maxHeight }}
            role="log"
            aria-live="polite"
            aria-label="Conversation transcript"
        >
            {transcript.map((entry: TranscriptEntry) => (
                <TranscriptMessage
                    key={entry.id}
                    entry={entry}
                    showTimestamp={showTimestamps}
                />
            ))}
        </div>
    );
}

// === Message Component ===

interface TranscriptMessageProps {
    entry: TranscriptEntry;
    showTimestamp: boolean;
}

function TranscriptMessage({
    entry,
    showTimestamp,
}: TranscriptMessageProps): React.ReactElement {
    const isUser = entry.role === 'student';

    return (
        <div
            className={cn(
                'flex flex-col gap-1',
                isUser ? 'items-end' : 'items-start'
            )}
        >
            {/* Speaker label */}
            <span
                className={cn(
                    'text-xs font-medium',
                    isUser ? 'text-primary' : 'text-secondary'
                )}
            >
                {isUser ? 'You' : 'NEXUS'}
            </span>

            {/* Message bubble */}
            <div
                className={cn(
                    'max-w-[80%] rounded-2xl px-4 py-2 text-sm shadow-sm',
                    isUser
                        ? 'bg-nexus-primary text-white rounded-br-sm'
                        : 'bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-border/50 text-foreground rounded-bl-sm'
                )}
            >
                {entry.content}
            </div>

            {/* Timestamp */}
            {showTimestamp && (
                <span className="text-xs text-muted-foreground">
                    {formatTimestamp(entry.timestamp)}
                </span>
            )}
        </div>
    );
}

// === Utilities ===

function formatTimestamp(timestamp: number): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

export default TranscriptPanel;
