import { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import type { MeetingDelegation, DelegationStats } from "../../types";
import { Button } from "../ui/Button";
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

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
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
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleApprove = async (id: number) => {
    try {
      await api.approveDelegation(id);
      await loadData();
    } catch (err) {
      console.error("Failed to approve delegation:", err);
      alert("Failed to approve delegation");
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt("Reason for rejection (optional):");
    try {
      await api.rejectDelegation(id, reason || undefined);
      await loadData();
    } catch (err) {
      console.error("Failed to reject delegation:", err);
      alert("Failed to reject delegation");
    }
  };

  const handleJoinMeeting = async (id: number) => {
    try {
      await api.joinMeeting(id);
      await loadData();
    } catch (err) {
      console.error("Failed to join meeting:", err);
      alert("Failed to join meeting");
    }
  };

  const handleProcessMeetings = async () => {
    try {
      setProcessing(true);
      const created = await api.processMeetings(24);
      alert(`Processed ${created.length} upcoming meeting(s)`);
      await loadData();
    } catch (err) {
      console.error("Failed to process meetings:", err);
      alert("Failed to process meetings");
    } finally {
      setProcessing(false);
    }
  };

  const tabs: { key: FilterTab; label: string; count?: number }[] = [
    { key: "all", label: "All", count: stats?.total },
    { key: "pending", label: "Pending", count: stats?.pending },
    { key: "upcoming", label: "Upcoming" },
    { key: "completed", label: "Completed", count: stats?.completed },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Meeting Delegations</h1>
          <p className="text-muted-foreground">
            AI-powered meeting attendance and reporting
          </p>
        </div>
        <Button
          onClick={handleProcessMeetings}
          disabled={processing}
          variant="outline"
        >
          {processing ? "Processing..." : "Scan Calendar"}
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            label="Total"
            value={stats.total}
            icon="📅"
          />
          <StatCard
            label="Pending"
            value={stats.pending}
            icon="⏳"
            highlight={stats.pending > 0}
          />
          <StatCard
            label="Approved"
            value={stats.approved}
            icon="✅"
          />
          <StatCard
            label="Completed"
            value={stats.completed}
            icon="✓"
          />
          <StatCard
            label="Failed"
            value={stats.failed}
            icon="❌"
            danger={stats.failed > 0}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-1 text-xs bg-muted px-1.5 py-0.5 rounded">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading delegations...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-destructive/10 text-destructive rounded">
          {error}
        </div>
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
          onSendReport={loadData}
        />
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  icon: string;
  highlight?: boolean;
  danger?: boolean;
}

function StatCard({ label, value, icon, highlight, danger }: StatCardProps) {
  let bgClass = "bg-card";
  if (highlight) bgClass = "bg-yellow-50 dark:bg-yellow-900/20";
  if (danger && value > 0) bgClass = "bg-red-50 dark:bg-red-900/20";

  return (
    <div className={`${bgClass} border rounded-lg p-4`}>
      <div className="flex items-center gap-2 mb-1">
        <span>{icon}</span>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

interface EmptyStateProps {
  activeTab: FilterTab;
  onScanCalendar: () => void;
}

function EmptyState({ activeTab, onScanCalendar }: EmptyStateProps) {
  const messages: Record<FilterTab, { title: string; description: string }> = {
    all: {
      title: "No Meeting Delegations",
      description: "Scan your calendar to find upcoming meetings for AI delegation.",
    },
    pending: {
      title: "No Pending Approvals",
      description: "All meeting delegations have been processed.",
    },
    upcoming: {
      title: "No Upcoming Meetings",
      description: "No approved delegations for meetings starting soon.",
    },
    completed: {
      title: "No Completed Reports",
      description: "Completed meeting reports will appear here.",
    },
  };

  const message = messages[activeTab];

  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <p className="text-lg text-muted-foreground mb-2">{message.title}</p>
      <p className="text-sm text-muted-foreground mb-4">{message.description}</p>
      {activeTab === "all" && (
        <Button onClick={onScanCalendar}>
          Scan Calendar for Meetings
        </Button>
      )}
    </div>
  );
}
