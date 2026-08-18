import { Link } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { Button } from "../components/ui/Button";
import { DelegationDashboard } from "../components/delegations";

export function DelegationsPage() {
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-bold">AI Workforce Platform</h1>
            <nav className="flex gap-4">
              <Link
                to="/"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Dashboard
              </Link>
              <Link
                to="/chat"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Chat
              </Link>
              <Link
                to="/delegations"
                className="text-sm font-medium text-foreground"
              >
                Delegations
              </Link>
              <Link
                to="/approvals"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Approvals
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.name} ({user?.role})
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <DelegationDashboard />
      </main>
    </div>
  );
}
