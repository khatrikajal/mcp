import { useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import type { ConversationSummary } from "../../types";
import { Badge } from "../ui/Badge";
import { cn } from "../../lib/cn";

interface SummariesPanelProps {
  summaries: ConversationSummary[];
}

export function SummariesPanel({ summaries }: SummariesPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (summaries.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
          <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
          No conversation summaries
        </h3>
        <p className="text-slate-500 dark:text-slate-400">
          Summaries are automatically generated for older conversations
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {summaries.map((summary) => {
        const isExpanded = expandedId === summary.id;

        return (
          <div
            key={summary.id}
            className={cn(
              "rounded-xl border bg-white dark:bg-slate-800 transition-all",
              isExpanded && "ring-2 ring-purple-500"
            )}
          >
            {/* Header */}
            <div
              className="p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50"
              onClick={() => setExpandedId(isExpanded ? null : summary.id)}
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="info" size="sm">
                      {summary.message_count} messages
                    </Badge>
                    {summary.time_range_start && summary.time_range_end && (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {format(new Date(summary.time_range_start), "MMM d")} - {format(new Date(summary.time_range_end), "MMM d, yyyy")}
                      </span>
                    )}
                  </div>
                  <p className={cn(
                    "text-slate-600 dark:text-slate-300",
                    !isExpanded && "line-clamp-2"
                  )}>
                    {summary.summary}
                  </p>
                </div>

                <button className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <svg
                    className={cn(
                      "w-5 h-5 transition-transform",
                      isExpanded && "transform rotate-180"
                    )}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="p-4 pt-0 border-t dark:border-slate-700 space-y-4">
                {/* Topics */}
                {summary.key_topics.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Key Topics
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {summary.key_topics.map((topic, idx) => (
                        <Badge key={idx} variant="default" size="sm">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Entities */}
                {summary.key_entities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Key Entities
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {summary.key_entities.map((entity, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                        >
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Items */}
                {summary.action_items.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Action Items
                    </h4>
                    <ul className="space-y-1">
                      {summary.action_items.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                          <svg className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Decisions */}
                {summary.decisions.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Decisions Made
                    </h4>
                    <ul className="space-y-1">
                      {summary.decisions.map((decision, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                          <svg className="w-4 h-4 mt-0.5 text-purple-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          {decision}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Metadata */}
                <div className="pt-3 border-t dark:border-slate-700 text-xs text-slate-500 dark:text-slate-400">
                  <span>Conversation #{summary.conversation_id}</span>
                  <span className="mx-2">|</span>
                  <span>Generated {formatDistanceToNow(new Date(summary.created_at), { addSuffix: true })}</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
