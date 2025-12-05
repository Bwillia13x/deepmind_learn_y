/**
 * Test Setup for Vitest
 *
 * Configures testing environment for React components.
 */

/// <reference types="@testing-library/jest-dom" />
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Cleanup after each test
afterEach(() => {
    cleanup();
});

// Mock Next.js router
vi.mock("next/navigation", () => ({
    useRouter: () => ({
        push: vi.fn(),
        replace: vi.fn(),
        back: vi.fn(),
        forward: vi.fn(),
        refresh: vi.fn(),
        prefetch: vi.fn(),
    }),
    usePathname: () => "/",
    useSearchParams: () => new URLSearchParams(),
}));

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Mock AudioContext for voice components
const mockAudioContext = {
    createAnalyser: vi.fn(() => ({
        connect: vi.fn(),
        disconnect: vi.fn(),
        fftSize: 2048,
        frequencyBinCount: 1024,
        getByteFrequencyData: vi.fn(),
    })),
    createMediaStreamSource: vi.fn(() => ({
        connect: vi.fn(),
        disconnect: vi.fn(),
    })),
    close: vi.fn(),
    state: "running",
};

global.AudioContext = vi.fn().mockImplementation(() => mockAudioContext);

// Mock navigator.mediaDevices for microphone access
Object.defineProperty(navigator, "mediaDevices", {
    value: {
        getUserMedia: vi.fn().mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        }),
        enumerateDevices: vi.fn().mockResolvedValue([]),
    },
    writable: true,
});

// Mock Service Worker
Object.defineProperty(navigator, "serviceWorker", {
    value: {
        register: vi.fn().mockResolvedValue({
            installing: null,
            waiting: null,
            active: { postMessage: vi.fn() },
        }),
        ready: Promise.resolve({
            active: { postMessage: vi.fn() },
            sync: { register: vi.fn() },
        }),
        controller: { postMessage: vi.fn() },
    },
    writable: true,
});
