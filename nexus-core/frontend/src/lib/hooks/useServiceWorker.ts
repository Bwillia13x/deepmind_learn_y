/**
 * Service Worker Management Hook
 *
 * Handles service worker registration, updates, and offline status.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface ServiceWorkerState {
    isSupported: boolean;
    isRegistered: boolean;
    isOnline: boolean;
    updateAvailable: boolean;
    registration: ServiceWorkerRegistration | null;
}

export interface UseServiceWorkerReturn extends ServiceWorkerState {
    // Actions
    register: () => Promise<void>;
    unregister: () => Promise<void>;
    update: () => Promise<void>;
    skipWaiting: () => void;
    // Offline audio queue
    queueAudioChunk: (sessionId: string, audioData: string, timestamp: number) => Promise<void>;
    triggerSync: () => Promise<void>;
}

export function useServiceWorker(): UseServiceWorkerReturn {
    const [state, setState] = useState<ServiceWorkerState>({
        isSupported: false,
        isRegistered: false,
        isOnline: true,
        updateAvailable: false,
        registration: null,
    });

    const registrationRef = useRef<ServiceWorkerRegistration | null>(null);

    // Check support on mount
    useEffect(() => {
        setState((prev) => ({
            ...prev,
            isSupported: 'serviceWorker' in navigator,
            isOnline: navigator.onLine,
        }));
    }, []);

    // Handle online/offline events
    useEffect(() => {
        const handleOnline = () => {
            console.log('[useServiceWorker] Online');
            setState((prev) => ({ ...prev, isOnline: true }));

            // Trigger sync when back online
            if (registrationRef.current && 'sync' in registrationRef.current) {
                (registrationRef.current as unknown as { sync: { register: (tag: string) => Promise<void> } })
                    .sync.register('audio-sync')
                    .catch(console.error);
            }
        };

        const handleOffline = () => {
            console.log('[useServiceWorker] Offline');
            setState((prev) => ({ ...prev, isOnline: false }));
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // Register service worker
    const register = useCallback(async () => {
        if (!('serviceWorker' in navigator)) {
            console.warn('[useServiceWorker] Service workers not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/',
            });

            console.log('[useServiceWorker] Registered:', registration.scope);

            registrationRef.current = registration;
            setState((prev) => ({
                ...prev,
                isRegistered: true,
                registration,
            }));

            // Check for updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (newWorker) {
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            console.log('[useServiceWorker] Update available');
                            setState((prev) => ({ ...prev, updateAvailable: true }));
                        }
                    });
                }
            });
        } catch (error) {
            console.error('[useServiceWorker] Registration failed:', error);
        }
    }, []);

    // Unregister service worker
    const unregister = useCallback(async () => {
        if (registrationRef.current) {
            try {
                await registrationRef.current.unregister();
                registrationRef.current = null;
                setState((prev) => ({
                    ...prev,
                    isRegistered: false,
                    registration: null,
                    updateAvailable: false,
                }));
                console.log('[useServiceWorker] Unregistered');
            } catch (error) {
                console.error('[useServiceWorker] Unregister failed:', error);
            }
        }
    }, []);

    // Check for updates
    const update = useCallback(async () => {
        if (registrationRef.current) {
            try {
                await registrationRef.current.update();
                console.log('[useServiceWorker] Update check complete');
            } catch (error) {
                console.error('[useServiceWorker] Update check failed:', error);
            }
        }
    }, []);

    // Skip waiting (activate new service worker)
    const skipWaiting = useCallback(() => {
        if (registrationRef.current?.waiting) {
            registrationRef.current.waiting.postMessage({ type: 'SKIP_WAITING' });

            // Reload to use new service worker
            window.location.reload();
        }
    }, []);

    // Queue audio chunk for offline sync
    const queueAudioChunk = useCallback(
        async (sessionId: string, audioData: string, timestamp: number) => {
            const controller = navigator.serviceWorker.controller;
            if (!controller) {
                throw new Error('Service worker not active');
            }

            return new Promise<void>((resolve, reject) => {
                const channel = new MessageChannel();

                channel.port1.onmessage = (event) => {
                    if (event.data.type === 'QUEUE_SUCCESS') {
                        resolve();
                    } else if (event.data.type === 'QUEUE_ERROR') {
                        reject(new Error(event.data.payload.error));
                    }
                };

                controller.postMessage(
                    {
                        type: 'QUEUE_AUDIO',
                        payload: { sessionId, audioData, timestamp },
                    },
                    [channel.port2]
                );
            });
        },
        []
    );

    // Trigger background sync
    const triggerSync = useCallback(async () => {
        const controller = navigator.serviceWorker.controller;
        if (!controller) {
            throw new Error('Service worker not active');
        }

        return new Promise<void>((resolve, reject) => {
            const channel = new MessageChannel();
            const timeout = setTimeout(() => reject(new Error('Sync timeout')), 30000);

            channel.port1.onmessage = (event) => {
                clearTimeout(timeout);
                if (event.data.type === 'SYNC_REGISTERED' || event.data.type === 'SYNC_COMPLETE') {
                    resolve();
                } else {
                    reject(new Error('Sync failed'));
                }
            };

            controller.postMessage(
                { type: 'TRIGGER_SYNC' },
                [channel.port2]
            );
        });
    }, []);

    // Auto-register on mount
    useEffect(() => {
        if (state.isSupported && !state.isRegistered) {
            register();
        }
    }, [state.isSupported, state.isRegistered, register]);

    return {
        ...state,
        register,
        unregister,
        update,
        skipWaiting,
        queueAudioChunk,
        triggerSync,
    };
}
