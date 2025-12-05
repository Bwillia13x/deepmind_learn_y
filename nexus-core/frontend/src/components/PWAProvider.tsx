/**
 * PWA Provider Component
 *
 * Client-side component that wraps the app with PWA functionality.
 * Handles service worker registration and provides offline indicator.
 */

'use client';

import * as React from 'react';
import { OfflineIndicator } from '@/components/ui';

export function PWAProvider({ children }: { children: React.ReactNode }): React.ReactElement {
    return (
        <>
            {children}
            <OfflineIndicator />
        </>
    );
}
