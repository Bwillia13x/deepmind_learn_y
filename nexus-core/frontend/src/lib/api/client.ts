/**
 * API Client for NEXUS Backend
 *
 * Provides typed HTTP methods with automatic auth token handling.
 * Uses the native fetch API for Next.js compatibility.
 */

import type {
    Student,
    StudentCreate,
    StudentUpdate,
    StudentListResponse,
    OracySessionListResponse,
    ScoutReport,
    ScoutReportUpdate,
    ScoutReportListResponse,
    CopyableReportResponse,
    TranscriptResponse,
    CurriculumSearchResponse,
    HealthResponse,
    APIError,
    ClassOverviewStats,
    EngagementTrendResponse,
    StrugglingStudentsResponse,
    CurriculumCoverageResponse,
    AnalyticsSummaryResponse,
} from '@/lib/types/api';

// === Configuration ===

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// === Types ===

interface RequestOptions {
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
    headers?: Record<string, string>;
    body?: unknown;
    signal?: AbortSignal;
}

type QueryParams = Record<string, string | number | boolean | undefined>;

// === Token Management ===

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
    authToken = token;
    if (token) {
        // Also persist in localStorage for session recovery
        if (typeof window !== 'undefined') {
            localStorage.setItem('nexus_auth_token', token);
        }
    } else {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('nexus_auth_token');
        }
    }
}

export function getAuthToken(): string | null {
    if (authToken) return authToken;

    // Try to recover from localStorage
    if (typeof window !== 'undefined') {
        authToken = localStorage.getItem('nexus_auth_token');
    }
    return authToken;
}

// === Error Handling ===

export class ApiError extends Error {
    constructor(
        public statusCode: number,
        public detail: string
    ) {
        super(detail);
        this.name = 'ApiError';
    }
}

// === Base Request ===

async function request<T>(
    endpoint: string,
    options: RequestOptions
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getAuthToken();

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const fetchOptions: globalThis.RequestInit = {
        method: options.method,
        headers,
        signal: options.signal,
    };

    if (options.body) {
        fetchOptions.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, fetchOptions);

    // Handle no content responses
    if (response.status === 204) {
        return undefined as T;
    }

    const data = await response.json();

    if (!response.ok) {
        const error = data as APIError;
        throw new ApiError(response.status, error.detail || 'An error occurred');
    }

    return data as T;
}

function buildQueryString(params: QueryParams): string {
    const entries = Object.entries(params).filter(
        ([, value]) => value !== undefined
    );

    if (entries.length === 0) return '';

    const searchParams = new URLSearchParams();
    for (const [key, value] of entries) {
        searchParams.append(key, String(value));
    }

    return `?${searchParams.toString()}`;
}

// === Health Check ===

export async function getHealth(): Promise<HealthResponse> {
    // Health endpoint is outside v1
    const response = await fetch(
        `${API_BASE_URL.replace('/api/v1', '')}/health`
    );
    return response.json();
}

// === Students API ===

export const studentsApi = {
    list: async (params?: {
        page?: number;
        page_size?: number;
        search?: string;
        grade?: number;
    }): Promise<StudentListResponse> => {
        const query = buildQueryString(params ?? {});
        return request<StudentListResponse>(`/students${query}`, { method: 'GET' });
    },

    get: async (id: string): Promise<Student> => {
        return request<Student>(`/students/${id}`, { method: 'GET' });
    },

    getByCode: async (code: string): Promise<Student> => {
        return request<Student>(`/students/code/${code}`, { method: 'GET' });
    },

    create: async (data: StudentCreate): Promise<Student> => {
        return request<Student>('/students', { method: 'POST', body: data });
    },

    update: async (id: string, data: StudentUpdate): Promise<Student> => {
        return request<Student>(`/students/${id}`, { method: 'PATCH', body: data });
    },

    delete: async (id: string): Promise<void> => {
        return request<void>(`/students/${id}`, { method: 'DELETE' });
    },
};

// === Sessions API ===

export const sessionsApi = {
    list: async (params?: {
        page?: number;
        page_size?: number;
        student_id?: string;
        status?: string;
    }): Promise<OracySessionListResponse> => {
        const query = buildQueryString(params ?? {});
        return request<OracySessionListResponse>(`/sessions${query}`, {
            method: 'GET',
        });
    },

    listForStudent: async (
        studentId: string,
        params?: { page?: number; page_size?: number }
    ): Promise<OracySessionListResponse> => {
        const query = buildQueryString(params ?? {});
        return request<OracySessionListResponse>(
            `/sessions/student/${studentId}${query}`,
            { method: 'GET' }
        );
    },

    get: async (id: string): Promise<OracySessionListResponse> => {
        // Returns session with related data
        return request<OracySessionListResponse>(`/sessions/${id}`, {
            method: 'GET',
        });
    },
};

// === Reports API ===

export const reportsApi = {
    list: async (params?: {
        page?: number;
        page_size?: number;
        is_reviewed?: boolean;
        teacher_id?: string;
    }): Promise<ScoutReportListResponse> => {
        const query = buildQueryString(params ?? {});
        return request<ScoutReportListResponse>(`/reports${query}`, {
            method: 'GET',
        });
    },

    get: async (id: string): Promise<ScoutReport> => {
        return request<ScoutReport>(`/reports/${id}`, { method: 'GET' });
    },

    getForSession: async (sessionId: string): Promise<ScoutReport> => {
        return request<ScoutReport>(`/reports/session/${sessionId}`, {
            method: 'GET',
        });
    },

    update: async (id: string, data: ScoutReportUpdate): Promise<ScoutReport> => {
        return request<ScoutReport>(`/reports/${id}`, {
            method: 'PATCH',
            body: data,
        });
    },

    getCopyable: async (id: string): Promise<CopyableReportResponse> => {
        return request<CopyableReportResponse>(`/reports/${id}/copy`, {
            method: 'GET',
        });
    },

    getTranscript: async (id: string): Promise<TranscriptResponse> => {
        return request<TranscriptResponse>(`/reports/${id}/transcript`, {
            method: 'GET',
        });
    },
};

// === Curriculum API ===

export const curriculumApi = {
    search: async (params: {
        query: string;
        grade?: number;
        subject?: string;
        limit?: number;
    }): Promise<CurriculumSearchResponse> => {
        const query = buildQueryString(params);
        return request<CurriculumSearchResponse>(`/curriculum/search${query}`, {
            method: 'GET',
        });
    },
};

// === Analytics API ===

export const analyticsApi = {
    getOverview: async (params?: {
        school_code?: string;
        days?: number;
    }): Promise<ClassOverviewStats> => {
        const query = buildQueryString(params ?? {});
        return request<ClassOverviewStats>(`/analytics/overview${query}`, {
            method: 'GET',
        });
    },

    getEngagementTrend: async (params?: {
        school_code?: string;
        days?: number;
    }): Promise<EngagementTrendResponse> => {
        const query = buildQueryString(params ?? {});
        return request<EngagementTrendResponse>(`/analytics/engagement-trend${query}`, {
            method: 'GET',
        });
    },

    getStrugglingStudents: async (params?: {
        school_code?: string;
        threshold_days?: number;
    }): Promise<StrugglingStudentsResponse> => {
        const query = buildQueryString(params ?? {});
        return request<StrugglingStudentsResponse>(`/analytics/struggling-students${query}`, {
            method: 'GET',
        });
    },

    getCurriculumCoverage: async (params?: {
        school_code?: string;
        grade?: number;
        subject?: string;
        days?: number;
    }): Promise<CurriculumCoverageResponse> => {
        const query = buildQueryString(params ?? {});
        return request<CurriculumCoverageResponse>(`/analytics/curriculum-coverage${query}`, {
            method: 'GET',
        });
    },

    getSummary: async (params?: {
        school_code?: string;
    }): Promise<AnalyticsSummaryResponse> => {
        const query = buildQueryString(params ?? {});
        return request<AnalyticsSummaryResponse>(`/analytics/summary${query}`, {
            method: 'GET',
        });
    },
};

// === WebSocket URL Builder ===

export function getVoiceStreamUrl(studentCode: string, token?: string): string {
    const wsBase = API_BASE_URL.replace(/^http/, 'ws').replace('/api/v1', '');
    const authToken = token ?? getAuthToken();

    let url = `${wsBase}/api/v1/ws/oracy/${studentCode}`;
    if (authToken) {
        url += `?token=${authToken}`;
    }

    return url;
}

// === Default Export ===

const api = {
    setAuthToken,
    getAuthToken,
    getHealth,
    students: studentsApi,
    sessions: sessionsApi,
    reports: reportsApi,
    curriculum: curriculumApi,
    analytics: analyticsApi,
    getVoiceStreamUrl,
};

export default api;
