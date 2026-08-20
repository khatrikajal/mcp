import { format, formatDistanceToNow, isFuture, differenceInMinutes } from "date-fns";
import type { InterviewSession } from "../../types";
import { cn } from "../../lib/cn";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

interface InterviewCardProps {
  interview: InterviewSession;
  onGenerateQuestions: (id: number) => void;
  onStart: (id: number) => void;
  onEnd: (id: number) => void;
  onCancel: (interview: InterviewSession) => void;
  onViewReport: (id: number) => void;
}

export function InterviewCard({
  interview,
  onGenerateQuestions,
  onStart,
  onEnd,
  onCancel,
  onViewReport,
}: InterviewCardProps) {
  const scheduledTime = new Date(interview.scheduled_time);
  const isUpcoming = isFuture(scheduledTime);
  const minutesUntil = differenceInMinutes(scheduledTime, new Date());
  const isStartingSoon = minutesUntil > 0 && minutesUntil <= 15;

  const statusConfig: Record<
    string,
    { label: string; variant: "default" | "success" | "warning" | "danger" | "info" }
  > = {
    scheduled: { label: "Scheduled", variant: "default" },
    preparing: { label: "Preparing", variant: "info" },
    ready: { label: "Ready", variant: "success" },
    in_progress: { label: "In Progress", variant: "warning" },
    analyzing: { label: "Analyzing", variant: "info" },
    completed: { label: "Completed", variant: "success" },
    cancelled: { label: "Cancelled", variant: "danger" },
    failed: { label: "Failed", variant: "danger" },
  };

  const typeConfig: Record<string, { icon: string; label: string }> = {
    technical: { icon: "💻", label: "Technical" },
    behavioral: { icon: "🤝", label: "Behavioral" },
    hr: { icon: "👤", label: "HR" },
    mixed: { icon: "📋", label: "Mixed" },
  };

  const recommendationConfig: Record<
    string,
    { label: string; color: string }
  > = {
    strong_hire: { label: "Strong Hire", color: "text-emerald-600 dark:text-emerald-400" },
    hire: { label: "Hire", color: "text-green-600 dark:text-green-400" },
    maybe: { label: "Maybe", color: "text-amber-600 dark:text-amber-400" },
    no_hire: { label: "No Hire", color: "text-orange-600 dark:text-orange-400" },
    strong_no_hire: { label: "Strong No", color: "text-red-600 dark:text-red-400" },
  };

  const status = statusConfig[interview.status] || statusConfig.scheduled;
  const type = typeConfig[interview.interview_type] || typeConfig.mixed;

  return (
    <div
      className={cn(
        "rounded-xl border bg-white dark:bg-slate-800 transition-all hover:shadow-lg",
        isStartingSoon && interview.status === "ready" && "ring-2 ring-purple-500",
        interview.status === "in_progress" && "ring-2 ring-amber-500 animate-pulse"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b dark:border-slate-700">
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 dark:text-white truncate">
              {interview.candidate_name}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
              {interview.position_title}
            </p>
          </div>
          <Badge variant={status.variant} size="sm">
            {status.label}
          </Badge>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Interview Type */}
        <div className="flex items-center gap-2 text-sm">
          <span>{type.icon}</span>
          <span className="text-slate-600 dark:text-slate-400">{type.label} Interview</span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-600 dark:text-slate-400">
            {interview.duration_minutes} min
          </span>
        </div>

        {/* Scheduled Time */}
        <div className="flex items-center gap-2 text-sm">
          <svg
            className="w-4 h-4 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <span className="text-slate-600 dark:text-slate-400">
            {format(scheduledTime, "MMM d, yyyy 'at' h:mm a")}
          </span>
        </div>

        {/* Time indicator */}
        {isUpcoming && interview.status !== "completed" && (
          <div
            className={cn(
              "text-xs font-medium",
              isStartingSoon
                ? "text-purple-600 dark:text-purple-400"
                : "text-slate-500 dark:text-slate-400"
            )}
          >
            {isStartingSoon
              ? `Starting in ${minutesUntil} minutes`
              : `Starts ${formatDistanceToNow(scheduledTime, { addSuffix: true })}`}
          </div>
        )}

        {/* Questions count */}
        {interview.questions_count > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <svg
              className="w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-slate-600 dark:text-slate-400">
              {interview.questions_count} questions prepared
            </span>
          </div>
        )}

        {/* Score & Recommendation (for completed) */}
        {interview.status === "completed" && interview.overall_score !== undefined && (
          <div className="mt-4 pt-4 border-t dark:border-slate-700">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-sm text-slate-500 dark:text-slate-400">Score</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {interview.overall_score}%
                </div>
              </div>
              {interview.recommendation && (
                <div className="text-right">
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Recommendation
                  </div>
                  <div
                    className={cn(
                      "text-lg font-semibold",
                      recommendationConfig[interview.recommendation]?.color
                    )}
                  >
                    {recommendationConfig[interview.recommendation]?.label}
                  </div>
                </div>
              )}
            </div>

            {/* Competency scores preview */}
            {Object.keys(interview.competency_scores).length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(interview.competency_scores)
                  .slice(0, 3)
                  .map(([competency, score]) => (
                    <span
                      key={competency}
                      className="text-xs px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                    >
                      {competency.replace("_", " ")}: {score}/10
                    </span>
                  ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="p-4 pt-0 flex flex-wrap gap-2">
        {/* Scheduled - Generate Questions */}
        {interview.status === "scheduled" && (
          <>
            <Button
              size="sm"
              onClick={() => onGenerateQuestions(interview.id)}
              className="flex-1"
            >
              Generate Questions
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCancel(interview)}
            >
              Cancel
            </Button>
          </>
        )}

        {/* Ready - Start Interview */}
        {interview.status === "ready" && (
          <>
            <Button
              size="sm"
              onClick={() => onStart(interview.id)}
              className="flex-1 gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Start Interview
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCancel(interview)}
            >
              Cancel
            </Button>
          </>
        )}

        {/* In Progress - End Interview */}
        {interview.status === "in_progress" && (
          <Button
            size="sm"
            onClick={() => onEnd(interview.id)}
            className="flex-1 gap-2 bg-amber-600 hover:bg-amber-700"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
              />
            </svg>
            End & Analyze
          </Button>
        )}

        {/* Completed - View Report */}
        {interview.status === "completed" && (
          <Button
            size="sm"
            onClick={() => onViewReport(interview.id)}
            className="flex-1 gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            View Report
          </Button>
        )}

        {/* Analyzing - Show progress */}
        {interview.status === "analyzing" && (
          <div className="flex-1 flex items-center justify-center gap-2 text-sm text-purple-600 dark:text-purple-400">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Analyzing responses...
          </div>
        )}
      </div>
    </div>
  );
}
