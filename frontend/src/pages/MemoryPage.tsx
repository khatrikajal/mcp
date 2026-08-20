import { useState, useEffect } from "react";
import { MemoryViewer } from "../components/memory";
import { api } from "../services/api";
import type { Agent } from "../types";

export function MemoryPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agentsData = await api.getAgents();
        setAgents(agentsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load agents");
      } finally {
        setIsLoading(false);
      }
    };

    loadAgents();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="p-6 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 max-w-md text-center">
          <h2 className="text-lg font-semibold mb-2">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Navigation */}
      <nav className="bg-white dark:bg-slate-800 border-b dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-8">
              <a href="/" className="flex items-center gap-2">
                <span className="text-2xl">brain</span>
                <span className="font-bold text-slate-900 dark:text-white">
                  AI Workforce
                </span>
              </a>
              <div className="hidden md:flex items-center gap-4">
                <NavLink href="/">Dashboard</NavLink>
                <NavLink href="/chat">Chat</NavLink>
                <NavLink href="/delegations">Delegations</NavLink>
                <NavLink href="/interviews">Interviews</NavLink>
                <NavLink href="/memory" active>Memory</NavLink>
                <NavLink href="/approvals">Approvals</NavLink>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <MemoryViewer agents={agents} />
      </main>
    </div>
  );
}

function NavLink({
  href,
  children,
  active = false,
}: {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}) {
  return (
    <a
      href={href}
      className={`text-sm font-medium transition-colors ${
        active
          ? "text-purple-600 dark:text-purple-400"
          : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
      }`}
    >
      {children}
    </a>
  );
}
