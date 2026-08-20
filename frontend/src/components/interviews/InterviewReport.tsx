import { useState, useEffect } from "react";
import { format } from "date-fns";
import { api } from "../../services/api";
import type { InterviewReport as InterviewReportType } from "../../types";
import { Modal, ModalHeader, ModalBody, ModalFooter } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { toast } from "../ui/Toast";
import { cn } from "../../lib/cn";
import { CandidateScorecard } from "./CandidateScorecard";

interface InterviewReportProps {
  interviewId: number;
  onClose: () => void;
}

type TabKey = "summary" | "scorecard" | "questions" | "full_report";

export function InterviewReport({ interviewId, onClose }: InterviewReportProps) {
  const [report, setReport] = useState<InterviewReportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("summary");
  const [sending, setSending] = useState(false);
  const [emailInput, setEmailInput] = useState("");

  useEffect(() => {
    loadReport();
  }, [interviewId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getInterviewReport(interviewId);
      setReport(data);
    } catch (err) {
      console.error("Failed to load report:", err);
      setError("Failed to load interview report");
    } finally {
      setLoading(false);
    }
  };

  const handleSendReport = async () => {
    if (!emailInput.trim()) {
      toast.error("Enter email address", "Please enter at least one recipient email");
      return;
    }

    const emails = emailInput.split(",").map((e) => e.trim()).filter(Boolean);
    if (emails.some((e) => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))) {
      toast.error("Invalid email", "Please check the email format");
      return;
    }

    try {
      setSending(true);
      await api.sendInterviewReport(interviewId, emails);
      toast.success("Report sent", `Sent to ${emails.length} recipient(s)`);
      setEmailInput("");
    } catch (err) {
      console.error("Failed to send report:", err);
      toast.error("Failed to send report", "Please try again");
    } finally {
      setSending(false);
    }
  };

  const recommendationConfig: Record<
    string,
    { label: string; color: string; bgColor: string }
  > = {
    strong_hire: {
      label: "Strong Hire",
      color: "text-emerald-700 dark:text-emerald-300",
      bgColor: "bg-emerald-100 dark:bg-emerald-900/30",
    },
    hire: {
      label: "Hire",
      color: "text-green-700 dark:text-green-300",
      bgColor: "bg-green-100 dark:bg-green-900/30",
    },
    maybe: {
      label: "Maybe",
      color: "text-amber-700 dark:text-amber-300",
      bgColor: "bg-amber-100 dark:bg-amber-900/30",
    },
    no_hire: {
      label: "No Hire",
      color: "text-orange-700 dark:text-orange-300",
      bgColor: "bg-orange-100 dark:bg-orange-900/30",
    },
    strong_no_hire: {
      label: "Strong No Hire",
      color: "text-red-700 dark:text-red-300",
      bgColor: "bg-red-100 dark:bg-red-900/30",
    },
  };

  const tabs: { key: TabKey; label: string; icon: string }[] = [
    { key: "summary", label: "Summary", icon: "📋" },
    { key: "scorecard", label: "Scorecard", icon: "📊" },
    { key: "questions", label: "Questions", icon: "❓" },
    { key: "full_report", label: "Full Report", icon: "📝" },
  ];

  if (loading) {
    return (
      <Modal open={true} onClose={onClose} size="xl">
        <ModalHeader onClose={onClose}>Interview Report</ModalHeader>
        <ModalBody>
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
          </div>
        </ModalBody>
      </Modal>
    );
  }

  if (error || !report) {
    return (
      <Modal open={true} onClose={onClose} size="lg">
        <ModalHeader onClose={onClose}>Interview Report</ModalHeader>
        <ModalBody>
          <div className="text-center py-16">
            <span className="text-4xl">⚠</span>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              {error || "Report not found"}
            </p>
            <Button onClick={loadReport} variant="outline" className="mt-4">
              Try Again
            </Button>
          </div>
        </ModalBody>
      </Modal>
    );
  }

  const recConfig = recommendationConfig[report.recommendation] || recommendationConfig.maybe;

  return (
    <Modal open={true} onClose={onClose} size="xl">
      <ModalHeader onClose={onClose}>
        <div className="flex items-center gap-3">
          <span>Interview Report</span>
          <span
            className={cn(
              "px-3 py-1 rounded-full text-sm font-medium",
              recConfig.bgColor,
              recConfig.color
            )}
          >
            {recConfig.label}
          </span>
        </div>
      </ModalHeader>

      {/* Report Header */}
      <div className="px-6 py-4 border-b dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {report.candidate_name}
            </h2>
            <p className="text-slate-600 dark:text-slate-400">{report.position_title}</p>
            {report.completed_at && (
              <p className="text-sm text-slate-500 mt-1">
                Completed {format(new Date(report.completed_at), "MMMM d, yyyy 'at' h:mm a")}
              </p>
            )}
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-slate-900 dark:text-white">
              {report.overall_score}%
            </div>
            <p className="text-sm text-slate-500">Overall Score</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-6 border-b dark:border-slate-700">
        <nav className="flex gap-1 -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "px-4 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
                activeTab === tab.key
                  ? "border-purple-500 text-purple-600 dark:text-purple-400"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900"
              )}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <ModalBody className="max-h-[60vh] overflow-y-auto">
        {/* Summary Tab */}
        {activeTab === "summary" && (
          <div className="space-y-6">
            {/* Report Summary */}
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border dark:border-slate-700">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Executive Summary
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                {report.report_summary || "No summary available."}
              </p>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800">
                <h3 className="font-semibold text-emerald-800 dark:text-emerald-300 mb-3 flex items-center gap-2">
                  <span>✓</span> Strengths
                </h3>
                <ul className="space-y-2">
                  {report.strengths.length > 0 ? (
                    report.strengths.map((strength, i) => (
                      <li key={i} className="text-sm text-emerald-700 dark:text-emerald-300">
                        • {strength}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-emerald-600 dark:text-emerald-400 italic">
                      No strengths identified
                    </li>
                  )}
                </ul>
              </div>

              <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                <h3 className="font-semibold text-amber-800 dark:text-amber-300 mb-3 flex items-center gap-2">
                  <span>⚠</span> Areas for Improvement
                </h3>
                <ul className="space-y-2">
                  {report.weaknesses.length > 0 ? (
                    report.weaknesses.map((weakness, i) => (
                      <li key={i} className="text-sm text-amber-700 dark:text-amber-300">
                        • {weakness}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-amber-600 dark:text-amber-400 italic">
                      No areas identified
                    </li>
                  )}
                </ul>
              </div>
            </div>

            {/* Competency Scores */}
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border dark:border-slate-700">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
                Competency Breakdown
              </h3>
              <div className="space-y-3">
                {Object.entries(report.competency_scores).map(([competency, score]) => (
                  <div key={competency} className="flex items-center gap-3">
                    <span className="text-sm text-slate-600 dark:text-slate-400 w-32 capitalize">
                      {competency.replace("_", " ")}
                    </span>
                    <div className="flex-1 h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          score >= 8
                            ? "bg-emerald-500"
                            : score >= 6
                            ? "bg-blue-500"
                            : score >= 4
                            ? "bg-amber-500"
                            : "bg-red-500"
                        )}
                        style={{ width: `${score * 10}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-900 dark:text-white w-12 text-right">
                      {score}/10
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Scorecard Tab */}
        {activeTab === "scorecard" && (
          <CandidateScorecard
            overallScore={report.overall_score}
            recommendation={report.recommendation}
            competencyScores={report.competency_scores}
            questions={report.questions}
          />
        )}

        {/* Questions Tab */}
        {activeTab === "questions" && (
          <div className="space-y-4">
            {report.questions.map((question) => (
              <div
                key={question.id}
                className="bg-white dark:bg-slate-800 rounded-lg border dark:border-slate-700 overflow-hidden"
              >
                <div className="p-4 border-b dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <span className="text-sm text-slate-500">
                        Question {question.question_number}
                      </span>
                      <p className="font-medium text-slate-900 dark:text-white mt-1">
                        {question.question_text}
                      </p>
                    </div>
                    {question.score !== null && question.score !== undefined && (
                      <div
                        className={cn(
                          "px-3 py-1 rounded-full text-sm font-medium",
                          question.score >= 8
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                            : question.score >= 6
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                            : question.score >= 4
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                            : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                        )}
                      >
                        {question.score}/10
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="default" size="sm">
                      {question.question_type}
                    </Badge>
                    {question.competency && (
                      <Badge variant="info" size="sm">
                        {question.competency.replace("_", " ")}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="p-4">
                  <p className="text-sm text-slate-500 mb-1">Candidate's Answer:</p>
                  <p className="text-slate-700 dark:text-slate-300">
                    {question.candidate_answer || "No answer recorded"}
                  </p>
                  {question.feedback && (
                    <div className="mt-3 pt-3 border-t dark:border-slate-700">
                      <p className="text-sm text-slate-500 mb-1">AI Feedback:</p>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {question.feedback}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Full Report Tab */}
        {activeTab === "full_report" && (
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <div
              className="bg-white dark:bg-slate-800 rounded-lg p-6 border dark:border-slate-700"
              dangerouslySetInnerHTML={{
                __html: report.report
                  .replace(/\n/g, "<br>")
                  .replace(/#{3} (.*)/g, "<h3>$1</h3>")
                  .replace(/#{2} (.*)/g, "<h2>$1</h2>")
                  .replace(/#{1} (.*)/g, "<h1>$1</h1>")
                  .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                  .replace(/\*(.*?)\*/g, "<em>$1</em>"),
              }}
            />
          </div>
        )}
      </ModalBody>

      <ModalFooter>
        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <div className="flex-1 flex gap-2">
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              placeholder="Enter email(s) to send report..."
              className="flex-1 px-3 py-2 border rounded-lg dark:border-slate-700 dark:bg-slate-800 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none text-sm"
            />
            <Button onClick={handleSendReport} disabled={sending} variant="outline">
              {sending ? "Sending..." : "Send"}
            </Button>
          </div>
          <Button onClick={onClose}>Close</Button>
        </div>
      </ModalFooter>
    </Modal>
  );
}
