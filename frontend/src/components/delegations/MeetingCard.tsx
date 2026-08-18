import { useState } from "react";
import type { MeetingDelegation, MeetingImportance, DelegationStatus } from "../../types";
import { Button } from "../ui/Button";

interface MeetingCardProps {
  delegation: MeetingDelegation;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onViewReport?: (id: number) => void;
  onJoinMeeting?: (id: number) => void;
}

export function MeetingCard({
  delegation,
  onApprove,
  onReject,
  onViewReport,
  onJoinMeeting,
}: MeetingCardProps) {
  const [processing, setProcessing] = useState(false);

  const handleApprove = async () => {
    if (!onApprove) return;
    setProcessing(true);
    try {
      await onApprove(delegation.id);
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!onReject) return;
    setProcessing(true);
    try {
      await onReject(delegation.id);
    } finally {
      setProcessing(false);
    }
  };

  const handleJoin = async () => {
    if (!onJoinMeeting) return;
    setProcessing(true);
    try {
      await onJoinMeeting(delegation.id);
    } finally {
      setProcessing(false);
    }
  };

  const startTime = new Date(delegation.meeting_start_time);
  const endTime = new Date(delegation.meeting_end_time);
  const now = new Date();
  const isUpcoming = startTime > now;
  const isOngoing = startTime <= now && endTime >= now;

  return (
    <div className="border rounded-lg p-4 bg-card">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{delegation.meeting_title}</h3>
          <p className="text-sm text-muted-foreground">
            {formatDateTime(startTime)} - {formatTime(endTime)}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <ImportanceBadge importance={delegation.importance} />
          <StatusBadge status={delegation.status} />
        </div>
      </div>

      {/* Meeting Info */}
      {delegation.meeting_description && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {delegation.meeting_description}
        </p>
      )}

      {/* Attendees */}
      {delegation.meeting_attendees.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-muted-foreground">Attendees:</span>
          <div className="flex flex-wrap gap-1">
            {delegation.meeting_attendees.slice(0, 3).map((attendee, idx) => (
              <span
                key={idx}
                className="text-xs bg-muted px-2 py-0.5 rounded"
              >
                {attendee.name || attendee.email}
              </span>
            ))}
            {delegation.meeting_attendees.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{delegation.meeting_attendees.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Importance Reasons */}
      {delegation.importance_reasons.length > 0 && (
        <div className="bg-muted/50 rounded p-2 mb-3">
          <p className="text-xs font-medium mb-1">Classification Reasons:</p>
          <ul className="text-xs text-muted-foreground space-y-0.5">
            {delegation.importance_reasons.slice(0, 3).map((reason, idx) => (
              <li key={idx}>• {reason}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Auto-approval indicator */}
      {delegation.auto_approved && (
        <p className="text-xs text-green-600 mb-3">
          ✓ Auto-approved (importance: {delegation.importance})
        </p>
      )}

      {/* Error message */}
      {delegation.error_message && (
        <p className="text-xs text-destructive mb-3">
          Error: {delegation.error_message}
        </p>
      )}

      {/* Report summary (if completed) */}
      {delegation.status === "completed" && delegation.report_summary && (
        <div className="bg-muted/50 rounded p-2 mb-3">
          <p className="text-xs font-medium mb-1">Summary:</p>
          <p className="text-xs text-muted-foreground line-clamp-3">
            {delegation.report_summary}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-3">
        {delegation.status === "pending" && (
          <>
            <Button
              size="sm"
              onClick={handleApprove}
              disabled={processing}
              className="flex-1"
            >
              {processing ? "..." : "Approve"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleReject}
              disabled={processing}
              className="flex-1"
            >
              Reject
            </Button>
          </>
        )}

        {delegation.status === "approved" && isUpcoming && (
          <Button
            size="sm"
            onClick={handleJoin}
            disabled={processing}
          >
            {processing ? "Joining..." : "Join Now"}
          </Button>
        )}

        {delegation.status === "joined" && isOngoing && (
          <span className="text-sm text-green-600 flex items-center gap-1">
            <span className="animate-pulse">●</span> AI is in the meeting
          </span>
        )}

        {delegation.status === "completed" && onViewReport && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewReport(delegation.id)}
          >
            View Report
          </Button>
        )}

        {delegation.status === "completed" && !delegation.report_sent && (
          <Button size="sm" variant="outline">
            Send Report
          </Button>
        )}

        {delegation.report_sent && (
          <span className="text-xs text-muted-foreground">
            ✓ Report sent
          </span>
        )}
      </div>
    </div>
  );
}

function ImportanceBadge({ importance }: { importance: MeetingImportance }) {
  const colors: Record<MeetingImportance, string> = {
    critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    low: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  };

  const icons: Record<MeetingImportance, string> = {
    critical: "🔴",
    high: "🟠",
    medium: "🟡",
    low: "🟢",
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded ${colors[importance]}`}>
      {icons[importance]} {importance.charAt(0).toUpperCase() + importance.slice(1)}
    </span>
  );
}

function StatusBadge({ status }: { status: DelegationStatus }) {
  const colors: Record<DelegationStatus, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    approved: "bg-blue-100 text-blue-800",
    rejected: "bg-gray-100 text-gray-800",
    joining: "bg-blue-100 text-blue-800",
    joined: "bg-green-100 text-green-800",
    recording: "bg-purple-100 text-purple-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };

  const labels: Record<DelegationStatus, string> = {
    pending: "Pending Approval",
    approved: "Approved",
    rejected: "Rejected",
    joining: "Joining...",
    joined: "In Meeting",
    recording: "Recording",
    completed: "Completed",
    failed: "Failed",
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded ${colors[status]}`}>
      {labels[status]}
    </span>
  );
}

function formatDateTime(date: Date): string {
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}
