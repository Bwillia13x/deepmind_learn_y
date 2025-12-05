'use client';

/**
 * Teacher Analytics Dashboard
 *
 * Provides cohort-level insights for teachers:
 * - Class-wide engagement trends (line chart)
 * - Struggling students alerts
 * - Curriculum coverage heatmap
 */

import * as React from 'react';
import { useEffect, useCallback } from 'react';
import { analyticsApi } from '@/lib/api/client';
import { useTeacherStore } from '@/lib/store/useTeacherStore';
import type {
    EngagementTrendPoint,
    StrugglingStudentAlert,
    CurriculumCoverageItem,
} from '@/lib/types/api';
import { cn } from '@/lib/utils';

// Icons (using simple SVG for now)
const TrendingUpIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
);

const AlertTriangleIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
);

const BookOpenIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
);

const UsersIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
);

const ClockIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

// === Components ===

interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    trend?: 'up' | 'down' | 'neutral';
    className?: string;
}

function StatCard({ title, value, subtitle, icon, trend, className }: StatCardProps) {
    return (
        <div className={cn(
            "glass-card p-4",
            className
        )}>
            <div className="flex items-center justify-between">
                <div className="text-muted-foreground">{icon}</div>
                {trend && (
                    <span className={cn(
                        "text-xs px-2 py-1 rounded-full",
                        trend === 'up' && "bg-nexus-success/10 text-nexus-success",
                        trend === 'down' && "bg-nexus-error/10 text-nexus-error",
                        trend === 'neutral' && "bg-muted text-muted-foreground"
                    )}>
                        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
                    </span>
                )}
            </div>
            <div className="mt-3">
                <div className="text-2xl font-bold text-foreground">{value}</div>
                <div className="text-sm text-muted-foreground">{title}</div>
                {subtitle && (
                    <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>
                )}
            </div>
        </div>
    );
}

interface EngagementChartProps {
    data: EngagementTrendPoint[];
}

function EngagementChart({ data }: EngagementChartProps) {
    if (data.length === 0) {
        return (
            <div className="h-48 flex items-center justify-center text-muted-foreground">
                No engagement data available
            </div>
        );
    }

    const maxSessions = Math.max(...data.map(d => d.total_sessions), 1);

    return (
        <div className="space-y-4">
            {/* Legend */}
            <div className="flex gap-4 text-xs">
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-nexus-success" />
                    <span>High</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-nexus-warning" />
                    <span>Medium</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-nexus-error" />
                    <span>Low</span>
                </div>
            </div>

            {/* Chart */}
            <div className="h-48 flex items-end gap-1">
                {data.map((point: EngagementTrendPoint) => {
                    const height = (point.total_sessions / maxSessions) * 100;
                    const highPct = point.total_sessions > 0
                        ? (point.high_engagement_count / point.total_sessions) * 100
                        : 0;
                    const medPct = point.total_sessions > 0
                        ? (point.medium_engagement_count / point.total_sessions) * 100
                        : 0;
                    const lowPct = 100 - highPct - medPct;

                    return (
                        <div
                            key={point.date}
                            className="flex-1 flex flex-col justify-end group relative"
                        >
                            <div
                                className="w-full flex flex-col rounded-t overflow-hidden"
                                style={{ height: `${height}%`, minHeight: point.total_sessions > 0 ? '8px' : '0' }}
                            >
                                <div
                                    className="bg-nexus-success"
                                    style={{ height: `${highPct}%` }}
                                />
                                <div
                                    className="bg-nexus-warning"
                                    style={{ height: `${medPct}%` }}
                                />
                                <div
                                    className="bg-nexus-error"
                                    style={{ height: `${lowPct}%` }}
                                />
                            </div>

                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                                <div className="bg-popover border border-border rounded-lg p-2 shadow-lg text-xs whitespace-nowrap">
                                    <div className="font-medium">{point.date}</div>
                                    <div>Total: {point.total_sessions} sessions</div>
                                    <div className="text-nexus-success">High: {point.high_engagement_count}</div>
                                    <div className="text-nexus-warning">Med: {point.medium_engagement_count}</div>
                                    <div className="text-nexus-error">Low: {point.low_engagement_count}</div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* X-axis labels */}
            <div className="flex justify-between text-xs text-muted-foreground">
                <span>{data[0]?.date}</span>
                <span>{data[data.length - 1]?.date}</span>
            </div>
        </div>
    );
}

interface StrugglingStudentCardProps {
    alert: StrugglingStudentAlert;
}

function StrugglingStudentCard({ alert }: StrugglingStudentCardProps) {
    const severityColor = alert.consecutive_low_engagement_days >= 5
        ? 'border-nexus-error bg-nexus-error/5'
        : alert.consecutive_low_engagement_days >= 4
            ? 'border-orange-500 bg-orange-50'
            : 'border-nexus-warning bg-nexus-warning/5';

    return (
        <div className={cn(
            "rounded-lg border-l-4 p-4",
            severityColor
        )}>
            <div className="flex justify-between items-start">
                <div>
                    <div className="font-medium text-foreground">
                        {alert.student_code}
                    </div>
                    <div className="text-sm text-muted-foreground">
                        Grade {alert.grade} • {alert.primary_language}
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-sm font-medium text-nexus-error">
                        {alert.consecutive_low_engagement_days} days low
                    </div>
                    <div className="text-xs text-muted-foreground">
                        {alert.avg_session_duration_minutes.toFixed(1)} min avg
                    </div>
                </div>
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
                <span className="font-medium">Recommended:</span> {alert.recommended_action}
            </div>
        </div>
    );
}

interface CurriculumHeatmapProps {
    items: CurriculumCoverageItem[];
}

function CurriculumHeatmap({ items }: CurriculumHeatmapProps) {
    if (items.length === 0) {
        return (
            <div className="h-48 flex items-center justify-center text-muted-foreground">
                No curriculum data available
            </div>
        );
    }

    // Group by subject
    const bySubject: Record<string, CurriculumCoverageItem[]> = {};
    for (const item of items) {
        if (!bySubject[item.subject]) {
            bySubject[item.subject] = [];
        }
        bySubject[item.subject].push(item);
    }

    const getHeatColor = (sessionCount: number, maxCount: number) => {
        if (sessionCount === 0) return 'bg-muted';
        const intensity = sessionCount / maxCount;
        if (intensity > 0.7) return 'bg-nexus-success';
        if (intensity > 0.4) return 'bg-nexus-success/70';
        if (intensity > 0.2) return 'bg-nexus-success/40';
        return 'bg-nexus-success/20';
    };

    const maxSessions = Math.max(...items.map(i => i.session_count), 1);

    return (
        <div className="space-y-4">
            {Object.entries(bySubject).slice(0, 4).map(([subject, outcomes]: [string, CurriculumCoverageItem[]]) => (
                <div key={subject}>
                    <div className="text-sm font-medium text-foreground mb-2">{subject}</div>
                    <div className="flex flex-wrap gap-1">
                        {outcomes.slice(0, 10).map((outcome: CurriculumCoverageItem) => (
                            <div
                                key={outcome.outcome_id}
                                className={cn(
                                    "w-8 h-8 rounded flex items-center justify-center text-xs cursor-default group relative",
                                    getHeatColor(outcome.session_count, maxSessions),
                                    outcome.session_count === 0 && "text-gray-400"
                                )}
                            >
                                {outcome.session_count || '-'}

                                {/* Tooltip */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                                    <div className="bg-popover border border-border rounded-lg p-2 shadow-lg text-xs whitespace-nowrap max-w-xs">
                                        <div className="font-medium">{outcome.outcome_code}</div>
                                        <div className="text-muted-foreground truncate">{outcome.outcome_description.slice(0, 60)}...</div>
                                        <div className="mt-1">
                                            Sessions: {outcome.session_count} • Students: {outcome.unique_students}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {outcomes.length > 10 && (
                            <div className="w-8 h-8 rounded bg-gray-50 flex items-center justify-center text-xs text-muted-foreground">
                                +{outcomes.length - 10}
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

// === Main Page ===

export default function AnalyticsDashboardPage(): React.ReactElement {
    const {
        overviewStats: overview,
        engagementTrends: engagement,
        strugglingStudents: struggling,
        curriculumCoverage: curriculum,
        isLoading,
        error,
        dateRange,
        setData,
        setLoading,
        setError,
        setDateRange
    } = useTeacherStore();

    // Calculate days from dateRange for API calls
    const timePeriod = Math.ceil((dateRange.end.getTime() - dateRange.start.getTime()) / (1000 * 60 * 60 * 24));

    const fetchAnalytics = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const [overviewData, engagementData, strugglingData, curriculumData] = await Promise.all([
                analyticsApi.getOverview({ days: 7 }), // Overview is always weekly
                analyticsApi.getEngagementTrend({ days: timePeriod }),
                analyticsApi.getStrugglingStudents({ threshold_days: 3 }),
                analyticsApi.getCurriculumCoverage({ days: timePeriod }),
            ]);

            setData({
                overviewStats: overviewData,
                engagementTrends: engagementData,
                strugglingStudents: strugglingData,
                curriculumCoverage: curriculumData,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load analytics');
        } finally {
            setLoading(false);
        }
    }, [timePeriod, setData, setError, setLoading]);

    useEffect(() => {
        // Initial fetch if no data or if we want to refresh on mount (optional)
        // For now, let's fetch if overview is missing
        if (!overview) {
            fetchAnalytics();
        }
    }, [fetchAnalytics, overview]);

    // When time period changes, we need to refetch. 
    // We can do this by checking if the current data matches the requested range? 
    // For now, let's just trigger fetch when the user changes the selection.

    const onPeriodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const days = Number(e.target.value);
        const end = new Date();
        const start = new Date();
        start.setDate(end.getDate() - days);
        setDateRange(start, end);

        // We need to wait for state update or pass the new days directly.
        // Since setDateRange is sync in Zustand (mostly), but the effect might be better.
        // Let's just force a fetch with the new days.
        // Actually, let's just rely on the store update and a separate effect?
        // No, let's keep it simple.

        // We will trigger a fetch manually here to ensure it happens.
        // But wait, fetchAnalytics uses the store's dateRange (via timePeriod variable).
        // So we need to wait for the store to update.
        // Zustand updates are synchronous.

        // However, timePeriod is a const derived from the hook return. 
        // It won't update until the next render.
        // So we should pass the days directly to a fetch function or use an effect.

        // Let's use an effect that watches `dateRange`.
    };

    useEffect(() => {
        // This effect runs when dateRange changes.
        // We should fetch data.
        // But we want to avoid double fetching on mount.
        // On mount, dateRange is set to default.
        // If we have data, we might not want to fetch?
        // Let's just fetch. It's safer.
        fetchAnalytics();
    }, [dateRange, fetchAnalytics]);


    if (isLoading && !overview) { // Only show full loading if no data
        return (
            <main className="min-h-screen bg-background p-6">
                <div className="max-w-7xl mx-auto">
                    <div className="animate-pulse space-y-6">
                        <div className="h-8 bg-muted rounded w-1/3" />
                        <div className="grid grid-cols-4 gap-4">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="h-24 bg-muted rounded" />
                            ))}
                        </div>
                        <div className="h-64 bg-muted rounded" />
                    </div>
                </div>
            </main>
        );
    }

    if (error && !overview) {
        return (
            <main className="min-h-screen bg-background p-6">
                <div className="max-w-7xl mx-auto">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                        {error}
                        <button onClick={fetchAnalytics} className="ml-4 underline">Retry</button>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-background app-grid-pattern">
            {/* Header */}
            <header className="border-b border-border/50 bg-white/70 dark:bg-black/70 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">Analytics Dashboard</h1>
                            <p className="text-muted-foreground">Class-wide insights and engagement trends</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <select
                                value={timePeriod}
                                onChange={onPeriodChange}
                                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                                aria-label="Select time period"
                            >
                                <option value={7}>Last 7 days</option>
                                <option value={14}>Last 14 days</option>
                                <option value={30}>Last 30 days</option>
                                <option value={90}>Last 90 days</option>
                            </select>
                            <a
                                href="/teacher"
                                className="text-sm text-nexus-primary hover:underline"
                            >
                                ← Back to Reports
                            </a>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-6 space-y-6">
                {/* Overview Stats */}
                <section>
                    <h2 className="text-lg font-semibold text-foreground mb-4">This Week at a Glance</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard
                            title="Active Students"
                            value={overview?.active_students_this_week ?? 0}
                            subtitle={`of ${overview?.total_students ?? 0} total`}
                            icon={<UsersIcon />}
                        />
                        <StatCard
                            title="Practice Sessions"
                            value={overview?.total_sessions_this_week ?? 0}
                            subtitle={`${overview?.avg_session_duration_minutes?.toFixed(1) ?? 0} min avg`}
                            icon={<TrendingUpIcon />}
                        />
                        <StatCard
                            title="Total Practice Time"
                            value={`${Math.round(overview?.total_practice_minutes_this_week ?? 0)} min`}
                            subtitle="across all students"
                            icon={<ClockIcon />}
                        />
                        <StatCard
                            title="High Engagement"
                            value={`${Math.round((overview?.high_engagement_rate ?? 0) * 100)}%`}
                            subtitle={`${overview?.reports_pending_review ?? 0} reports pending`}
                            icon={<BookOpenIcon />}
                            trend={overview && overview.high_engagement_rate > 0.6 ? 'up' : 'neutral'}
                        />
                    </div>
                </section>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Engagement Trend */}
                    <div className="lg:col-span-2">
                        <div className="glass-card p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-lg font-semibold text-foreground">Engagement Trend</h2>
                                {engagement && (
                                    <div className="flex gap-4 text-sm">
                                        <span className="text-nexus-success">{engagement.overall_high_percentage}% High</span>
                                        <span className="text-nexus-warning">{engagement.overall_medium_percentage}% Med</span>
                                        <span className="text-nexus-error">{engagement.overall_low_percentage}% Low</span>
                                    </div>
                                )}
                            </div>
                            <EngagementChart data={engagement?.trend_data ?? []} />
                        </div>
                    </div>

                    {/* Struggling Students Alert */}
                    <div className="lg:col-span-1">
                        <div className="glass-card p-6 h-full">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertTriangleIcon />
                                <h2 className="text-lg font-semibold text-foreground">Needs Attention</h2>
                                {struggling && struggling.total_struggling > 0 && (
                                    <span className="bg-nexus-error/10 text-nexus-error text-xs px-2 py-1 rounded-full">
                                        {struggling.total_struggling}
                                    </span>
                                )}
                            </div>

                            {struggling && struggling.alerts.length > 0 ? (
                                <div className="space-y-3 max-h-64 overflow-y-auto">
                                    {struggling.alerts.slice(0, 5).map((alert, idx) => (
                                        <StrugglingStudentCard key={idx} alert={alert} />
                                    ))}
                                </div>
                            ) : (
                                <div className="h-32 flex items-center justify-center text-muted-foreground">
                                    <div className="text-center">
                                        <div className="text-2xl mb-2">✨</div>
                                        <div>All students engaged!</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Curriculum Coverage */}
                <section>
                    <div className="glass-card p-6">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <h2 className="text-lg font-semibold text-foreground">Curriculum Coverage</h2>
                                <p className="text-sm text-muted-foreground">
                                    Alberta Program of Studies outcomes practiced
                                </p>
                            </div>
                            {curriculum && (
                                <div className="text-right">
                                    <div className="text-2xl font-bold text-foreground">
                                        {curriculum.coverage_percentage}%
                                    </div>
                                    <div className="text-sm text-muted-foreground">
                                        {curriculum.total_outcomes_covered} of {curriculum.total_outcomes_available} outcomes
                                    </div>
                                </div>
                            )}
                        </div>
                        <CurriculumHeatmap items={curriculum?.outcomes ?? []} />

                        {curriculum && (curriculum.most_practiced_subject || curriculum.least_practiced_subject) && (
                            <div className="mt-4 flex gap-4 text-sm">
                                {curriculum.most_practiced_subject && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-nexus-success">↑ Most practiced:</span>
                                        <span className="font-medium">{curriculum.most_practiced_subject}</span>
                                    </div>
                                )}
                                {curriculum.least_practiced_subject && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-orange-600">↓ Needs focus:</span>
                                        <span className="font-medium">{curriculum.least_practiced_subject}</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </main>
    );
}
