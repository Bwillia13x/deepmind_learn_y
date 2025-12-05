/**
 * useVoiceStream Hook
 *
 * Manages WebSocket connection for real-time voice streaming.
 * Handles audio recording, transmission, and playback.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { getVoiceStreamUrl } from '@/lib/api/client';
import { useSessionStore } from '@/lib/store/useSessionStore';
import type { WSMessage, WSMessageType } from '@/lib/types/api';

// === Types ===

export interface VoiceStreamOptions {
    studentCode: string;
    onSessionReady?: (sessionId: string) => void;
    onSessionEnded?: (data: { duration: number; turnCount: number }) => void;
    onTranscript?: (text: string, isAI: boolean) => void;
    onError?: (error: string) => void;
    onLatencyUpdate?: (latencyMs: number) => void;
}

interface UseVoiceStreamReturn {
    connect: () => void;
    disconnect: () => void;
    startRecording: () => void;
    stopRecording: () => void;
    isConnected: boolean;
    isRecording: boolean;
    error: string | null;
}

// === Constants ===

const AUDIO_SAMPLE_RATE = 24000; // OpenAI Realtime API uses 24kHz
const AUDIO_CHANNELS = 1;
const INITIAL_RECONNECT_DELAY_MS = 1000; // Start with 1 second
const MAX_RECONNECT_DELAY_MS = 30000; // Cap at 30 seconds
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_JITTER_MS = 500; // Random jitter to prevent thundering herd

// === Utility: Calculate exponential backoff with jitter ===

function calculateBackoffDelay(attempt: number): number {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s (capped at MAX_RECONNECT_DELAY_MS)
    const exponentialDelay = Math.min(
        INITIAL_RECONNECT_DELAY_MS * Math.pow(2, attempt),
        MAX_RECONNECT_DELAY_MS
    );
    // Add random jitter to prevent all clients reconnecting at once
    const jitter = Math.random() * RECONNECT_JITTER_MS;
    return exponentialDelay + jitter;
}

// === Utility: Get user-friendly error message ===

function getErrorMessage(closeCode: number, reason: string): string {
    // WebSocket close codes: https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent/code
    switch (closeCode) {
        case 1000:
            return 'Session ended normally';
        case 1001:
            return 'Server is restarting, please wait...';
        case 1002:
            return 'Protocol error - please refresh the page';
        case 1003:
            return 'Invalid data received - please refresh the page';
        case 1006:
            return 'Connection lost unexpectedly - check your internet';
        case 1008:
            return 'Policy violation - please contact support';
        case 1009:
            return 'Message too large - please try again';
        case 1011:
            return 'Server error - please try again later';
        case 1012:
            return 'Server restarting - please wait...';
        case 1013:
            return 'Server too busy - please try again later';
        case 1014:
            return 'Gateway error - please try again';
        case 1015:
            return 'TLS handshake failed - check your connection';
        case 4000:
            return 'Invalid student code';
        case 4001:
            return 'Session expired - please rejoin';
        case 4002:
            return 'Too many connections - please try again';
        case 4003:
            return 'Not authorized - please check your code';
        default:
            return reason || 'Connection error - please try again';
    }
}

// === Utility: Audio Context ===

function createAudioContext(): AudioContext {
    return new (window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext })
            .webkitAudioContext)({
                sampleRate: AUDIO_SAMPLE_RATE,
            });
}

// === Utility: Convert Float32 to Int16 ===

function float32ToInt16(buffer: Float32Array): Int16Array {
    const int16 = new Int16Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
        const s = Math.max(-1, Math.min(1, buffer[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
}

// === Utility: Convert Int16 to Float32 ===

function int16ToFloat32(buffer: Int16Array): Float32Array<ArrayBuffer> {
    const float32 = new Float32Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
        float32[i] = buffer[i] / (buffer[i] < 0 ? 0x8000 : 0x7fff);
    }
    return float32 as Float32Array<ArrayBuffer>;
}

// === Hook ===

export function useVoiceStream(
    options: VoiceStreamOptions
): UseVoiceStreamReturn {
    const {
        studentCode,
        onSessionReady,
        onSessionEnded,
        onTranscript,
        onError,
        onLatencyUpdate,
    } = options;

    // Refs
    const wsRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const audioQueueRef = useRef<Float32Array[]>([]);
    const isPlayingRef = useRef(false);

    // State
    const [isConnected, setIsConnected] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Store actions
    const {
        setConnectionStatus,
        setSessionId,
        setReconnectAttempt,
        recordLatency,
        addTranscriptEntry,
        endSession,
        setError: setStoreError,
    } = useSessionStore();

    // === Audio Playback ===

    const playAudioChunk = useCallback((data: ArrayBuffer) => {
        if (!audioContextRef.current) return;

        const int16Data = new Int16Array(data);
        const float32Data = int16ToFloat32(int16Data);
        audioQueueRef.current.push(float32Data);

        if (!isPlayingRef.current) {
            processAudioQueue();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const processAudioQueue = useCallback(() => {
        if (
            audioQueueRef.current.length === 0 ||
            !audioContextRef.current
        ) {
            isPlayingRef.current = false;
            return;
        }

        isPlayingRef.current = true;
        const audioData = audioQueueRef.current.shift()!;

        const buffer = audioContextRef.current.createBuffer(
            AUDIO_CHANNELS,
            audioData.length,
            AUDIO_SAMPLE_RATE
        );
        // Cast to satisfy strict ArrayBuffer typing
        buffer.copyToChannel(audioData as Float32Array<ArrayBuffer>, 0);

        const source = audioContextRef.current.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContextRef.current.destination);
        source.onended = processAudioQueue;
        source.start();
    }, []);

    // === WebSocket Handlers ===

    const handleWSMessage = useCallback(
        (message: WSMessage) => {
            const { type, data } = message;

            switch (type as WSMessageType) {
                case 'session_ready': {
                    const { session_id } = data as { session_id: string };
                    setSessionId(session_id);
                    onSessionReady?.(session_id);
                    break;
                }

                case 'session_ended': {
                    const { duration_seconds, turn_count } = data as {
                        duration_seconds: number;
                        turn_count: number;
                    };
                    endSession();
                    onSessionEnded?.({ duration: duration_seconds, turnCount: turn_count });
                    break;
                }

                case 'ai_text': {
                    const { text } = data as { text: string };
                    addTranscriptEntry('nexus', text);
                    onTranscript?.(text, true);
                    break;
                }

                case 'transcript': {
                    const { text } = data as { text: string };
                    addTranscriptEntry('student', text);
                    onTranscript?.(text, false);
                    break;
                }

                case 'latency_update': {
                    const { latency_ms } = data as { latency_ms?: number };
                    if (latency_ms !== undefined) {
                        recordLatency(latency_ms);
                        onLatencyUpdate?.(latency_ms);
                    }
                    break;
                }

                case 'error': {
                    const { error: errorMsg } = data as { error: string };
                    setError(errorMsg);
                    onError?.(errorMsg);
                    break;
                }
            }
        },
        [
            onSessionReady,
            onSessionEnded,
            onTranscript,
            onError,
            onLatencyUpdate,
            setSessionId,
            recordLatency,
            addTranscriptEntry,
            endSession,
        ]
    );

    const handleMessage = useCallback(
        async (event: MessageEvent) => {
            if (event.data instanceof Blob) {
                // Binary audio data from AI
                const arrayBuffer = await event.data.arrayBuffer();
                playAudioChunk(arrayBuffer);
                return;
            }

            try {
                const message = JSON.parse(event.data) as WSMessage;
                handleWSMessage(message);
            } catch {
                console.error('Failed to parse WebSocket message');
            }
        },
        [playAudioChunk, handleWSMessage]
    );

    // === Connect ===

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        setConnectionStatus('connecting');
        setError(null);
        setStoreError(null);

        const url = getVoiceStreamUrl(studentCode);
        const ws = new WebSocket(url);
        wsRef.current = ws;

        // Initialize audio context
        if (!audioContextRef.current) {
            audioContextRef.current = createAudioContext();
        }

        ws.onopen = () => {
            setIsConnected(true);
            setConnectionStatus('connected');
            reconnectAttemptsRef.current = 0;
            setReconnectAttempt(0);

            // Send session start message
            ws.send(
                JSON.stringify({
                    type: 'session_start',
                    data: { student_code: studentCode },
                })
            );
        };

        ws.onmessage = handleMessage;

        ws.onerror = () => {
            const errorMsg = 'WebSocket connection error';
            setError(errorMsg);
            setStoreError(errorMsg);
            setConnectionStatus('error');
        };

        ws.onclose = (event) => {
            setIsConnected(false);
            setIsRecording(false);

            const closeCode = event.code;
            const closeReason = event.reason;

            // Determine if we should attempt reconnection
            // Don't reconnect for clean closes (1000) or auth/policy errors (4xxx)
            const shouldReconnect = !event.wasClean &&
                closeCode !== 1000 &&
                closeCode < 4000 &&
                reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS;

            if (shouldReconnect) {
                const attempt = reconnectAttemptsRef.current + 1;
                reconnectAttemptsRef.current = attempt;
                setReconnectAttempt(attempt);
                setConnectionStatus('reconnecting');

                const delay = calculateBackoffDelay(attempt - 1);
                console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${attempt}/${MAX_RECONNECT_ATTEMPTS})`);

                setTimeout(connect, delay);
            } else {
                setConnectionStatus('disconnected');
                setReconnectAttempt(0);

                // Set user-friendly error message if not a clean close
                if (closeCode !== 1000) {
                    const errorMsg = getErrorMessage(closeCode, closeReason);
                    setError(errorMsg);
                    setStoreError(errorMsg, closeCode);
                    onError?.(errorMsg);
                }
            }
        };
    }, [studentCode, handleMessage, setConnectionStatus, setReconnectAttempt, setStoreError, onError]);

    // === Disconnect ===

    const disconnect = useCallback(() => {
        // Stop recording first
        if (isRecording) {
            stopRecording();
        }

        // Reset reconnect counter
        reconnectAttemptsRef.current = 0;
        setReconnectAttempt(0);

        // Send session end message
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'session_end', data: {} }));
            wsRef.current.close(1000, 'User disconnected');
        }

        wsRef.current = null;
        setIsConnected(false);
        setConnectionStatus('disconnected');

        // Clear audio queue
        audioQueueRef.current = [];
        isPlayingRef.current = false;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isRecording, setConnectionStatus, setReconnectAttempt]);

    // === Start Recording ===

    const startRecording = useCallback(async () => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setError('Not connected to voice stream');
            return;
        }

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: AUDIO_SAMPLE_RATE,
                    channelCount: AUDIO_CHANNELS,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            mediaStreamRef.current = stream;

            // Create audio processing pipeline
            const audioContext = audioContextRef.current ?? createAudioContext();
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            sourceRef.current = source;

            // Use ScriptProcessorNode for audio processing
            // Note: This is deprecated but worklet requires more setup
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e: AudioProcessingEvent) => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                    return;
                }

                const inputData = e.inputBuffer.getChannelData(0);
                const int16Data = float32ToInt16(inputData);

                // Send audio chunk as binary
                wsRef.current.send(int16Data.buffer);
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            setIsRecording(true);
            useSessionStore.getState().setMicOn(true);
        } catch (err) {
            const message =
                err instanceof Error ? err.message : 'Failed to access microphone';
            setError(message);
            onError?.(message);
        }
    }, [onError]);

    // === Stop Recording ===

    const stopRecording = useCallback(() => {
        // Disconnect audio nodes
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }

        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }

        // Stop media stream tracks
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track: MediaStreamTrack) => track.stop());
            mediaStreamRef.current = null;
        }

        setIsRecording(false);
        useSessionStore.getState().setMicOn(false);
    }, []);

    // === Cleanup on Unmount ===

    useEffect(() => {
        return () => {
            disconnect();

            if (audioContextRef.current) {
                audioContextRef.current.close();
                audioContextRef.current = null;
            }
        };
    }, [disconnect]);

    return {
        connect,
        disconnect,
        startRecording,
        stopRecording,
        isConnected,
        isRecording,
        error,
    };
}

export default useVoiceStream;
