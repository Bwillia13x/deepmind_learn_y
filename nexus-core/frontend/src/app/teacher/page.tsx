'use client';

/**
 * Teacher Dashboard Page
 *
 * View and manage Scout Reports from student oracy sessions.
 * Key Feature: "Copy for IPP" - One-click copy of formatted report for compliance docs.
 */

import * as React from 'react';
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { reportsApi, studentsApi } from '@/lib/api/client';
import type { ScoutReportWithSession, Student } from '@/lib/types/api';
import { cn } from '@/lib/utils';

// Copy success feedback duration
const COPY_FEEDBACK_MS = 2000;

export default function TeacherDashboardPage(): React.ReactElement {
    const router = useRouter();
    const [reports, setReports] = useState<ScoutReportWithSession[]>([]);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [_students, setStudents] = useState<Student[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<'all' | 'unreviewed' | 'reviewed'>('all');
    const [selectedReport, setSelectedReport] = useState<ScoutReportWithSession | null>(null);
    const [selectedStudentCode, setSelectedStudentCode] = useState<string | null>(null);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    // Get unique student codes from reports
    const studentCodes = useMemo(() => {
        const codes = new Set(reports.map(r => r.student_code).filter(Boolean));
        return Array.from(codes).sort() as string[];
    }, [reports]);

    // Fetch reports
    const fetchReports = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const params: { is_reviewed?: boolean } = {};
            if (filter === 'unreviewed') params.is_reviewed = false;
            if (filter === 'reviewed') params.is_reviewed = true;

            const [reportsResponse, studentsResponse] = await Promise.all([
                reportsApi.list(params),
                studentsApi.list({ page_size: 100 }),
            ]);

            setReports(reportsResponse.reports);
            setStudents(studentsResponse.students);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load reports');
        } finally {
            setIsLoading(false);
        }
    }, [filter]);

    useEffect(() => {
        fetchReports();
    }, [fetchReports]);

    // Mark report as reviewed
    const handleMarkReviewed = useCallback(async (reportId: string) => {
        try {
            await reportsApi.update(reportId, { is_reviewed: true });
            fetchReports();
            if (selectedReport?.id === reportId) {
                setSelectedReport(null);
            }
        } catch (err) {
            console.error('Failed to mark report as reviewed:', err);
        }
    }, [fetchReports, selectedReport]);

    // Copy report to clipboard
    const handleCopyReport = useCallback(async (reportId: string) => {
        try {
            const copyable = await reportsApi.getCopyable(reportId);
            await navigator.clipboard.writeText(copyable.formatted_text);
            setCopiedId(reportId);
            setTimeout(() => setCopiedId(null), COPY_FEEDBACK_MS);
        } catch (err) {
            console.error('Failed to copy report:', err);
        }
    }, []);

    // Filter reports by student
    const filteredReports = useMemo(() => {
        if (!selectedStudentCode) return reports;
        return reports.filter(r => r.student_code === selectedStudentCode);
    }, [reports, selectedStudentCode]);

    return (
        <main className="min-h-screen bg-background app-grid-pattern">
            {/* Header */}
            <header className="border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-50">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-nexus-secondary/10 flex items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-nexus-secondary">
                                <path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82ZM12 3 1 9l11 6 9-4.91V17h2V9L12 3Z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gradient-primary">NEXUS</h1>
                            <p className="text-xs text-muted-foreground font-medium">Teacher Dashboard</p>
                        </div>
                    </div>
                    <button
                        onClick={() => router.push('/')}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-muted/50"
                    >
                        <span>←</span> Back to home
                    </button>
                </div>
            </header>

            <div className="container mx-auto px-4 py-8">
                {/* Filter Tabs */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div className="flex gap-2 p-1 bg-muted/50 rounded-xl">
                        {(['all', 'unreviewed', 'reviewed'] as const).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setFilter(tab)}
                                className={cn(
                                    'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                                    filter === tab
                                        ? 'bg-background text-foreground shadow-sm'
                                        : 'text-muted-foreground hover:text-foreground hover:bg-background/50'
                                )}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>

                    {/* Student Filter */}
                    {studentCodes.length > 0 && (
                        <div className="flex items-center gap-3 bg-card border border-border rounded-xl px-4 py-2 shadow-sm">
                            <span className="text-sm text-muted-foreground font-medium">Filter by Student:</span>
                            <select
                                value={selectedStudentCode ?? ''}
                                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedStudentCode(e.target.value || null)}
                                className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
                            >
                                <option value="">All Students</option>
                                {studentCodes.map((code) => (
                                    <option key={code} value={code}>{code}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {/* Content */}
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="animate-spin w-10 h-10 border-4 border-nexus-primary border-t-transparent rounded-full mb-4" />
                        <p className="text-muted-foreground animate-pulse">Loading reports...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-20 bg-destructive/5 rounded-2xl border border-destructive/10">
                        <p className="text-destructive font-medium mb-4">{error}</p>
                        <button
                            onClick={fetchReports}
                            className="px-6 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
                        >
                            Retry
                        </button>
                    </div>
                ) : reports.length === 0 ? (
                    <div className="text-center py-20 bg-card border border-border border-dashed rounded-2xl">
                        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <p className="text-lg font-medium text-foreground">No reports found</p>
                        <p className="text-muted-foreground">Wait for students to complete practice sessions.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                        {/* Reports List */}
                        <div className="lg:col-span-4 space-y-4 h-[calc(100vh-200px)] overflow-y-auto pr-2 scrollbar-thin">
                            <div className="flex items-center justify-between mb-2 sticky top-0 bg-background z-10 py-2">
                                <h2 className="font-semibold text-foreground">
                                    Scout Reports <span className="ml-2 text-xs bg-muted px-2 py-1 rounded-full text-muted-foreground">{filteredReports.length}</span>
                                </h2>
                            </div>
                            <div className="space-y-3">
                                {filteredReports.map((report: ScoutReportWithSession) => (
                                    <ReportCard
                                        key={report.id}
                                        report={report}
                                        isSelected={selectedReport?.id === report.id}
                                        onClick={() => setSelectedReport(report)}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Report Detail */}
                        <div className="lg:col-span-8 h-[calc(100vh-200px)] overflow-y-auto scrollbar-thin">
                            {selectedReport ? (
                                <ReportDetail
                                    report={selectedReport}
                                    onMarkReviewed={handleMarkReviewed}
                                    onCopy={handleCopyReport}
                                    isCopied={copiedId === selectedReport.id}
                                />
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center bg-card/50 border border-border border-dashed rounded-2xl p-8 text-center">
                                    <div className="w-20 h-20 bg-nexus-primary/5 rounded-full flex items-center justify-center mb-6 animate-pulse-soft">
                                        <svg className="w-10 h-10 text-nexus-primary/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                        </svg>
                                    </div>
                                    <h3 className="text-xl font-semibold text-foreground mb-2">Select a Report</h3>
                                    <p className="text-muted-foreground max-w-sm">
                                        Choose a student report from the list to view detailed insights and generate IPP content.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}

// === Report Card Component ===

interface ReportCardProps {
    report: ScoutReportWithSession;
    isSelected: boolean;
    onClick: () => void;
}

function ReportCard({ report, isSelected, onClick }: ReportCardProps): React.ReactElement {
    const engagementColors = {
        low: 'bg-nexus-warning/10 text-nexus-warning border-nexus-warning/20',
        medium: 'bg-nexus-primary/10 text-nexus-primary border-nexus-primary/20',
        high: 'bg-nexus-success/10 text-nexus-success border-nexus-success/20',
    };

    return (
        <button
            onClick={onClick}
            className={cn(
                'w-full text-left p-4 rounded-xl border transition-all duration-200 group relative overflow-hidden',
                isSelected
                    ? 'bg-card border-nexus-primary shadow-md ring-1 ring-nexus-primary/50'
                    : 'bg-card/50 border-border hover:border-nexus-primary/50 hover:shadow-sm hover:bg-card'
            )}
        >
            {isSelected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-nexus-primary" />}

            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground">
                        {report.student_code?.substring(0, 2) ?? '??'}
                    </div>
                    <span className="text-sm font-semibold text-foreground">
                        {report.student_code ?? 'Unknown Student'}
                    </span>
                </div>
                <span
                    className={cn(
                        'px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border',
                        engagementColors[report.engagement_level]
                    )}
                >
                    {report.engagement_level}
                </span>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2 mb-3 leading-relaxed group-hover:text-foreground/80 transition-colors">
                {report.insight_text}
            </p>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDate(report.created_at)}
                    </span>
                </div>
                {!report.is_reviewed && (
                    <span className="flex h-2 w-2 rounded-full bg-nexus-warning animate-pulse" title="New Report" />
                )}
            </div>
        </button>
    );
}

// === Report Detail Component ===

interface ReportDetailProps {
    report: ScoutReportWithSession;
    onMarkReviewed: (id: string) => void;
    onCopy: (id: string) => void;
    isCopied: boolean;
}

function ReportDetail({
    report,
    onMarkReviewed,
    onCopy,
    isCopied,
}: ReportDetailProps): React.ReactElement {
    const [showTranscript, setShowTranscript] = useState(false);
    const [transcriptData, setTranscriptData] = useState<import('@/lib/types/api').TranscriptResponse | null>(null);
    const [transcriptLoading, setTranscriptLoading] = useState(false);
    const [transcriptError, setTranscriptError] = useState<string | null>(null);

    // Fetch transcript when opening
    const handleShowTranscript = useCallback(async () => {
        if (showTranscript) {
            setShowTranscript(false);
            return;
        }

        setTranscriptLoading(true);
        setTranscriptError(null);

        try {
            const data = await reportsApi.getTranscript(report.id);
            setTranscriptData(data);
            setShowTranscript(true);
        } catch (err) {
            setTranscriptError(err instanceof Error ? err.message : 'Failed to load transcript');
        } finally {
            setTranscriptLoading(false);
        }
    }, [showTranscript, report.id]);

    return (
        <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden animate-fade-in">
            {/* Header */}
            <div className="p-6 border-b border-border bg-muted/10">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-foreground mb-1">
                            Scout Report
                        </h2>
                        <p className="text-sm text-muted-foreground">
                            Generated insights for IPP documentation
                        </p>
                    </div>
                    <div className="flex gap-3">
                        {/* Review Transcript Button */}
                        <button
                            onClick={handleShowTranscript}
                            disabled={transcriptLoading}
                            className={cn(
                                'px-4 py-2 text-sm font-medium rounded-lg transition-all border',
                                showTranscript
                                    ? 'bg-nexus-secondary/10 text-nexus-secondary border-nexus-secondary/20'
                                    : 'bg-background text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                            )}
                        >
                            {transcriptLoading ? (
                                <span className="flex items-center gap-2">
                                    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Loading...
                                </span>
                            ) : (
                                <span className="flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    {showTranscript ? 'Hide Transcript' : 'Review Transcript'}
                                </span>
                            )}
                        </button>

                        {/* COPY FOR IPP - The killer feature! */}
                        <button
                            onClick={() => onCopy(report.id)}
                            className={cn(
                                'px-5 py-2 text-sm font-bold rounded-lg transition-all shadow-sm flex items-center gap-2',
                                isCopied
                                    ? 'bg-nexus-success text-white scale-105'
                                    : 'bg-nexus-primary text-white hover:bg-nexus-primary/90 hover:shadow-md hover:-translate-y-0.5'
                            )}
                        >
                            {isCopied ? (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                    </svg>
                                    Copy for IPP
                                </>
                            )}
                        </button>

                        {!report.is_reviewed && (
                            <button
                                onClick={() => onMarkReviewed(report.id)}
                                className="px-3 py-2 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors"
                                title="Mark as reviewed"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-6 p-4 bg-background rounded-xl border border-border/50">
                    <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">Student</span>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-nexus-primary/10 flex items-center justify-center text-[10px] font-bold text-nexus-primary">
                                {report.student_code?.substring(0, 1) ?? '?'}
                            </div>
                            <p className="font-semibold text-foreground">{report.student_code ?? 'Unknown'}</p>
                        </div>
                    </div>
                    <div className="flex flex-col border-l border-border/50 pl-6">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">Duration</span>
                        <p className="font-semibold text-foreground">
                            {report.session_duration_seconds
                                ? formatDuration(report.session_duration_seconds)
                                : 'N/A'}
                        </p>
                    </div>
                    <div className="flex flex-col border-l border-border/50 pl-6">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">Turns</span>
                        <p className="font-semibold text-foreground">{report.session_turn_count}</p>
                    </div>
                </div>
            </div>

            {/* Transcript Panel (collapsible) */}
            {showTranscript && (
                <div className="animate-accordion-down">
                    <TranscriptPanel
                        transcriptData={transcriptData}
                        error={transcriptError}
                    />
                </div>
            )}

            {/* Content */}
            <div className="p-8 space-y-8">
                {/* Insight */}
                <Section title="Key Insights" icon="💡">
                    <p className="text-foreground/90 leading-relaxed text-lg">{report.insight_text}</p>
                </Section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Linguistic Observations */}
                    {report.linguistic_observations && (
                        <Section title="Linguistic Observations" icon="🗣️">
                            <p className="text-foreground/80 leading-relaxed">{report.linguistic_observations}</p>
                        </Section>
                    )}

                    {/* Curriculum Connections */}
                    {report.curriculum_connections && (
                        <Section title="Curriculum Connections" icon="📚">
                            <p className="text-foreground/80 leading-relaxed">{report.curriculum_connections}</p>
                        </Section>
                    )}
                </div>

                {/* Recommended Next Steps */}
                {report.recommended_next_steps && (
                    <Section title="Recommended Next Steps" icon="🎯" className="bg-nexus-primary/5 border border-nexus-primary/10 rounded-xl p-6">
                        <p className="text-foreground/80 leading-relaxed">{report.recommended_next_steps}</p>
                    </Section>
                )}
            </div>
        </div>
    );
}

// === Section Component ===

function Section({
    title,
    icon,
    children,
    className,
}: {
    title: string;
    icon?: string;
    children: React.ReactNode;
    className?: string;
}): React.ReactElement {
    return (
        <div className={className}>
            <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                {icon && <span className="text-lg">{icon}</span>}
                {title}
            </h3>
            {children}
        </div>
    );
}

// === Utilities ===

function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// === Transcript Panel Component ===

interface TranscriptPanelProps {
    transcriptData: import('@/lib/types/api').TranscriptResponse | null;
    error: string | null;
}

function TranscriptPanel({ transcriptData, error }: TranscriptPanelProps): React.ReactElement {
    if (error) {
        return (
            <div className="p-4 border-b border-border bg-destructive/10">
                <p className="text-sm text-destructive">{error}</p>
            </div>
        );
    }

    if (!transcriptData) {
        return (
            <div className="p-4 border-b border-border bg-muted/50">
                <p className="text-sm text-muted-foreground">Loading transcript...</p>
            </div>
        );
    }

    return (
        <div className="border-b border-border bg-muted/30">
            {/* Transcript Header */}
            <div className="p-4 border-b border-border/50">
                <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h3 className="font-medium text-foreground">Session Transcript</h3>
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                        PII-Scrubbed
                    </span>
                </div>
                <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>
                        Started: {formatDate(transcriptData.started_at)}
                    </span>
                    {transcriptData.ended_at && (
                        <span>
                            Ended: {formatDate(transcriptData.ended_at)}
                        </span>
                    )}
                    <span>
                        {transcriptData.session_turn_count} conversation turns
                    </span>
                </div>
            </div>

            {/* Transcript Content */}
            <div className="p-4 max-h-64 overflow-y-auto">
                {transcriptData.transcript_summary ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        <p className="text-foreground/80 whitespace-pre-wrap leading-relaxed">
                            {transcriptData.transcript_summary}
                        </p>
                    </div>
                ) : (
                    <div className="text-center py-6">
                        <svg className="w-10 h-10 mx-auto text-muted-foreground/50 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-sm text-muted-foreground">
                            No transcript summary available for this session.
                        </p>
                        <p className="text-xs text-muted-foreground/70 mt-1">
                            Note: Audio is never stored per FOIP compliance.
                        </p>
                    </div>
                )}
            </div>

            {/* Privacy Notice */}
            <div className="px-4 py-2 bg-info/10 text-xs text-info flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                    This transcript has been summarized and scrubbed of any personally identifiable information (PII) per FOIP requirements.
                </span>
            </div>
        </div>
    );
}
