import { useAuthStore } from "../stores/authStore";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";

export function DashboardPage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">AI Workforce Platform</h1>
          <div className="flex items-center gap-4">
            <Button onClick={() => navigate("/chat")}>
              Start Chat
            </Button>
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
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Agents</CardTitle>
              <CardDescription>Manage your AI assistants</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Create and configure specialized AI agents for different tasks
              </p>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => navigate("/chat")}>
            <CardHeader>
              <CardTitle>Conversations</CardTitle>
              <CardDescription>Chat history</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                View and continue your conversations with AI agents
              </p>
              <Button className="mt-4 w-full" variant="outline">
                Go to Chat →
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Meeting Delegation</CardTitle>
              <CardDescription>AI-powered meeting assistant</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Let AI join and summarize meetings automatically
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Interview Automation</CardTitle>
              <CardDescription>AI interview conductor</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Automate candidate interviews with AI-powered analysis
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Planning Workflows</CardTitle>
              <CardDescription>Multi-step task execution</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Create and visualize complex multi-step workflows
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Approvals</CardTitle>
              <CardDescription>Human-in-the-loop gates</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Review and approve sensitive AI actions
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Welcome, {user?.name}!</CardTitle>
              <CardDescription>Getting started with the AI Workforce Platform</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Your Account Details:</h3>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>Email: {user?.email}</li>
                  <li>Role: {user?.role}</li>
                  <li>Organization ID: {user?.organization_id}</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Next Steps:</h3>
                <ol className="text-sm space-y-1 list-decimal list-inside text-muted-foreground">
                  <li>Create your first AI agent</li>
                  <li>Configure tool permissions</li>
                  <li>Start a conversation</li>
                  <li>Explore meeting delegation and interview automation</li>
                </ol>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
