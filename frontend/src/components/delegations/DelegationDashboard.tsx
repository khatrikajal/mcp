import { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import type { MeetingDelegation, DelegationStats } from "../../types";
import { cn } from "../../lib/cn";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Modal, ModalHeader, ModalBody, ModalFooter, ConfirmModal } from "../ui/Modal";
import { DelegationCardSkeleton, StatCardSkeleton } from "../ui/Skeleton";
import { toast } from "../ui/Toast";
import { MeetingCard } from "./MeetingCard";
import { DelegationReport } from "./DelegationReport";

type FilterTab = "all" | "pending" | "upcoming" | "completed";

export function DelegationDashboard() {
  const [delegations, setDelegations] = useState<MeetingDelegation[]>([]);
  const [stats, setStats] = useState<DelegationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [processing, setProcessing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Confirmation modal state
  const [confirmAction, setConfirmAction] = useState<{
    type: "approve" | "reject";
    delegationId: number;
    title: string;
  } | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const loadData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      else setRefreshing(true);
      setError(null);

      // Load delegations based on active tab
      let data: MeetingDelegation[];
      switch (activeTab) {
        case "pending":
          data = await api.getPendingDelegations();
          break;
        case "upcoming":
          data = await api.getUpcomingDelegations(60);
          break;
        case "completed":
          data = await api.getDelegations({ status: "completed", limit: 20 });
          break;
        default:
          data = await api.getDelegations({ limit: 50 });
      }

      setDelegations(data);

      // Also load stats
      const statsData = await api.getDelegationStats();
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load delegations:", err);
      setError("Failed to load meeting delegations");
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

  const handleApprove = async (id: number) => {
    setConfirmAction({
      type: "approve",
      delegationId: id,
      title: delegations.find((d) => d.id === id)?.meeting_title || "this meeting",
    });
  };

  const handleReject = async (id: number) => {
    setConfirmAction({
      type: "reject",
      delegationId: id,
      title: delegations.find((d) => d.id === id)?.meeting_title || "this meeting",
    });
    setRejectReason("");
  };

  const confirmApproval = async () => {
    if (!confirmAction) return;
    try {
      await api.approveDelegation(confirmAction.delegationId);
      toast.success("Delegation approved", "AI will join this meeting");
      await loadData(false);
    } catch (err) {
      console.error("Failed to approve delegation:", err);
      toast.error("Failed to approve", "Please try again");
    } finally {
      setConfirmAction(null);
    }
  };

  const confirmRejection = async () => {
    if (!confirmAction) return;
    try {
      await api.rejectDelegation(confirmAction.delegationId, rejectReason || undefined);
      toast.success("Delegation rejected", "AI will not join this meeting");
      await loadData(false);
    } catch (err) {
      console.error("Failed to reject delegation:", err);
      toast.error("Failed to reject", "Please try again");
    } finally {
      setConfirmAction(null);
      setRejectReason("");
    }
  };

  const handleJoinMeeting = async (id: number) => {
    try {
      await api.joinMeeting(id);
      toast.success("Joining meeting", "AI is connecting to the meeting");
      await loadData(false);
    } catch (err) {
      console.error("Failed to join meeting:", err);
      toast.error("Failed to join", "Could not connect to meeting");
    }
  };

  const handleProcessMeetings = async () => {
    try {
      setProcessing(true);
      const created = await api.processMeetings(24);
      if (created.length > 0) {
        toast.success(
          `Found ${created.length} meeting(s)`,
          "New delegations have been created"
        );
      } else {
        toast.info("No new meetings", "Calendar is up to date");
      }
      await loadData(false);
    } catch (err) {
      console.error("Failed to process meetings:", err);
      toast.error("Failed to scan calendar", "Please try again");
    } finally {
      setProcessing(false);
    }
  };

  const tabs: { key: FilterTab; label: string; count?: number }[] = [
    { key: "all", label: "All Meetings", count: stats?.total },
    { key: "pending", label: "Needs Approval", count: stats?.pending },
    { key: "upcoming", label: "Upcoming" },
    { key: "completed", label: "Completed", count: stats?.completed },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Meeting Delegations
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            AI-powered meeting attendance, transcription, and reporting
          </p>
        </div>
        <div className="flex items-center gap-3">
          {refreshing && (
            <span className="text-sm text-slate-500 animate-pulse">
              Refreshing...
            </span>
          )}
          <Button
            onClick={handleProcessMeetings}
            disabled={processing}
            variant="outline"
            className="gap-2"
          >
            {processing ? (
              <>
                <span className="animate-spin">⟳</span>
                Scanning...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Scan Calendar
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : stats ? (
          <>
            <StatCard label="Total" value={stats.total} icon="📅" />
            <StatCard
              label="Pending"
              value={stats.pending}
              icon="⏳"
              variant={stats.pending > 0 ? "warning" : "default"}
            />
            <StatCard label="Approved" value={stats.approved} icon="✅" variant="info" />
            <StatCard label="Completed" value={stats.completed} icon="✓" variant="success" />
            <StatCard
              label="Failed"
              value={stats.failed}
              icon="❌"
              variant={stats.failed > 0 ? "danger" : "default"}
            />
          </>
        ) : null}
      </div>

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
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300"
              )}
            >
              {tab.label}
              {tab.count !== undefined && (
                <Badge
                  variant={
                    tab.key === "pending" && tab.count > 0
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
      ) : delegations.length === 0 ? (
        <EmptyState activeTab={activeTab} onScanCalendar={handleProcessMeetings} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {delegations.map((delegation) => (
            <MeetingCard
              key={delegation.id}
              delegation={delegation}
              onApprove={handleApprove}
              onReject={handleReject}
              onJoinMeeting={handleJoinMeeting}
              onViewReport={setSelectedReportId}
            />
          ))}
        </div>
      )}

      {/* Report Modal */}
      {selectedReportId && (
        <DelegationReport
          delegationId={selectedReportId}
          onClose={() => setSelectedReportId(null)}
          onSendReport={() => loadData(false)}
        />
      )}

      {/* Approve Confirmation Modal */}
      <ConfirmModal
        open={confirmAction?.type === "approve"}
        onClose={() => setConfirmAction(null)}
        onConfirm={confirmApproval}
        title="Approve Delegation"
        description={`Allow AI to join "${confirmAction?.title}"? The AI will record the meeting, take notes, and generate a summary report.`}
        confirmText="Approve & Enable"
        variant="info"
      />

      {/* Reject Modal with Reason */}
      <Modal
        open={confirmAction?.type === "reject"}
        onClose={() => setConfirmAction(null)}
        size="sm"
      >
        <ModalHeader onClose={() => setConfirmAction(null)}>
          Reject Delegation
        </ModalHeader>
        <ModalBody>
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            The AI will not join "{confirmAction?.title}". You can optionally
            provide a reason.
          </p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Reason for rejection (optional)"
            className="w-full px-3 py-2 border rounded-lg dark:border-slate-700 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            rows={3}
          />
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setConfirmAction(null)}>
            Cancel
          </Button>
          <Button onClick={confirmRejection}>
            Reject Delegation
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  label: string;
  value: number;
  icon: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

function StatCard({ label, value, icon, variant = "default" }: StatCardProps) {
  const variantStyles = {
    default: "bg-white dark:bg-slate-800",
    success: "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800",
    warning: "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800",
    danger: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    info: "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800",
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
      <p className="text-3xl font-bold text-slate-900 dark:text-white">{value}</p>
    </div>
  );
}

// Empty State Component
interface EmptyStateProps {
  activeTab: FilterTab;
  onScanCalendar: () => void;
}

function EmptyState({ activeTab, onScanCalendar }: EmptyStateProps) {
  const messages: Record<
    FilterTab,
    { icon: string; title: string; description: string; action?: boolean }
  > = {
    all: {
      icon: "📅",
      title: "No Meeting Delegations",
      description:
        "Scan your calendar to find upcoming meetings for AI delegation.",
      action: true,
    },
    pending: {
      icon: "✅",
      title: "All Caught Up!",
      description: "No meetings are waiting for your approval.",
    },
    upcoming: {
      icon: "🕐",
      title: "No Upcoming Meetings",
      description: "No approved delegations for meetings starting soon.",
    },
    completed: {
      icon: "📝",
      title: "No Completed Reports",
      description: "Meeting reports will appear here after AI attends meetings.",
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
        <Button onClick={onScanCalendar} className="gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Scan Calendar for Meetings
        </Button>
      )}
    </div>
  );
}

// Error State Component
function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-6xl mb-4">⚠️</span>
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
