import { useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import type { AgentMemory } from "../../types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";

interface MemoryCardProps {
  memory: AgentMemory;
  onDelete: (id: number) => void;
  similarity?: number;
}

export function MemoryCard({ memory, onDelete, similarity }: MemoryCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const typeColors: Record<string, { bg: string; text: string }> = {
    preference: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-600 dark:text-blue-400" },
    fact: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-600 dark:text-green-400" },
    interaction: { bg: "bg-purple-100 dark:bg-purple-900/30", text: "text-purple-600 dark:text-purple-400" },
    summary: { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-600 dark:text-amber-400" },
    meeting: { bg: "bg-cyan-100 dark:bg-cyan-900/30", text: "text-cyan-600 dark:text-cyan-400" },
    email: { bg: "bg-rose-100 dark:bg-rose-900/30", text: "text-rose-600 dark:text-rose-400" },
    context: { bg: "bg-slate-100 dark:bg-slate-700", text: "text-slate-600 dark:text-slate-400" },
  };

  const colors = typeColors[memory.memory_type] || typeColors.context;
  const importancePercent = Math.round(memory.importance * 100);

  return (
    <div
      className={cn(
        "rounded-xl border bg-white dark:bg-slate-800 transition-all hover:shadow-md",
        expanded && "ring-2 ring-purple-500"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b dark:border-slate-700">
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn(colors.bg, colors.text)} size="sm">
                {memory.memory_type}
              </Badge>
              {similarity !== undefined && (
                <Badge variant="info" size="sm">
                  {Math.round(similarity * 100)}% match
                </Badge>
              )}
            </div>
            <h3 className="font-medium text-slate-900 dark:text-white truncate">
              {memory.key}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-right">
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Importance
              </div>
              <div className={cn(
                "text-sm font-medium",
                importancePercent >= 70 ? "text-green-600 dark:text-green-400" :
                importancePercent >= 40 ? "text-amber-600 dark:text-amber-400" :
                "text-slate-500 dark:text-slate-400"
              )}>
                {importancePercent}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <p className={cn(
          "text-sm text-slate-600 dark:text-slate-300",
          !expanded && "line-clamp-3"
        )}>
          {memory.summary || memory.content}
        </p>

        {memory.content.length > 200 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-sm text-purple-600 dark:text-purple-400 hover:underline"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}

        {/* Metadata */}
        <div className="mt-4 pt-4 border-t dark:border-slate-700 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500 dark:text-slate-400">
          {memory.source && (
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <span>Source: {memory.source}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span>Accessed {memory.access_count} times</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Created {formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })}</span>
          </div>
          {memory.expires_at && (
            <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>Expires {format(new Date(memory.expires_at), "MMM d, yyyy")}</span>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 pt-0 flex justify-end gap-2">
        {confirmDelete ? (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setConfirmDelete(false)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onDelete(memory.id)}
            >
              Confirm Delete
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setConfirmDelete(true)}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
        )}
      </div>
    </div>
  );
}
