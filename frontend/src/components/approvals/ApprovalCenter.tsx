import { useState, useEffect } from "react";
import { api } from "../../services/api";
import type { ApprovalRequest } from "../../types";
import { Button } from "../ui/Button";

export function ApprovalCenter() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadApprovals();
    // Refresh every 10 seconds
    const interval = setInterval(loadApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadApprovals = async () => {
    try {
      const data = await api.getPendingApprovals();
      setApprovals(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load approvals:", err);
      setError("Failed to load approval requests");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId: number) => {
    try {
      await api.approveRequest(approvalId);
      await loadApprovals();
    } catch (err) {
      console.error("Failed to approve:", err);
      alert("Failed to approve request");
    }
  };

  const handleReject = async (approvalId: number) => {
    const reason = prompt("Reason for rejection (optional):");
    try {
      await api.rejectRequest(approvalId, reason || undefined);
      await loadApprovals();
    } catch (err) {
      console.error("Failed to reject:", err);
      alert("Failed to reject request");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading approvals...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 text-destructive">
        {error}
      </div>
    );
  }

  if (approvals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <p className="text-lg text-muted-foreground mb-2">No Pending Approvals</p>
        <p className="text-sm text-muted-foreground">
          All approval requests have been processed.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Approval Center</h2>
        <p className="text-sm text-muted-foreground">
          {approvals.length} pending request{approvals.length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="grid gap-4">
        {approvals.map((approval) => (
          <ApprovalCard
            key={approval.id}
            approval={approval}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        ))}
      </div>
    </div>
  );
}

interface ApprovalCardProps {
  approval: ApprovalRequest;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
}

function ApprovalCard({ approval, onApprove, onReject }: ApprovalCardProps) {
  const [processing, setProcessing] = useState(false);

  const handleApprove = async () => {
    setProcessing(true);
    try {
      await onApprove(approval.id);
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    setProcessing(true);
    try {
      await onReject(approval.id);
    } finally {
      setProcessing(false);
    }
  };

  const timeAgo = getTimeAgo(new Date(approval.created_at));
  const expiresIn = getTimeUntil(new Date(approval.expires_at));

  return (
    <div className="border rounded-lg p-4 bg-card">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <span className="text-warning">⚠️</span>
            {approval.tool_name}
          </h3>
          <p className="text-sm text-muted-foreground">{timeAgo}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Expires {expiresIn}</p>
        </div>
      </div>

      <p className="text-sm mb-3">{approval.description}</p>

      <div className="bg-muted p-3 rounded mb-4">
        <p className="text-xs font-mono text-muted-foreground mb-1">Arguments:</p>
        <pre className="text-xs font-mono whitespace-pre-wrap break-all">
          {JSON.stringify(approval.tool_arguments, null, 2)}
        </pre>
      </div>

      {approval.step_index !== undefined && (
        <p className="text-xs text-muted-foreground mb-3">
          Part of execution plan (Step {approval.step_index + 1})
        </p>
      )}

      <div className="flex gap-2">
        <Button
          onClick={handleApprove}
          disabled={processing}
          className="flex-1"
        >
          {processing ? "Processing..." : "Approve & Execute"}
        </Button>
        <Button
          variant="outline"
          onClick={handleReject}
          disabled={processing}
          className="flex-1"
        >
          Reject
        </Button>
      </div>
    </div>
  );
}

function getTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds} second${seconds !== 1 ? "s" : ""} ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days !== 1 ? "s" : ""} ago`;
}

function getTimeUntil(date: Date): string {
  const seconds = Math.floor((date.getTime() - Date.now()) / 1000);

  if (seconds < 0) return "expired";
  if (seconds < 60) return `in ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `in ${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `in ${hours}h`;
}
