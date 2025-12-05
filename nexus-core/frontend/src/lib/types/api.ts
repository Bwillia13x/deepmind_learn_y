/**
 * API Types for NEXUS Frontend
 *
 * TypeScript interfaces aligned with backend Pydantic models.
 * Run `scripts/sync_types.sh` to regenerate from backend.
 */

// === Enums ===

export type EngagementLevel = 'low' | 'medium' | 'high';

export type SessionStatus = 'active' | 'completed' | 'interrupted' | 'error';

export type UserRole = 'student' | 'teacher' | 'admin';

// === Student ===

export interface Student {
    id: string;
    student_code: string;
    grade: number;
    primary_language: string;
    school_code?: string | null;
}

export interface StudentCreate {
    student_code: string;
    grade: number;
    primary_language?: string;
    school_code?: string | null;
}

export interface StudentUpdate {
    grade?: number;
    primary_language?: string;
    school_code?: string | null;
}

export interface StudentListResponse {
    students: Student[];
    total: number;
    page: number;
    page_size: number;
}

// === Oracy Session ===

export interface OracySession {
    id: string;
    student_id: string;
    status: SessionStatus;
    duration_seconds?: number | null;
    turn_count: number;
    transcript_summary?: string | null;
    curriculum_outcome_ids?: string | null;
    avg_response_latency_ms?: number | null;
    started_at: string; // ISO datetime
    ended_at?: string | null;
}

export interface OracySessionListResponse {
    sessions: OracySession[];
    total: number;
    page: number;
    page_size: number;
}

// === Scout Report ===

export interface ScoutReport {
    id: string;
    oracy_session_id: string;
    teacher_id?: string | null;
    engagement_level: EngagementLevel;
    insight_text: string;
    linguistic_observations?: string | null;
    curriculum_connections?: string | null;
    recommended_next_steps?: string | null;
    is_reviewed: boolean;
    teacher_notes?: string | null;
    created_at: string;
    reviewed_at?: string | null;
}

export interface ScoutReportWithSession extends ScoutReport {
    session_duration_seconds?: number | null;
    session_turn_count: number;
    student_code?: string | null;
}

export interface ScoutReportUpdate {
    teacher_notes?: string | null;
    is_reviewed?: boolean;
}

export interface ScoutReportListResponse {
    reports: ScoutReportWithSession[];
    total: number;
    page: number;
    page_size: number;
}

export interface CopyableReportResponse {
    insight_text: string;
    linguistic_observations?: string | null;
    curriculum_connections?: string | null;
    recommended_next_steps?: string | null;
    formatted_text: string;
}

export interface TranscriptResponse {
    report_id: string;
    session_id: string;
    student_code?: string | null;
    transcript_summary?: string | null;
    session_duration_seconds?: number | null;
    session_turn_count: number;
    started_at: string;
    ended_at?: string | null;
}

// === Curriculum ===

export interface CurriculumOutcome {
    id: string;
    outcome_code: string;
    subject: string;
    grade: number;
    strand?: string | null;
    outcome_text: string;
    keywords?: string | null;
    cultural_bridge_hints?: string | null;
}

export interface CurriculumSearchResponse {
    outcomes: CurriculumOutcome[];
    total: number;
}

// === WebSocket Messages ===

export type WSMessageType =
    | 'audio_chunk'
    | 'session_start'
    | 'session_end'
    | 'user_message'
    | 'ai_audio'
    | 'ai_text'
    | 'transcript'
    | 'session_ready'
    | 'session_ended'
    | 'error'
    | 'latency_update';

export interface WSMessage<T = unknown> {
    type: WSMessageType;
    data: T;
}

export interface SessionReadyData {
    session_id: string;
    student_code: string;
}

export interface SessionEndedData {
    session_id: string;
    duration_seconds: number;
    turn_count: number;
}

export interface AITextData {
    text: string;
}

export interface LatencyUpdateData {
    latency_ms?: number;
    bytes_received?: number;
}

export interface ErrorData {
    error: string;
}

// === API Error ===

export interface APIError {
    detail: string;
    status_code?: number;
}

// === Health Check ===

export interface HealthResponse {
    status: string;
    app: string;
    version: string;
}

// === Analytics ===

export interface EngagementTrendPoint {
    date: string;
    high_engagement_count: number;
    medium_engagement_count: number;
    low_engagement_count: number;
    total_sessions: number;
    avg_duration_minutes: number;
}

export interface EngagementTrendResponse {
    period_start: string;
    period_end: string;
    trend_data: EngagementTrendPoint[];
    overall_high_percentage: number;
    overall_medium_percentage: number;
    overall_low_percentage: number;
}

export interface StrugglingStudentAlert {
    student_code: string;
    grade: number;
    primary_language: string;
    consecutive_low_engagement_days: number;
    last_session_date: string | null;
    avg_session_duration_minutes: number;
    recommended_action: string;
}

export interface StrugglingStudentsResponse {
    alerts: StrugglingStudentAlert[];
    total_struggling: number;
    threshold_days: number;
}

export interface CurriculumCoverageItem {
    outcome_id: string;
    outcome_code: string;
    outcome_description: string;
    subject: string;
    grade: number;
    session_count: number;
    unique_students: number;
    avg_engagement_score: number;
}

export interface CurriculumCoverageResponse {
    outcomes: CurriculumCoverageItem[];
    total_outcomes_covered: number;
    total_outcomes_available: number;
    coverage_percentage: number;
    most_practiced_subject: string | null;
    least_practiced_subject: string | null;
}

export interface ClassOverviewStats {
    total_students: number;
    active_students_this_week: number;
    total_sessions_this_week: number;
    avg_session_duration_minutes: number;
    total_practice_minutes_this_week: number;
    high_engagement_rate: number;
    reports_pending_review: number;
}

export interface AnalyticsSummaryResponse {
    overview: ClassOverviewStats;
    engagement_trend: EngagementTrendResponse;
    struggling_students: StrugglingStudentsResponse;
    curriculum_coverage: CurriculumCoverageResponse;
}
