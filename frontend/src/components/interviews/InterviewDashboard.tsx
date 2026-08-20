import { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import type { InterviewSession, InterviewStats } from "../../types";
import { cn } from "../../lib/cn";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { ConfirmModal } from "../ui/Modal";
import { DelegationCardSkeleton, StatCardSkeleton } from "../ui/Skeleton";
import { toast } from "../ui/Toast";
import { InterviewScheduler } from "./InterviewScheduler";
import { InterviewCard } from "./InterviewCard";
import { InterviewReport } from "./InterviewReport";

type FilterTab = "all" | "upcoming" | "in_progress" | "completed";

export function InterviewDashboard() {
  const [interviews, setInterviews] = useState<InterviewSession[]>([]);
  const [stats, setStats] = useState<InterviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [showScheduler, setShowScheduler] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Cancel confirmation modal
  const [cancelInterview, setCancelInterview] = useState<InterviewSession | null>(null);

  const loadData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      else setRefreshing(true);
      setError(null);

      // Load interviews based on active tab
      let data: InterviewSession[];
      switch (activeTab) {
        case "upcoming":
          data = await api.getUpcomingInterviews(168); // 1 week ahead
          break;
        case "in_progress":
          data = await api.getInterviews({ status_filter: "in_progress" });
          break;
        case "completed":
          data = await api.getInterviews({ status_filter: "completed", limit: 20 });
          break;
        default:
          data = await api.getInterviews({ limit: 50 });
      }

      setInterviews(data);

      // Also load stats
      const statsData = await api.getInterviewStats();
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load interviews:", err);
      setError("Failed to load interview sessions");
      toast.error("Failed to load data", "Please try again");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(() => loadData(false), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleGenerateQuestions = async (id: number) => {
    try {
      const questions = await api.generateQuestions(id);
      toast.success(
        `Generated ${questions.length} questions`,
        "Interview is now ready to start"
      );
      await loadData(false);
    } catch (err) {
      console.error("Failed to generate questions:", err);
      toast.error("Failed to generate questions", "Please try again");
    }
  };

  const handleStartInterview = async (id: number) => {
    try {
      const result = await api.startInterview(id);
      toast.success(
        "Interview started",
        `AI is ready with ${result.total_questions} questions`
      );
      await loadData(false);
    } catch (err) {
      console.error("Failed to start interview:", err);
      toast.error("Failed to start interview", "Please try again");
    }
  };

  const handleEndInterview = async (id: number) => {
    try {
      const result = await api.endInterview(id);
      toast.success(
        `Analysis complete: Score ${result.overall_score}%`,
        `Recommendation: ${result.recommendation.replace("_", " ").toUpperCase()}`
      );
      await loadData(false);
    } catch (err) {
      console.error("Failed to end interview:", err);
      toast.error("Failed to end interview", "Please try again");
    }
  };

  const confirmCancelInterview = async () => {
    if (!cancelInterview) return;
    try {
      await api.cancelInterview(cancelInterview.id);
      toast.success("Interview cancelled", "The interview has been cancelled");
      await loadData(false);
    } catch (err) {
      console.error("Failed to cancel interview:", err);
      toast.error("Failed to cancel", "Please try again");
    } finally {
      setCancelInterview(null);
    }
  };

  const handleInterviewCreated = () => {
    setShowScheduler(false);
    loadData(false);
    toast.success("Interview scheduled", "Generate questions when ready");
  };

  const tabs: { key: FilterTab; label: string; count?: number }[] = [
    { key: "all", label: "All Interviews", count: stats?.total },
    { key: "upcoming", label: "Upcoming", count: (stats?.scheduled || 0) + (stats?.ready || 0) },
    { key: "in_progress", label: "In Progress", count: stats?.in_progress },
    { key: "completed", label: "Completed", count: stats?.completed },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            AI Interview Conductor
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            Automated interviews with AI-powered analysis and scoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          {refreshing && (
            <span className="text-sm text-slate-500 animate-pulse">
              Refreshing...
            </span>
          )}
          <Button onClick={() => setShowScheduler(true)} className="gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Schedule Interview
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : stats ? (
          <>
            <StatCard label="Total" value={stats.total} icon="📋" />
            <StatCard
              label="Scheduled"
              value={stats.scheduled + stats.ready}
              icon="📅"
              variant={stats.scheduled > 0 ? "info" : "default"}
            />
            <StatCard
              label="In Progress"
              value={stats.in_progress}
              icon="🎤"
              variant={stats.in_progress > 0 ? "warning" : "default"}
            />
            <StatCard
              label="Completed"
              value={stats.completed}
              icon="✓"
              variant="success"
            />
            <StatCard
              label="Avg Score"
              value={Math.round(stats.average_score)}
              icon="📊"
              suffix="%"
            />
          </>
        ) : null}
      </div>

      {/* Recommendation Distribution */}
      {stats && stats.completed > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Recommendation Distribution
          </h3>
          <div className="flex flex-wrap gap-3">
            <RecommendationBadge
              label="Strong Hire"
              count={stats.recommendations.strong_hire || 0}
              variant="success"
            />
            <RecommendationBadge
              label="Hire"
              count={stats.recommendations.hire || 0}
              variant="success"
            />
            <RecommendationBadge
              label="Maybe"
              count={stats.recommendations.maybe || 0}
              variant="warning"
            />
            <RecommendationBadge
              label="No Hire"
              count={stats.recommendations.no_hire || 0}
              variant="danger"
            />
            <RecommendationBadge
              label="Strong No"
              count={stats.recommendations.strong_no_hire || 0}
              variant="danger"
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b dark:border-slate-700">
        <nav className="flex gap-1 -mb-px" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              role="tab"
              aria-selected={activeTab === tab.key}
              className={cn(
                "px-4 py-3 text-sm font-medium border-b-2 transition-all",
                activeTab === tab.key
                  ? "border-purple-500 text-purple-600 dark:text-purple-400"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300"
              )}
            >
              {tab.label}
              {tab.count !== undefined && (
                <Badge
                  variant={
                    tab.key === "in_progress" && tab.count > 0
                      ? "warning"
                      : "default"
                  }
                  size="sm"
                  className="ml-2"
                >
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <DelegationCardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => loadData()} />
      ) : interviews.length === 0 ? (
        <EmptyState activeTab={activeTab} onSchedule={() => setShowScheduler(true)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {interviews.map((interview) => (
            <InterviewCard
              key={interview.id}
              interview={interview}
              onGenerateQuestions={handleGenerateQuestions}
              onStart={handleStartInterview}
              onEnd={handleEndInterview}
              onCancel={setCancelInterview}
              onViewReport={setSelectedReportId}
            />
          ))}
        </div>
      )}

      {/* Schedule Interview Modal */}
      {showScheduler && (
        <InterviewScheduler
          onClose={() => setShowScheduler(false)}
          onCreated={handleInterviewCreated}
        />
      )}

      {/* View Report Modal */}
      {selectedReportId && (
        <InterviewReport
          interviewId={selectedReportId}
          onClose={() => setSelectedReportId(null)}
        />
      )}

      {/* Cancel Confirmation Modal */}
      <ConfirmModal
        open={!!cancelInterview}
        onClose={() => setCancelInterview(null)}
        onConfirm={confirmCancelInterview}
        title="Cancel Interview"
        description={`Are you sure you want to cancel the interview with ${cancelInterview?.candidate_name}? This action cannot be undone.`}
        confirmText="Cancel Interview"
        variant="danger"
      />
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  label: string;
  value: number;
  icon: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  suffix?: string;
}

function StatCard({ label, value, icon, variant = "default", suffix = "" }: StatCardProps) {
  const variantStyles = {
    default: "bg-white dark:bg-slate-800",
    success: "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800",
    warning: "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800",
    danger: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    info: "bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800",
  };

  return (
    <div
      className={cn(
        "rounded-xl border p-4 transition-shadow hover:shadow-md",
        variantStyles[variant]
      )}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
          {label}
        </span>
      </div>
      <p className="text-3xl font-bold text-slate-900 dark:text-white">
        {value}{suffix}
      </p>
    </div>
  );
}

// Recommendation Badge Component
interface RecommendationBadgeProps {
  label: string;
  count: number;
  variant: "success" | "warning" | "danger";
}

function RecommendationBadge({ label, count, variant }: RecommendationBadgeProps) {
  const colors = {
    success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
    warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    danger: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  };

  return (
    <div className={cn("px-4 py-2 rounded-lg", colors[variant])}>
      <span className="font-semibold">{count}</span>
      <span className="ml-2">{label}</span>
    </div>
  );
}

// Empty State Component
interface EmptyStateProps {
  activeTab: FilterTab;
  onSchedule: () => void;
}

function EmptyState({ activeTab, onSchedule }: EmptyStateProps) {
  const messages: Record<
    FilterTab,
    { icon: string; title: string; description: string; action?: boolean }
  > = {
    all: {
      icon: "🎤",
      title: "No Interviews Scheduled",
      description: "Schedule your first AI-conducted interview to get started.",
      action: true,
    },
    upcoming: {
      icon: "📅",
      title: "No Upcoming Interviews",
      description: "No interviews are scheduled for the near future.",
      action: true,
    },
    in_progress: {
      icon: "⏳",
      title: "No Active Interviews",
      description: "No interviews are currently in progress.",
    },
    completed: {
      icon: "📝",
      title: "No Completed Interviews",
      description: "Interview reports will appear here after completion.",
    },
  };

  const message = messages[activeTab];

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-6xl mb-4">{message.icon}</span>
      <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
        {message.title}
      </h3>
      <p className="text-slate-600 dark:text-slate-400 max-w-md mb-6">
        {message.description}
      </p>
      {message.action && (
        <Button onClick={onSchedule} className="gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Schedule Interview
        </Button>
      )}
    </div>
  );
}

// Error State Component
function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-6xl mb-4">⚠</span>
      <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
        Something went wrong
      </h3>
      <p className="text-slate-600 dark:text-slate-400 max-w-md mb-6">{error}</p>
      <Button onClick={onRetry} variant="outline">
        Try Again
      </Button>
    </div>
  );
}
