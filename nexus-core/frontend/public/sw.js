/**
 * NEXUS Service Worker
 *
 * Provides offline functionality for the PWA:
 * - Caches static assets for offline access
 * - Queues audio chunks when offline for later sync
 * - Background sync when connection restored
 */

const CACHE_NAME = 'nexus-cache-v1';
const AUDIO_QUEUE_DB = 'nexus-audio-queue';

// Assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/student',
    '/teacher',
    '/manifest.json',
    '/sounds/README.md',
];

// API routes that should NOT be cached
const NO_CACHE_PATTERNS = [
    /\/api\/v1\/sessions/,
    /\/api\/v1\/analytics/,
    /\/api\/v1\/reports/,
    /ws:\/\//,
    /wss:\/\//,
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    // Activate immediately
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log(`[SW] Deleting old cache: ${name}`);
                        return caches.delete(name);
                    })
            );
        })
    );
    // Take control immediately
    self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip WebSocket requests
    if (url.protocol === 'ws:' || url.protocol === 'wss:') {
        return;
    }

    // Skip API requests that shouldn't be cached
    if (NO_CACHE_PATTERNS.some((pattern) => pattern.test(request.url))) {
        return;
    }

    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            // Return cached response if available
            if (cachedResponse) {
                console.log(`[SW] Serving from cache: ${request.url}`);
                return cachedResponse;
            }

            // Otherwise fetch from network
            return fetch(request)
                .then((networkResponse) => {
                    // Cache successful responses
                    if (networkResponse && networkResponse.status === 200) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return networkResponse;
                })
                .catch((error) => {
                    console.warn(`[SW] Fetch failed: ${request.url}`, error);

                    // Return offline page for navigation requests
                    if (request.mode === 'navigate') {
                        return caches.match('/');
                    }

                    throw error;
                });
        })
    );
});

// === Audio Queue for Offline Support ===

/**
 * Open IndexedDB for audio queue
 */
function openAudioQueueDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(AUDIO_QUEUE_DB, 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('chunks')) {
                const store = db.createObjectStore('chunks', {
                    keyPath: 'id',
                    autoIncrement: true,
                });
                store.createIndex('sessionId', 'sessionId', { unique: false });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

/**
 * Queue an audio chunk for later sync
 */
async function queueAudioChunk(sessionId, audioData, timestamp) {
    const db = await openAudioQueueDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['chunks'], 'readwrite');
        const store = transaction.objectStore('chunks');

        const chunk = {
            sessionId,
            audioData,
            timestamp,
            createdAt: Date.now(),
        };

        const request = store.add(chunk);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Get all queued chunks for a session
 */
async function getQueuedChunks(sessionId) {
    const db = await openAudioQueueDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['chunks'], 'readonly');
        const store = transaction.objectStore('chunks');
        const index = store.index('sessionId');

        const request = index.getAll(sessionId);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Delete synced chunks
 */
async function deleteSyncedChunks(ids) {
    const db = await openAudioQueueDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['chunks'], 'readwrite');
        const store = transaction.objectStore('chunks');

        let deleteCount = 0;
        ids.forEach((id) => {
            const request = store.delete(id);
            request.onsuccess = () => {
                deleteCount++;
                if (deleteCount === ids.length) {
                    resolve(deleteCount);
                }
            };
            request.onerror = () => reject(request.error);
        });

        if (ids.length === 0) resolve(0);
    });
}

// === Background Sync ===

/**
 * Handle sync event when back online
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Sync event:', event.tag);

    if (event.tag === 'audio-sync') {
        event.waitUntil(syncAudioChunks());
    }
});

/**
 * Sync queued audio chunks to server
 */
async function syncAudioChunks() {
    console.log('[SW] Syncing queued audio chunks...');

    try {
        const db = await openAudioQueueDB();
        const transaction = db.transaction(['chunks'], 'readonly');
        const store = transaction.objectStore('chunks');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onerror = () => reject(request.error);
            request.onsuccess = async () => {
                const chunks = request.result;
                console.log(`[SW] Found ${chunks.length} queued chunks`);

                if (chunks.length === 0) {
                    resolve();
                    return;
                }

                // Group chunks by session
                const bySession = chunks.reduce((acc, chunk) => {
                    if (!acc[chunk.sessionId]) {
                        acc[chunk.sessionId] = [];
                    }
                    acc[chunk.sessionId].push(chunk);
                    return acc;
                }, {});

                // Sync each session's chunks
                const syncPromises = Object.entries(bySession).map(
                    async ([sessionId, sessionChunks]) => {
                        try {
                            // Sort by timestamp
                            sessionChunks.sort((a, b) => a.timestamp - b.timestamp);

                            // POST to sync endpoint
                            const response = await fetch('/api/v1/sessions/sync', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    session_id: sessionId,
                                    chunks: sessionChunks.map((c) => ({
                                        audio_data: c.audioData,
                                        timestamp: c.timestamp,
                                    })),
                                }),
                            });

                            if (response.ok) {
                                // Delete synced chunks
                                await deleteSyncedChunks(sessionChunks.map((c) => c.id));
                                console.log(`[SW] Synced ${sessionChunks.length} chunks for session ${sessionId}`);
                            }
                        } catch (error) {
                            console.error(`[SW] Failed to sync session ${sessionId}:`, error);
                        }
                    }
                );

                await Promise.all(syncPromises);
                resolve();
            };
        });
    } catch (error) {
        console.error('[SW] Sync failed:', error);
        throw error;
    }
}

// === Message handling ===

/**
 * Handle messages from the main thread
 */
self.addEventListener('message', async (event) => {
    const { type, payload } = event.data;

    switch (type) {
        case 'QUEUE_AUDIO':
            try {
                await queueAudioChunk(
                    payload.sessionId,
                    payload.audioData,
                    payload.timestamp
                );
                event.source.postMessage({ type: 'QUEUE_SUCCESS', payload: { timestamp: payload.timestamp } });
            } catch (error) {
                event.source.postMessage({ type: 'QUEUE_ERROR', payload: { error: error.message } });
            }
            break;

        case 'GET_QUEUED_CHUNKS':
            try {
                const chunks = await getQueuedChunks(payload.sessionId);
                event.source.postMessage({ type: 'QUEUED_CHUNKS', payload: { chunks } });
            } catch (error) {
                event.source.postMessage({ type: 'QUEUE_ERROR', payload: { error: error.message } });
            }
            break;

        case 'TRIGGER_SYNC':
            try {
                await self.registration.sync.register('audio-sync');
                event.source.postMessage({ type: 'SYNC_REGISTERED' });
            } catch (error) {
                // Fallback if background sync not supported
                await syncAudioChunks();
                event.source.postMessage({ type: 'SYNC_COMPLETE' });
            }
            break;

        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        default:
            console.log('[SW] Unknown message type:', type);
    }
});

// === Periodic Sync (if supported) ===

self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'audio-periodic-sync') {
        event.waitUntil(syncAudioChunks());
    }
});

console.log('[SW] Service worker loaded');
