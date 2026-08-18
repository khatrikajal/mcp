import { useState, useEffect } from "react";
import { api } from "../../services/api";
import type { DelegationReport as DelegationReportType } from "../../types";
import { Button } from "../ui/Button";

interface DelegationReportProps {
  delegationId: number;
  onClose: () => void;
  onSendReport?: () => void;
}

export function DelegationReport({
  delegationId,
  onClose,
  onSendReport,
}: DelegationReportProps) {
  const [report, setReport] = useState<DelegationReportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadReport();
  }, [delegationId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await api.getDelegationReport(delegationId);
      setReport(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load report:", err);
      setError("Failed to load meeting report");
    } finally {
      setLoading(false);
    }
  };

  const handleSendReport = async () => {
    try {
      setSending(true);
      await api.sendDelegationReport(delegationId);
      alert("Report sent successfully!");
      onSendReport?.();
    } catch (err) {
      console.error("Failed to send report:", err);
      alert("Failed to send report");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-card rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <p className="text-center text-muted-foreground">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-card rounded-lg p-6 max-w-3xl w-full mx-4">
          <p className="text-destructive mb-4">{error || "Report not found"}</p>
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    );
  }

  const startTime = new Date(report.meeting_start_time);
  const endTime = new Date(report.meeting_end_time);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-lg max-w-3xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold">{report.meeting_title}</h2>
              <p className="text-sm text-muted-foreground">
                {formatDate(startTime)} • {formatTime(startTime)} - {formatTime(endTime)}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>

          {/* Attendees */}
          {report.meeting_attendees.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {report.meeting_attendees.map((attendee, idx) => (
                <span
                  key={idx}
                  className="text-xs bg-muted px-2 py-0.5 rounded"
                >
                  {attendee.name || attendee.email}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Executive Summary */}
          {report.report_summary && (
            <section>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <span className="text-lg">📋</span> Executive Summary
              </h3>
              <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
                {report.report_summary}
              </p>
            </section>
          )}

          {/* Action Items */}
          {report.action_items && report.action_items.length > 0 && (
            <section>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <span className="text-lg">✅</span> Action Items
              </h3>
              <ul className="space-y-2">
                {report.action_items.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm bg-muted/50 p-2 rounded"
                  >
                    <span className="text-muted-foreground">•</span>
                    <div>
                      <span className="font-medium">[{item.assignee}]</span>{" "}
                      {item.task}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Decisions */}
          {report.decisions && report.decisions.length > 0 && (
            <section>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <span className="text-lg">🎯</span> Decisions Made
              </h3>
              <ul className="space-y-2">
                {report.decisions.map((decision, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm bg-muted/50 p-2 rounded"
                  >
                    <span className="text-muted-foreground">•</span>
                    <span>{decision}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Full Report */}
          {report.report && (
            <section>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <span className="text-lg">📝</span> Full Report
              </h3>
              <div className="text-sm whitespace-pre-wrap bg-muted/50 p-3 rounded max-h-64 overflow-y-auto">
                {report.report}
              </div>
            </section>
          )}

          {/* Transcript Toggle */}
          {report.transcript && (
            <section>
              <button
                onClick={() => setShowTranscript(!showTranscript)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
              >
                <span>{showTranscript ? "▼" : "▶"}</span>
                <span className="text-lg">🎙️</span>
                {showTranscript ? "Hide Transcript" : "Show Transcript"}
              </button>
              {showTranscript && (
                <div className="mt-2 text-xs whitespace-pre-wrap bg-muted/50 p-3 rounded max-h-64 overflow-y-auto font-mono">
                  {report.transcript}
                </div>
              )}
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t flex justify-between items-center">
          <div>
            {report.report_sent ? (
              <span className="text-sm text-green-600">✓ Report sent</span>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={handleSendReport}
                disabled={sending}
              >
                {sending ? "Sending..." : "Send Report via Email"}
              </Button>
            )}
          </div>
          <Button size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}
