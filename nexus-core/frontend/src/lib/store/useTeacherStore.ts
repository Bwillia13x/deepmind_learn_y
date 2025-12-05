import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
    ClassOverviewStats,
    EngagementTrendResponse,
    StrugglingStudentsResponse,
    CurriculumCoverageResponse,
} from '@/lib/types/api';

interface TeacherState {
    // UI State
    selectedClassId: string | null;
    dateRange: {
        start: Date;
        end: Date;
    };

    // Data Cache
    overviewStats: ClassOverviewStats | null;
    engagementTrends: EngagementTrendResponse | null;
    strugglingStudents: StrugglingStudentsResponse | null;
    curriculumCoverage: CurriculumCoverageResponse | null;

    // Fetch Status
    isLoading: boolean;
    error: string | null;
    lastFetched: number | null;

    // Actions
    setSelectedClassId: (classId: string) => void;
    setDateRange: (start: Date, end: Date) => void;
    setLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
    setData: (data: {
        overviewStats?: ClassOverviewStats;
        engagementTrends?: EngagementTrendResponse;
        strugglingStudents?: StrugglingStudentsResponse;
        curriculumCoverage?: CurriculumCoverageResponse;
    }) => void;
    reset: () => void;
}

export const useTeacherStore = create<TeacherState>()(
    devtools(
        persist(
            (set) => ({
                selectedClassId: 'class-101', // Default for prototype
                dateRange: {
                    start: new Date(new Date().setDate(new Date().getDate() - 30)), // Last 30 days
                    end: new Date(),
                },

                overviewStats: null,
                engagementTrends: null,
                strugglingStudents: null,
                curriculumCoverage: null,

                isLoading: false,
                error: null,
                lastFetched: null,

                setSelectedClassId: (classId) => set({ selectedClassId: classId }),
                setDateRange: (start, end) => set({ dateRange: { start, end } }),
                setLoading: (isLoading) => set({ isLoading }),
                setError: (error) => set({ error }),
                setData: (data) => set((state) => ({
                    ...state,
                    ...data,
                    lastFetched: Date.now(),
                    error: null,
                })),
                reset: () => set({
                    selectedClassId: null,
                    overviewStats: null,
                    engagementTrends: null,
                    strugglingStudents: null,
                    curriculumCoverage: null,
                    isLoading: false,
                    error: null,
                    lastFetched: null,
                }),
            }),
            {
                name: 'nexus-teacher-storage',
                partialize: (state) => ({
                    selectedClassId: state.selectedClassId,
                    // Don't persist large data blobs or dates (dates need serialization handling)
                    // For now, just persist selection
                }),
            }
        )
    )
);
