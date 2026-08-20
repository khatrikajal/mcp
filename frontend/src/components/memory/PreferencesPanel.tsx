import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import type { UserPreference, PreferenceCategory } from "../../types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";

interface PreferencesPanelProps {
  preferences: UserPreference[];
  onDelete: (id: number) => void;
}

export function PreferencesPanel({ preferences, onDelete }: PreferencesPanelProps) {
  const [categoryFilter, setCategoryFilter] = useState<PreferenceCategory | "all">("all");
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  const categories: PreferenceCategory[] = [
    "scheduling",
    "communication",
    "workflow",
    "personal",
    "tool",
  ];

  const categoryConfig: Record<PreferenceCategory, { icon: string; color: string }> = {
    scheduling: { icon: "calendar", color: "text-blue-600 dark:text-blue-400" },
    communication: { icon: "chat", color: "text-green-600 dark:text-green-400" },
    workflow: { icon: "workflow", color: "text-purple-600 dark:text-purple-400" },
    personal: { icon: "user", color: "text-amber-600 dark:text-amber-400" },
    tool: { icon: "tool", color: "text-cyan-600 dark:text-cyan-400" },
  };

  const filteredPreferences = categoryFilter === "all"
    ? preferences
    : preferences.filter((p) => p.category === categoryFilter);

  const groupedPreferences = filteredPreferences.reduce((acc, pref) => {
    if (!acc[pref.category]) {
      acc[pref.category] = [];
    }
    acc[pref.category].push(pref);
    return acc;
  }, {} as Record<string, UserPreference[]>);

  const handleDelete = (id: number) => {
    onDelete(id);
    setConfirmDeleteId(null);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600 dark:text-green-400";
    if (confidence >= 0.5) return "text-amber-600 dark:text-amber-400";
    return "text-slate-500 dark:text-slate-400";
  };

  const getSourceBadge = (sourceType: string | undefined) => {
    switch (sourceType) {
      case "explicit":
        return <Badge variant="success" size="sm">Explicit</Badge>;
      case "correction":
        return <Badge variant="warning" size="sm">Correction</Badge>;
      case "pattern":
        return <Badge variant="info" size="sm">Pattern</Badge>;
      case "llm_inferred":
        return <Badge variant="default" size="sm">Inferred</Badge>;
      default:
        return <Badge variant="default" size="sm">Auto</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={categoryFilter === "all" ? "default" : "outline"}
          onClick={() => setCategoryFilter("all")}
        >
          All
        </Button>
        {categories.map((category) => (
          <Button
            key={category}
            size="sm"
            variant={categoryFilter === category ? "default" : "outline"}
            onClick={() => setCategoryFilter(category)}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </Button>
        ))}
      </div>

      {/* Preferences List */}
      {filteredPreferences.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            No preferences found
          </h3>
          <p className="text-slate-500 dark:text-slate-400">
            Preferences are automatically learned from your interactions
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPreferences).map(([category, prefs]) => (
            <div key={category}>
              <h3 className={cn(
                "text-lg font-medium mb-4 capitalize",
                categoryConfig[category as PreferenceCategory]?.color || "text-slate-900 dark:text-white"
              )}>
                {category} Preferences
              </h3>
              <div className="space-y-3">
                {prefs.map((pref) => (
                  <div
                    key={pref.id}
                    className="p-4 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-slate-900 dark:text-white">
                            {pref.preference_key.replace(/_/g, " ")}
                          </span>
                          {getSourceBadge(pref.source_type)}
                        </div>
                        <p className="text-slate-600 dark:text-slate-300">
                          {pref.preference_value}
                        </p>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Confidence Indicator */}
                        <div className="text-right">
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
                            Confidence
                          </div>
                          <div className={cn("font-medium", getConfidenceColor(pref.confidence))}>
                            {Math.round(pref.confidence * 100)}%
                          </div>
                        </div>

                        {/* Delete Button */}
                        {confirmDeleteId === pref.id ? (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setConfirmDeleteId(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDelete(pref.id)}
                            >
                              Delete
                            </Button>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setConfirmDeleteId(pref.id)}
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="mt-3 pt-3 border-t dark:border-slate-700 flex gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span>
                        Confirmed {pref.times_confirmed} time{pref.times_confirmed !== 1 ? "s" : ""}
                      </span>
                      {pref.times_contradicted > 0 && (
                        <span className="text-amber-600 dark:text-amber-400">
                          Contradicted {pref.times_contradicted} time{pref.times_contradicted !== 1 ? "s" : ""}
                        </span>
                      )}
                      <span>
                        Updated {formatDistanceToNow(new Date(pref.updated_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
