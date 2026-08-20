import { useState } from "react";
import { api } from "../../services/api";
import type { MemorySearchResult, MemoryType } from "../../types";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { MemoryCard } from "./MemoryCard";

interface MemorySearchProps {
  agentId: number;
}

export function MemorySearch({ agentId }: MemorySearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [topK, setTopK] = useState(10);
  const [threshold, setThreshold] = useState(0.3);
  const [selectedTypes, setSelectedTypes] = useState<MemoryType[]>([]);

  const memoryTypes: MemoryType[] = [
    "preference",
    "fact",
    "interaction",
    "summary",
    "meeting",
    "email",
    "context",
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    setHasSearched(true);

    try {
      const searchResults = await api.searchMemories({
        query: query.trim(),
        agent_id: agentId,
        memory_types: selectedTypes.length > 0 ? selectedTypes : undefined,
        top_k: topK,
        threshold,
      });
      setResults(searchResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const toggleType = (type: MemoryType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleDelete = async (memoryId: number) => {
    try {
      await api.deleteMemory(memoryId);
      setResults((prev) => prev.filter((r) => r.memory.id !== memoryId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete memory");
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="space-y-4">
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              placeholder="Search memories semantically... (e.g., 'meetings about budget')"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
            />
          </div>
          <Button onClick={handleSearch} disabled={isSearching || !query.trim()}>
            {isSearching ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search
              </>
            )}
          </Button>
        </div>

        {/* Filters */}
        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-2">
              Memory Types
            </label>
            <div className="flex flex-wrap gap-2">
              {memoryTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => toggleType(type)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    selectedTypes.includes(type)
                      ? "bg-purple-600 text-white"
                      : "bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 hover:border-purple-500"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-2">
                Results Limit: {topK}
              </label>
              <input
                type="range"
                min="1"
                max="50"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-2">
                Similarity Threshold: {Math.round(threshold * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={threshold * 100}
                onChange={(e) => setThreshold(Number(e.target.value) / 100)}
                className="w-full accent-purple-600"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Results */}
      {hasSearched && (
        <div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-4">
            {results.length === 0
              ? "No matching memories found"
              : `Found ${results.length} matching ${results.length === 1 ? "memory" : "memories"}`}
          </h3>

          {results.length > 0 && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {results.map((result) => (
                <MemoryCard
                  key={result.memory.id}
                  memory={result.memory}
                  similarity={result.similarity}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!hasSearched && (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            Semantic Memory Search
          </h3>
          <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            Search through agent memories using natural language. The search uses
            vector embeddings to find semantically similar content, not just
            keyword matches.
          </p>
        </div>
      )}
    </div>
  );
}
