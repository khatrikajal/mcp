import { InterviewDashboard } from "../components/interviews";

export function InterviewsPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Navigation */}
      <nav className="bg-white dark:bg-slate-800 border-b dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-8">
              <a href="/" className="flex items-center gap-2">
                <span className="text-2xl">🤖</span>
                <span className="font-bold text-slate-900 dark:text-white">
                  AI Workforce
                </span>
              </a>
              <div className="hidden md:flex items-center gap-4">
                <NavLink href="/">Dashboard</NavLink>
                <NavLink href="/chat">Chat</NavLink>
                <NavLink href="/delegations">Delegations</NavLink>
                <NavLink href="/interviews" active>Interviews</NavLink>
                <NavLink href="/approvals">Approvals</NavLink>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <InterviewDashboard />
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
