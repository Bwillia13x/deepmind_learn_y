/**
 * NEXUS Session Store - Zustand State Management
 *
 * Centralized state for voice session management.
 * This is the "single source of truth" for all voice-related UI state.
 *
 * Per .context/01_domain_glossary.md, we use domain-specific terminology:
 * - oracy_session (not "session" or "call")
 * - student_code (not "user_id")
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// === Types ===

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface LatencyMetric {
    timestamp: number;
    value: number; // milliseconds
}

export interface TranscriptEntry {
    id: string;
    role: 'student' | 'nexus';
    content: string;
    timestamp: number;
}

export interface ScoutInsight {
    engagementLevel: 'low' | 'medium' | 'high';
    insightText: string;
    linguisticObservations?: string;
    curriculumConnections?: string;
    recommendedNextSteps?: string;
}

export interface SessionState {
    // Connection state
    connectionStatus: ConnectionStatus;
    sessionId: string | null;
    studentCode: string | null;
    reconnectAttempt: number; // Current reconnection attempt (0 = not reconnecting)
    maxReconnectAttempts: number; // Max allowed attempts

    // Voice state
    isMicOn: boolean;
    isAISpeaking: boolean;
    isListening: boolean;

    // Session data
    transcript: TranscriptEntry[];
    latencyMetrics: LatencyMetric[];
    turnCount: number;
    sessionStartTime: number | null;

    // Scout Report (generated after session)
    currentScoutInsight: ScoutInsight | null;

    // Error state
    error: string | null;
    lastErrorCode: number | null; // WebSocket close code for diagnostics
}

export interface SessionActions {
    // Connection actions
    setConnectionStatus: (status: ConnectionStatus) => void;
    startSession: (studentCode: string) => void;
    endSession: () => void;
    setSessionId: (id: string) => void;
    setReconnectAttempt: (attempt: number) => void;

    // Voice actions
    toggleMic: () => void;
    setMicOn: (on: boolean) => void;
    setAISpeaking: (speaking: boolean) => void;
    setListening: (listening: boolean) => void;

    // Transcript actions
    addTranscriptEntry: (role: 'student' | 'nexus', content: string) => void;
    clearTranscript: () => void;

    // Metrics actions
    recordLatency: (latencyMs: number) => void;
    incrementTurnCount: () => void;

    // Scout Report actions
    setScoutInsight: (insight: ScoutInsight | null) => void;

    // Error actions
    setError: (error: string | null, closeCode?: number) => void;

    // Reset
    reset: () => void;
}

// === Initial State ===

const initialState: SessionState = {
    connectionStatus: 'disconnected',
    sessionId: null,
    studentCode: null,
    reconnectAttempt: 0,
    maxReconnectAttempts: 5,
    isMicOn: false,
    isAISpeaking: false,
    isListening: false,
    transcript: [],
    latencyMetrics: [],
    turnCount: 0,
    sessionStartTime: null,
    currentScoutInsight: null,
    error: null,
    lastErrorCode: null,
};

// === Store ===

type SessionStore = SessionState & SessionActions;

export const useSessionStore = create<SessionStore>()(
    devtools(
        persist(
            (set: (partial: Partial<SessionStore> | ((state: SessionStore) => Partial<SessionStore>)) => void, get: () => SessionStore) => ({
                ...initialState,

                // Connection actions
                setConnectionStatus: (status: ConnectionStatus) => set({ connectionStatus: status }),

                startSession: (studentCode: string) =>
                    set({
                        studentCode,
                        connectionStatus: 'connecting',
                        sessionStartTime: Date.now(),
                        transcript: [],
                        latencyMetrics: [],
                        turnCount: 0,
                        error: null,
                    }),

                endSession: () =>
                    set({
                        connectionStatus: 'disconnected',
                        isMicOn: false,
                        isAISpeaking: false,
                        isListening: false,
                    }),

                setSessionId: (id: string) => set({ sessionId: id }),

                setReconnectAttempt: (attempt: number) => set({ reconnectAttempt: attempt }),

                // Voice actions
                toggleMic: () => set((state: SessionStore) => ({ isMicOn: !state.isMicOn })),

                setMicOn: (on: boolean) => set({ isMicOn: on }),

                setAISpeaking: (speaking: boolean) => set({ isAISpeaking: speaking }),

                setListening: (listening: boolean) => set({ isListening: listening }),

                // Transcript actions
                addTranscriptEntry: (role: 'student' | 'nexus', content: string) =>
                    set((state: SessionStore) => ({
                        transcript: [
                            ...state.transcript,
                            {
                                id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
                                role,
                                content,
                                timestamp: Date.now(),
                            },
                        ],
                    })),

                clearTranscript: () => set({ transcript: [] }),

                // Metrics actions
                recordLatency: (latencyMs: number) =>
                    set((state: SessionStore) => ({
                        latencyMetrics: [
                            ...state.latencyMetrics.slice(-99), // Keep last 100 metrics
                            { timestamp: Date.now(), value: latencyMs },
                        ],
                    })),

                incrementTurnCount: () =>
                    set((state: SessionStore) => ({ turnCount: state.turnCount + 1 })),

                // Scout Report actions
                setScoutInsight: (insight: ScoutInsight | null) => set({ currentScoutInsight: insight }),

                // Error actions
                setError: (error: string | null, closeCode?: number) =>
                    set({
                        error,
                        lastErrorCode: closeCode ?? null,
                        connectionStatus: error ? 'error' : get().connectionStatus,
                    }),

                // Reset
                reset: () => set(initialState),
            }),
            {
                name: 'nexus-session-storage',
                partialize: (state: SessionStore) => ({
                    // Only persist non-sensitive, non-transient data
                    studentCode: state.studentCode,
                }),
            }
        ),
        { name: 'NexusSession' }
    )
);

// === Selectors ===

export const selectIsActive = (state: SessionState): boolean =>
    state.connectionStatus === 'connected';

export const selectAverageLatency = (state: SessionState): number => {
    if (state.latencyMetrics.length === 0) return 0;
    const sum = state.latencyMetrics.reduce((acc, m) => acc + m.value, 0);
    return Math.round(sum / state.latencyMetrics.length);
};

export const selectSessionDuration = (state: SessionState): number => {
    if (!state.sessionStartTime) return 0;
    return Math.floor((Date.now() - state.sessionStartTime) / 1000);
};
