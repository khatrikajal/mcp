import type { Agent } from "../../types";

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgentId: number | null;
  onSelectAgent: (agentId: number) => void;
}

export function AgentSelector({
  agents,
  selectedAgentId,
  onSelectAgent,
}: AgentSelectorProps) {
  return (
    <div className="border-b p-4 bg-background">
      <label htmlFor="agent-select" className="text-sm font-medium mb-2 block">
        Select Agent
      </label>
      <select
        id="agent-select"
        value={selectedAgentId || ""}
        onChange={(e) => onSelectAgent(Number(e.target.value))}
        className="w-full p-2 border rounded-md bg-background"
      >
        <option value="" disabled>
          Choose an agent...
        </option>
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
      {selectedAgentId && (
        <p className="text-sm text-muted-foreground mt-2">
          {agents.find((a) => a.id === selectedAgentId)?.description}
        </p>
      )}
    </div>
  );
}
