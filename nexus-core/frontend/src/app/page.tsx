import Link from 'next/link';

export default function HomePage(): React.ReactElement {
    return (
        <main className="min-h-screen bg-background app-grid-pattern relative overflow-hidden">
            {/* Background Gradient Blobs */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-nexus-primary/10 rounded-full blur-3xl -z-10 opacity-50 animate-pulse-soft" />
            <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-nexus-secondary/10 rounded-full blur-3xl -z-10 opacity-30" />

            {/* Hero Section */}
            <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center min-h-screen relative z-10">
                {/* Logo & Badge */}
                <div className="mb-8 flex flex-col items-center animate-fade-in">
                    <div className="px-3 py-1 rounded-full bg-nexus-primary/10 border border-nexus-primary/20 text-nexus-primary text-xs font-medium mb-6 uppercase tracking-wider">
                        Alberta Education Pilot • Winter 2025
                    </div>
                    <h1 className="text-6xl md:text-7xl font-bold text-gradient-primary tracking-tight mb-4 text-center">
                        NEXUS
                    </h1>
                    <p className="text-xl md:text-2xl text-center text-muted-foreground font-light max-w-2xl">
                        Digital Para-Educator Assistant
                    </p>
                </div>

                {/* Description */}
                <div className="max-w-2xl text-center mb-16 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                    <p className="text-lg text-foreground/80 leading-relaxed">
                        AI-powered oracy practice partner for Alberta K-12 EAL students.
                        <br className="hidden md:block" />
                        Practice speaking in a safe, encouraging environment aligned with
                        curriculum outcomes.
                    </p>
                </div>

                {/* Entry Points */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl animate-slide-up" style={{ animationDelay: '0.2s' }}>
                    {/* Student Entry */}
                    <Link
                        href="/student"
                        className="group relative overflow-hidden rounded-2xl glass-card p-8 transition-all hover:-translate-y-1 hover:shadow-xl hover:border-nexus-primary/50"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-nexus-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="flex flex-col items-center relative z-10">
                            <div className="w-20 h-20 rounded-2xl bg-nexus-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                                <StudentIcon className="w-10 h-10 text-nexus-primary" />
                            </div>
                            <h2 className="text-2xl font-bold mb-3 text-foreground">Student Practice</h2>
                            <p className="text-base text-muted-foreground text-center leading-relaxed">
                                Start a voice conversation to practice speaking English with a friendly AI tutor.
                            </p>
                            <div className="mt-6 px-6 py-2 rounded-full bg-nexus-primary text-white font-medium text-sm opacity-0 transform translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300">
                                Start Session →
                            </div>
                        </div>
                    </Link>

                    {/* Teacher Entry */}
                    <Link
                        href="/teacher"
                        className="group relative overflow-hidden rounded-2xl glass-card p-8 transition-all hover:-translate-y-1 hover:shadow-xl hover:border-nexus-secondary/50"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-nexus-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="flex flex-col items-center relative z-10">
                            <div className="w-20 h-20 rounded-2xl bg-nexus-secondary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                                <TeacherIcon className="w-10 h-10 text-nexus-secondary" />
                            </div>
                            <h2 className="text-2xl font-bold mb-3 text-foreground">Teacher Dashboard</h2>
                            <p className="text-base text-muted-foreground text-center leading-relaxed">
                                Review automated &quot;Scout Reports&quot;, track progress, and generate IPP insights.
                            </p>
                            <div className="mt-6 px-6 py-2 rounded-full bg-nexus-secondary text-white font-medium text-sm opacity-0 transform translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300">
                                View Dashboard →
                            </div>
                        </div>
                    </Link>
                </div>

                {/* Privacy Notice */}
                <div className="mt-20 max-w-lg text-center animate-fade-in" style={{ animationDelay: '0.4s' }}>
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-muted/50 border border-border/50 text-xs text-muted-foreground">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3 text-nexus-success">
                            <path fillRule="evenodd" d="M12 1.5a5.25 5.25 0 00-5.25 5.25v3a3 3 0 00-3 3v6.75a3 3 0 003 3h10.5a3 3 0 003-3v-6.75a3 3 0 00-3-3v-3c0-2.9-2.35-5.25-5.25-5.25zm3.75 8.25v-3a3.75 3.75 0 10-7.5 0v3h7.5z" clipRule="evenodd" />
                        </svg>
                        Privacy-first design. Audio-only processing. FOIP compliant.
                    </div>
                </div>
            </div>
        </main>
    );
}

// === Icons ===

function StudentIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path d="M12 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0 9c-5.33 0-8 2.67-8 4v3h16v-3c0-1.33-2.67-4-8-4Z" />
        </svg>
    );
}

function TeacherIcon({ className }: { className?: string }): React.ReactElement {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={className}
        >
            <path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82ZM12 3 1 9l11 6 9-4.91V17h2V9L12 3Z" />
        </svg>
    );
}
