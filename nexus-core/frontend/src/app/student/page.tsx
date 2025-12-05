'use client';

/**
 * Student Practice Page
 *
 * Voice-based oracy practice interface designed specifically for young learners
 * and EAL (English as an Additional Language) students.
 *
 * Design Principles:
 * - Visual-first: Icons and animations over text
 * - Large touch targets for all interactive elements
 * - Immediate visual and audio feedback
 * - Friendly, encouraging interface with animated character
 * - Minimal text, clear visual states
 */

import * as React from 'react';
import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { VoiceOrb, TranscriptPanel, ConnectionStatus } from '@/components/voice';
import { useVoiceStream } from '@/lib/hooks';
import { useSessionStore, type ConnectionStatus as ConnectionStatusType, type SessionState, type SessionActions } from '@/lib/store/useSessionStore';
import {
    VisualButton,
    AnimatedCharacter,
    ProgressIndicator,
    VisualFeedback,
    LoadingSpinner,
    useAudioFeedback,
    type CharacterMood,
    type FeedbackType,
} from '@/components/ui';

export default function StudentPracticePage(): React.ReactElement {
    const router = useRouter();
    const [studentCode, setStudentCode] = useState('');
    const [isJoined, setIsJoined] = useState(false);
    const [showFeedback, setShowFeedback] = useState(false);
    const [feedbackType, setFeedbackType] = useState<FeedbackType>('success');
    const [characterMood, setCharacterMood] = useState<CharacterMood>('wave');
    const [sessionProgress, setSessionProgress] = useState(0);

    // Audio feedback hook for child-friendly sounds
    const { play: playSound } = useAudioFeedback(true, 0.5);

    const {
        connect,
        disconnect,
        startRecording,
        stopRecording,
        isConnected,
        isRecording,
        error,
    } = useVoiceStream({
        studentCode,
        onSessionReady: (sessionId) => {
            console.log('Session started:', sessionId);
        },
        onSessionEnded: ({ duration, turnCount }) => {
            console.log(`Session ended: ${duration}s, ${turnCount} turns`);
            handleEndSession();
        },
        onError: (err) => {
            console.error('Voice stream error:', err);
        },
    });

    const connectionStatus = useSessionStore((state: SessionState): ConnectionStatusType => state.connectionStatus);
    const reset = useSessionStore((state: SessionState & SessionActions) => state.reset);
    const transcript = useSessionStore((state: SessionState) => state.transcript);

    // Update character mood based on connection/recording state
    useEffect(() => {
        if (!isConnected && connectionStatus === 'connecting') {
            setCharacterMood('thinking');
        } else if (isConnected && isRecording) {
            setCharacterMood('listening');
        } else if (isConnected) {
            setCharacterMood('happy');
        } else {
            setCharacterMood('wave');
        }
    }, [isConnected, isRecording, connectionStatus]);

    // Update progress based on conversation turns
    useEffect(() => {
        const turns = transcript.length;
        // Progress increases with conversation turns (max 10 turns for 100%)
        const progress = Math.min(100, turns * 10);
        setSessionProgress(progress);

        // Play celebration when reaching milestones
        if (progress > 0 && progress % 30 === 0) {
            playSound('success');
            setFeedbackType('celebration');
            setShowFeedback(true);
        }
    }, [transcript.length, playSound]);

    const handleJoin = useCallback(() => {
        if (!studentCode.trim()) return;

        // Validate student code format (alphanumeric, 4-20 chars)
        const codeRegex = /^[A-Za-z0-9]{4,20}$/;
        if (!codeRegex.test(studentCode.trim())) {
            playSound('error');
            setFeedbackType('error');
            setShowFeedback(true);
            return;
        }

        playSound('start');
        setIsJoined(true);
        connect();
    }, [studentCode, connect, playSound]);

    const handleEndSession = useCallback(() => {
        playSound('complete');
        disconnect();
        reset();
        setIsJoined(false);
        setStudentCode('');
        setSessionProgress(0);
    }, [disconnect, reset, playSound]);

    const handleOrbClick = useCallback(() => {
        playSound('click');
        if (!isConnected) {
            setCharacterMood('thinking');
            connect();
        } else if (isRecording) {
            setCharacterMood('happy');
            stopRecording();
        } else {
            setCharacterMood('listening');
            startRecording();
        }
    }, [isConnected, isRecording, connect, startRecording, stopRecording, playSound]);

    // Entry screen - student code input
    if (!isJoined) {
        return (
            <main className="min-h-screen bg-background app-grid-pattern flex items-center justify-center p-4 relative overflow-hidden">
                {/* Background Blobs */}
                <div className="absolute top-0 left-0 w-96 h-96 bg-nexus-primary/10 rounded-full blur-3xl -z-10 opacity-50" />
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-nexus-secondary/10 rounded-full blur-3xl -z-10 opacity-50" />

                <div className="w-full max-w-md relative z-10 animate-slide-up">
                    <div className="glass-card rounded-2xl p-8 md:p-10">
                        {/* Header */}
                        <div className="text-center mb-8">
                            <div className="inline-block p-3 rounded-full bg-nexus-primary/10 mb-4 animate-float">
                                <span className="text-4xl">👋</span>
                            </div>
                            <h1 className="text-3xl font-bold text-gradient-primary mb-2">
                                Welcome to NEXUS
                            </h1>
                            <p className="text-muted-foreground">
                                Enter your student code to start speaking
                            </p>
                        </div>

                        {/* Student Code Input */}
                        <div className="space-y-6">
                            <div>
                                <label
                                    htmlFor="studentCode"
                                    className="block text-sm font-medium text-foreground mb-2 ml-1"
                                >
                                    Student Code
                                </label>
                                <div className="relative">
                                    <input
                                        id="studentCode"
                                        type="text"
                                        value={studentCode}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setStudentCode(e.target.value.toUpperCase())}
                                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleJoin()}
                                        placeholder="e.g. AB12"
                                        className="w-full px-6 py-4 text-lg tracking-widest text-center rounded-xl border border-input bg-background/50 backdrop-blur-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-nexus-primary focus:border-transparent transition-all shadow-sm"
                                        autoComplete="off"
                                        autoFocus
                                    />
                                    <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                                        {studentCode.length >= 4 && (
                                            <span className="text-nexus-success animate-fade-in">✓</span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={handleJoin}
                                disabled={!studentCode.trim()}
                                className="w-full px-6 py-4 rounded-xl bg-nexus-primary text-white font-bold text-lg shadow-lg shadow-nexus-primary/25 hover:bg-nexus-primary/90 hover:shadow-xl hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-nexus-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none transition-all"
                            >
                                Start Practice
                            </button>
                        </div>

                        {/* Back Link */}
                        <div className="mt-8 text-center">
                            <button
                                onClick={() => router.push('/')}
                                className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-2 mx-auto group"
                            >
                                <span className="group-hover:-translate-x-1 transition-transform">←</span> Back to home
                            </button>
                        </div>
                    </div>

                    {/* Privacy Notice */}
                    <p className="text-xs text-muted-foreground text-center mt-6 opacity-70">
                        🔒 Your voice is processed securely. No video is captured.
                    </p>
                </div>
            </main>
        );
    }

    // Practice screen - voice interface (child-friendly design)
    return (
        <main className="min-h-screen bg-background app-grid-pattern flex flex-col relative overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-nexus-primary/5 -z-10" />

            {/* Compact Header - minimal text */}
            <header className="flex items-center justify-between p-4 border-b border-border/50 bg-background/50 backdrop-blur-md sticky top-0 z-50">
                <div className="flex items-center gap-3">
                    {/* Simple icon badge for student */}
                    <div className="flex items-center gap-2 px-4 py-2 bg-nexus-primary/10 border border-nexus-primary/20 rounded-full">
                        <span className="text-xl">👤</span>
                        <span className="text-sm font-bold text-nexus-primary tracking-wide">{studentCode}</span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <ConnectionStatus />
                    {/* Exit button with icon */}
                    <VisualButton
                        variant="ghost"
                        size="sm"
                        icon={
                            <svg className="w-6 h-6 text-muted-foreground hover:text-destructive transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                        }
                        onClick={handleEndSession}
                        ariaLabel="End session and go home"
                        className="hover:bg-destructive/10 rounded-full p-2"
                    />
                </div>
            </header>

            {/* Main Content - Visual First Design */}
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
                {/* Voice Interface - Center Stage */}
                <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-8 relative">
                    {/* Visual Feedback Overlay */}
                    <div className="absolute top-8 right-8 z-20">
                        <VisualFeedback
                            type={feedbackType}
                            visible={showFeedback}
                            size="md"
                            onHide={() => setShowFeedback(false)}
                        />
                    </div>

                    {/* Animated Character - Shows state visually */}
                    <div className="mb-10 animate-float">
                        <AnimatedCharacter
                            mood={characterMood}
                            size="lg"
                            className="drop-shadow-2xl"
                        />
                    </div>

                    {/* Progress Indicator - Visual stars/steps */}
                    <div className="w-full max-w-xs mb-10">
                        <ProgressIndicator
                            value={sessionProgress}
                            variant="steps"
                            steps={5}
                            size="lg"
                            color="success"
                            celebrateOnComplete
                            ariaLabel="Conversation progress"
                        />
                    </div>

                    {/* Voice Orb - Main interaction point */}
                    <div className="relative group">
                        {connectionStatus === 'connecting' && (
                            <div className="absolute inset-0 flex items-center justify-center z-10">
                                <LoadingSpinner variant="orbit" size="xl" color="primary" />
                            </div>
                        )}

                        {/* Glow effect behind orb */}
                        <div className={cn(
                            "absolute inset-0 bg-nexus-primary/30 rounded-full blur-3xl transition-all duration-500",
                            isRecording ? "scale-150 opacity-100" : "scale-100 opacity-0 group-hover:opacity-50"
                        )} />

                        <div className="relative z-0">
                            <VoiceOrb
                                size="lg"
                                onClick={handleOrbClick}
                                disabled={connectionStatus === 'connecting'}
                            />
                        </div>
                    </div>

                    {/* Simple visual hints - icons instead of text */}
                    <div className="mt-12 h-12 flex items-center justify-center">
                        {!isConnected && connectionStatus !== 'connecting' && (
                            <div className="flex items-center gap-3 text-muted-foreground animate-pulse bg-card/50 px-4 py-2 rounded-full border border-border/50">
                                <span className="text-2xl">👆</span>
                                <span className="text-sm font-medium">Tap to start</span>
                            </div>
                        )}
                        {isConnected && !isRecording && (
                            <div className="flex items-center gap-3 text-nexus-primary animate-bounce bg-nexus-primary/10 px-4 py-2 rounded-full border border-nexus-primary/20">
                                <span className="text-2xl">🎤</span>
                                <span className="text-sm font-medium">Tap to speak</span>
                            </div>
                        )}
                        {isRecording && (
                            <div className="flex items-center gap-3 text-nexus-success bg-nexus-success/10 px-4 py-2 rounded-full border border-nexus-success/20">
                                <span className="text-2xl animate-pulse">👂</span>
                                <span className="text-sm font-medium">Listening...</span>
                            </div>
                        )}
                    </div>

                    {/* Error indicator - visual with friendly message */}
                    {error && (
                        <div className="mt-6 flex flex-col items-center gap-2 text-destructive animate-shake">
                            <div className="flex items-center gap-2 px-4 py-2 bg-destructive/10 rounded-lg border border-destructive/20">
                                <span className="text-xl">⚠️</span>
                                <span className="text-sm font-medium">
                                    {error}
                                </span>
                            </div>
                            {connectionStatus === 'error' && (
                                <button
                                    onClick={handleOrbClick}
                                    className="mt-2 px-6 py-2 text-sm font-medium bg-nexus-primary text-white rounded-full hover:bg-nexus-primary/90 transition-colors shadow-md"
                                >
                                    Try Again
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Transcript Panel - Simplified for children */}
                <div className="lg:w-96 border-t lg:border-t-0 lg:border-l border-border bg-card/30 backdrop-blur-sm flex flex-col h-[40vh] lg:h-auto">
                    {/* Visual header with speech bubble icon */}
                    <div className="p-4 border-b border-border/50 flex items-center gap-3 bg-card/50">
                        <div className="p-2 bg-nexus-secondary/10 rounded-lg">
                            <span className="text-xl">💬</span>
                        </div>
                        <span className="font-medium text-foreground">Conversation</span>
                    </div>
                    <div className="flex-1 overflow-hidden relative">
                        <TranscriptPanel
                            className="scrollbar-thin h-full"
                            maxHeight="100%"
                            showTimestamps={false}
                        />
                    </div>
                </div>
            </div>
        </main>
    );
}
