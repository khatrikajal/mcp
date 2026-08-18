import { useAuthStore } from "../stores/authStore";
import { Button } from "../components/ui/Button";
import { ApprovalCenter } from "../components/approvals/ApprovalCenter";

export function ApprovalsPage() {
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">AI Workforce Platform - Approvals</h1>
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

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <ApprovalCenter />
      </main>
    </div>
  );
}
