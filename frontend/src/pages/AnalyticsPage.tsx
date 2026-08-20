import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuthStore } from "../stores/authStore";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { cn } from "../lib/cn";

interface DashboardSummary {
  total_agents: number;
  total_conversations: number;
  total_messages: number;
  active_users_today: number;
  pending_approvals: number;
  meetings_this_week: number;
  interviews_this_week: number;
  security_alerts_24h: number;
}

interface DailyActivity {
  date: string;
  event_count: number;
  unique_users: number;
}

interface ToolUsage {
  tool_name: string;
  execution_count: number;
  success_count: number;
  success_rate: number;
}

interface SecurityAlert {
  id: number;
  event_type: string;
  threat_level: string;
  description?: string;
  ip_address?: string;
  user_id?: number;
  created_at: string;
}

type TabType = "overview" | "activity" | "tools" | "security";

export function AnalyticsPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [dailyActivity, setDailyActivity] = useState<DailyActivity[]>([]);
  const [toolUsage, setToolUsage] = useState<ToolUsage[]>([]);
  const [securityAlerts, setSecurityAlerts] = useState<SecurityAlert[]>([]);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (activeTab === "overview") {
        const [summaryData, activityData] = await Promise.all([
          api.getDashboardSummary(),
          api.getDailyActivity(7),
        ]);
        setSummary(summaryData);
        setDailyActivity(activityData);
      } else if (activeTab === "activity") {
        const activityData = await api.getDailyActivity(30);
        setDailyActivity(activityData);
      } else if (activeTab === "tools") {
        const toolData = await api.getToolUsageStats(30);
        setToolUsage(toolData);
      } else if (activeTab === "security") {
        const alertsData = await api.getSecurityAlerts({
          hours: 24,
          limit: 50,
        });
        setSecurityAlerts(alertsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "critical":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
      case "high":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400";
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      case "low":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300";
    }
  };

  const formatEventType = (type: string) => {
    return type
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "activity", label: "Activity" },
    { id: "tools", label: "Tool Usage" },
    { id: "security", label: "Security" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/dashboard")}>
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back
            </Button>
            <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.name} ({user?.role})
            </span>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="border-b mb-6">
          <nav className="flex gap-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "pb-3 px-1 text-sm font-medium border-b-2 transition-colors",
                  activeTab === tab.id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === "overview" && summary && (
              <div className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    title="Total Agents"
                    value={summary.total_agents}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                      </svg>
                    }
                    color="purple"
                  />
                  <StatCard
                    title="Total Conversations"
                    value={summary.total_conversations}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                    }
                    color="blue"
                  />
                  <StatCard
                    title="Active Users Today"
                    value={summary.active_users_today}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                      </svg>
                    }
                    color="green"
                  />
                  <StatCard
                    title="Security Alerts (24h)"
                    value={summary.security_alerts_24h}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                      </svg>
                    }
                    color={summary.security_alerts_24h > 0 ? "red" : "slate"}
                  />
                </div>

                {/* Second Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    title="Pending Approvals"
                    value={summary.pending_approvals}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    }
                    color="amber"
                  />
                  <StatCard
                    title="Meetings This Week"
                    value={summary.meetings_this_week}
                    icon={
                      <svg
                        className="w-5 h-5"
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
                    }
                    color="cyan"
                  />
                  <StatCard
                    title="Interviews This Week"
                    value={summary.interviews_this_week}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                      </svg>
                    }
                    color="indigo"
                  />
                  <StatCard
                    title="Total Messages"
                    value={summary.total_messages}
                    icon={
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                      </svg>
                    }
                    color="rose"
                  />
                </div>

                {/* Activity Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Activity (Last 7 Days)</CardTitle>
                    <CardDescription>
                      Daily event counts and unique users
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {dailyActivity.length > 0 ? (
                      <div className="h-64">
                        <SimpleBarChart data={dailyActivity} />
                      </div>
                    ) : (
                      <div className="h-64 flex items-center justify-center text-muted-foreground">
                        No activity data available
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Activity Tab */}
            {activeTab === "activity" && (
              <Card>
                <CardHeader>
                  <CardTitle>Daily Activity (Last 30 Days)</CardTitle>
                  <CardDescription>
                    Event counts and unique users by day
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {dailyActivity.length > 0 ? (
                    <div className="space-y-2">
                      {dailyActivity.map((day) => (
                        <div
                          key={day.date}
                          className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
                        >
                          <span className="font-medium">{day.date}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-muted-foreground">
                              {day.event_count} events
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {day.unique_users} users
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-muted-foreground">
                      No activity data available
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tools Tab */}
            {activeTab === "tools" && (
              <Card>
                <CardHeader>
                  <CardTitle>Tool Usage Statistics</CardTitle>
                  <CardDescription>
                    Tool execution counts and success rates over the last 30
                    days
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {toolUsage.length > 0 ? (
                    <div className="space-y-4">
                      {toolUsage.map((tool) => (
                        <div
                          key={tool.tool_name}
                          className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{tool.tool_name}</span>
                            <Badge
                              className={cn(
                                tool.success_rate >= 0.9
                                  ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                  : tool.success_rate >= 0.7
                                  ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                                  : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                              )}
                            >
                              {Math.round(tool.success_rate * 100)}% success
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>{tool.execution_count} executions</span>
                            <span>{tool.success_count} successful</span>
                          </div>
                          {/* Progress bar */}
                          <div className="mt-2 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                tool.success_rate >= 0.9
                                  ? "bg-green-500"
                                  : tool.success_rate >= 0.7
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              )}
                              style={{ width: `${tool.success_rate * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-muted-foreground">
                      No tool usage data available
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Security Tab */}
            {activeTab === "security" && (
              <Card>
                <CardHeader>
                  <CardTitle>Security Alerts (Last 24 Hours)</CardTitle>
                  <CardDescription>
                    Recent security events and potential threats
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {securityAlerts.length > 0 ? (
                    <div className="space-y-3">
                      {securityAlerts.map((alert) => (
                        <div
                          key={alert.id}
                          className="p-4 rounded-lg border bg-white dark:bg-slate-800"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium">
                                  {formatEventType(alert.event_type)}
                                </span>
                                <Badge
                                  className={getThreatLevelColor(
                                    alert.threat_level
                                  )}
                                >
                                  {alert.threat_level}
                                </Badge>
                              </div>
                              {alert.description && (
                                <p className="text-sm text-muted-foreground">
                                  {alert.description}
                                </p>
                              )}
                              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                {alert.ip_address && (
                                  <span>IP: {alert.ip_address}</span>
                                )}
                                <span>
                                  {new Date(alert.created_at).toLocaleString()}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-muted-foreground">
                      No security alerts in the last 24 hours
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}
      </main>
    </div>
  );
}

// Simple stat card component
function StatCard({
  title,
  value,
  icon,
  color = "slate",
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}) {
  const colorClasses: Record<string, string> = {
    purple: "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
    blue: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    green: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
    red: "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400",
    amber: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
    cyan: "bg-cyan-100 text-cyan-600 dark:bg-cyan-900/30 dark:text-cyan-400",
    indigo: "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400",
    rose: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400",
    slate: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400",
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", colorClasses[color])}>
            {icon}
          </div>
          <div>
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-sm text-muted-foreground">{title}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple bar chart component
function SimpleBarChart({ data }: { data: DailyActivity[] }) {
  const maxEvents = Math.max(...data.map((d) => d.event_count), 1);
  const maxUsers = Math.max(...data.map((d) => d.unique_users), 1);

  return (
    <div className="flex items-end justify-between h-full gap-2 px-4">
      {data.map((day) => {
        const eventHeight = (day.event_count / maxEvents) * 100;
        const userHeight = (day.unique_users / maxUsers) * 100;

        return (
          <div
            key={day.date}
            className="flex-1 flex flex-col items-center gap-2"
          >
            <div className="flex items-end gap-1 h-48">
              <div
                className="w-4 bg-purple-500 rounded-t transition-all"
                style={{ height: `${eventHeight}%` }}
                title={`${day.event_count} events`}
              />
              <div
                className="w-4 bg-blue-500 rounded-t transition-all"
                style={{ height: `${userHeight}%` }}
                title={`${day.unique_users} users`}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {new Date(day.date).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })}
            </span>
          </div>
        );
      })}
    </div>
  );
}
