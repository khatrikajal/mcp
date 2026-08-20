import { useState, useEffect } from "react";
import { api } from "../../services/api";
import type {
  AgentMemory,
  UserPreference,
  ConversationSummary,
  MemoryStats,
  MemoryType,
  Agent,
} from "../../types";
import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";
import { MemoryCard } from "./MemoryCard";
import { MemorySearch } from "./MemorySearch";
import { PreferencesPanel } from "./PreferencesPanel";
import { SummariesPanel } from "./SummariesPanel";

type Tab = "memories" | "search" | "preferences" | "summaries";

interface MemoryViewerProps {
  agents: Agent[];
}

export function MemoryViewer({ agents }: MemoryViewerProps) {
  const [activeTab, setActiveTab] = useState<Tab>("memories");
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [memories, setMemories] = useState<AgentMemory[]>([]);
  const [preferences, setPreferences] = useState<UserPreference[]>([]);
  const [summaries, setSummaries] = useState<ConversationSummary[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [memoryTypeFilter, setMemoryTypeFilter] = useState<MemoryType | "all">("all");

  // Set initial agent
  useEffect(() => {
    if (agents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgentId]);

  // Load data when agent or tab changes
  useEffect(() => {
    if (!selectedAgentId) return;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        if (activeTab === "memories" || activeTab === "search") {
          const [memoriesData, statsData] = await Promise.all([
            api.getAgentMemories(selectedAgentId, {
              memory_type: memoryTypeFilter === "all" ? undefined : memoryTypeFilter,
              limit: 100,
            }),
            api.getMemoryStats(selectedAgentId),
          ]);
          setMemories(memoriesData);
          setStats(statsData);
        } else if (activeTab === "preferences") {
          const prefsData = await api.getPreferences();
          setPreferences(prefsData);
        } else if (activeTab === "summaries") {
          const summariesData = await api.getUserSummaries({ agent_id: selectedAgentId });
          setSummaries(summariesData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [selectedAgentId, activeTab, memoryTypeFilter]);

  const handleDeleteMemory = async (memoryId: number) => {
    try {
      await api.deleteMemory(memoryId);
      setMemories((prev) => prev.filter((m) => m.id !== memoryId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete memory");
    }
  };

  const handleDeletePreference = async (preferenceId: number) => {
    try {
      await api.deletePreference(preferenceId);
      setPreferences((prev) => prev.filter((p) => p.id !== preferenceId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete preference");
    }
  };

  const memoryTypes: MemoryType[] = [
    "preference",
    "fact",
    "interaction",
    "summary",
    "meeting",
    "email",
    "context",
  ];

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "memories", label: "Memories", icon: "brain" },
    { id: "search", label: "Search", icon: "search" },
    { id: "preferences", label: "Preferences", icon: "settings" },
    { id: "summaries", label: "Summaries", icon: "document" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Memory Management
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            View and manage agent memories, preferences, and conversation summaries
          </p>
        </div>

        {/* Agent Selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600 dark:text-slate-400">Agent:</label>
          <select
            value={selectedAgentId || ""}
            onChange={(e) => setSelectedAgentId(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm"
          >
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Memories"
            value={stats.total_memories}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
          />
          <StatCard
            label="Facts"
            value={stats.by_type?.fact || 0}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <StatCard
            label="Preferences"
            value={stats.by_type?.preference || 0}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
          <StatCard
            label="Avg Importance"
            value={`${(stats.average_importance * 100).toFixed(0)}%`}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
          />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "pb-3 px-1 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab.id
                  ? "border-purple-600 text-purple-600 dark:text-purple-400"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Tab Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
        </div>
      ) : (
        <>
          {activeTab === "memories" && (
            <div className="space-y-4">
              {/* Memory Type Filter */}
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant={memoryTypeFilter === "all" ? "default" : "outline"}
                  onClick={() => setMemoryTypeFilter("all")}
                >
                  All
                </Button>
                {memoryTypes.map((type) => (
                  <Button
                    key={type}
                    size="sm"
                    variant={memoryTypeFilter === type ? "default" : "outline"}
                    onClick={() => setMemoryTypeFilter(type)}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Button>
                ))}
              </div>

              {/* Memory List */}
              {memories.length === 0 ? (
                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                  No memories found for this agent
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {memories.map((memory) => (
                    <MemoryCard
                      key={memory.id}
                      memory={memory}
                      onDelete={handleDeleteMemory}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "search" && selectedAgentId && (
            <MemorySearch agentId={selectedAgentId} />
          )}

          {activeTab === "preferences" && (
            <PreferencesPanel
              preferences={preferences}
              onDelete={handleDeletePreference}
            />
          )}

          {activeTab === "summaries" && (
            <SummariesPanel summaries={summaries} />
          )}
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
}) {
  return (
    <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
          {icon}
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white">{value}</div>
          <div className="text-sm text-slate-500 dark:text-slate-400">{label}</div>
        </div>
      </div>
    </div>
  );
}
