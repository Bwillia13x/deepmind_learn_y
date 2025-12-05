'use client';

/**
 * AudioPlayer Component
 *
 * Manages audio feedback for children's interactions.
 * Provides success sounds, error sounds, and celebration effects.
 */

import * as React from 'react';

export type SoundType = 'success' | 'error' | 'click' | 'complete' | 'start' | 'celebration';

export interface AudioPlayerProps {
    /** Whether audio is enabled */
    enabled?: boolean;
    /** Volume level (0-1) */
    volume?: number;
}

// Sound URLs (using Web Audio API to generate sounds programmatically)
// This avoids needing external audio files

interface AudioContextState {
    context: AudioContext | null;
    initialized: boolean;
}

const audioState: AudioContextState = {
    context: null,
    initialized: false,
};

function getAudioContext(): AudioContext | null {
    if (typeof window === 'undefined') {
        return null;
    }

    if (!audioState.initialized) {
        audioState.initialized = true;
        try {
            audioState.context = new (window.AudioContext || (window as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
        } catch {
            console.warn('Web Audio API not supported');
            return null;
        }
    }

    return audioState.context;
}

function playTone(
    frequency: number,
    duration: number,
    type: OscillatorType = 'sine',
    volume: number = 0.3
): void {
    const ctx = getAudioContext();
    if (!ctx) return;

    // Resume context if suspended (browser autoplay policy)
    if (ctx.state === 'suspended') {
        ctx.resume();
    }

    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);

    // Envelope for smoother sound
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration);
}

function playMelody(
    notes: Array<{ freq: number; duration: number }>,
    volume: number = 0.3
): void {
    const ctx = getAudioContext();
    if (!ctx) return;

    let currentTime = ctx.currentTime;

    for (const note of notes) {
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(note.freq, currentTime);

        gainNode.gain.setValueAtTime(0, currentTime);
        gainNode.gain.linearRampToValueAtTime(volume, currentTime + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.001, currentTime + note.duration);

        oscillator.start(currentTime);
        oscillator.stop(currentTime + note.duration);

        currentTime += note.duration;
    }
}

const soundEffects: Record<SoundType, (volume: number) => void> = {
    success: (vol) => {
        // Happy ascending tone
        playMelody([
            { freq: 523.25, duration: 0.1 }, // C5
            { freq: 659.25, duration: 0.1 }, // E5
            { freq: 783.99, duration: 0.15 }, // G5
        ], vol);
    },
    error: (vol) => {
        // Low descending tone
        playMelody([
            { freq: 311.13, duration: 0.15 }, // D#4
            { freq: 261.63, duration: 0.2 }, // C4
        ], vol);
    },
    click: (vol) => {
        // Short click
        playTone(800, 0.05, 'sine', vol);
    },
    complete: (vol) => {
        // Victory fanfare
        playMelody([
            { freq: 523.25, duration: 0.1 }, // C5
            { freq: 587.33, duration: 0.1 }, // D5
            { freq: 659.25, duration: 0.1 }, // E5
            { freq: 783.99, duration: 0.1 }, // G5
            { freq: 1046.5, duration: 0.3 }, // C6
        ], vol);
    },
    start: (vol) => {
        // Ready tone
        playMelody([
            { freq: 440, duration: 0.1 }, // A4
            { freq: 554.37, duration: 0.15 }, // C#5
        ], vol);
    },
    celebration: (vol) => {
        // Celebration flourish
        playMelody([
            { freq: 523.25, duration: 0.08 }, // C5
            { freq: 659.25, duration: 0.08 }, // E5
            { freq: 783.99, duration: 0.08 }, // G5
            { freq: 1046.5, duration: 0.08 }, // C6
            { freq: 783.99, duration: 0.08 }, // G5
            { freq: 1046.5, duration: 0.08 }, // C6
            { freq: 1318.51, duration: 0.2 }, // E6
        ], vol);
    },
};

export interface AudioPlayerHandle {
    play: (sound: SoundType) => void;
    setVolume: (volume: number) => void;
    setEnabled: (enabled: boolean) => void;
}

export const AudioPlayer = React.forwardRef<AudioPlayerHandle, AudioPlayerProps>(
    function AudioPlayer({ enabled = true, volume = 0.5 }, ref) {
        const [isEnabled, setIsEnabled] = React.useState(enabled);
        const [currentVolume, setCurrentVolume] = React.useState(volume);

        React.useImperativeHandle(ref, () => ({
            play: (sound: SoundType) => {
                if (isEnabled) {
                    soundEffects[sound](currentVolume);
                }
            },
            setVolume: (vol: number) => {
                setCurrentVolume(Math.max(0, Math.min(1, vol)));
            },
            setEnabled: (val: boolean) => {
                setIsEnabled(val);
            },
        }), [isEnabled, currentVolume]);

        // This component is headless - no UI
        return null;
    }
);

// Hook for easy audio playback
export function useAudioFeedback(enabled: boolean = true, volume: number = 0.5): {
    play: (sound: SoundType) => void;
    setVolume: (volume: number) => void;
    setEnabled: (enabled: boolean) => void;
} {
    const [isEnabled, setIsEnabled] = React.useState(enabled);
    const [currentVolume, setCurrentVolume] = React.useState(volume);

    const play = React.useCallback((sound: SoundType) => {
        if (isEnabled) {
            soundEffects[sound](currentVolume);
        }
    }, [isEnabled, currentVolume]);

    const setVolume = React.useCallback((vol: number) => {
        setCurrentVolume(Math.max(0, Math.min(1, vol)));
    }, []);

    const setEnabled = React.useCallback((val: boolean) => {
        setIsEnabled(val);
    }, []);

    return { play, setVolume, setEnabled };
}

export default AudioPlayer;
