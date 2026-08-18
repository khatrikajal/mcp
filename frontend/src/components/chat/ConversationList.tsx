import type { Conversation } from "../../types";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onNewConversation: () => void;
}

export function ConversationList({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
}: ConversationListProps) {
  return (
    <div className="w-64 border-r bg-background flex flex-col">
      <div className="p-4 border-b">
        <Button onClick={onNewConversation} className="w-full">
          + New Chat
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {conversations.length === 0 ? (
          <div className="text-center text-muted-foreground text-sm p-4">
            No conversations yet
          </div>
        ) : (
          conversations.map((conversation) => (
            <Card
              key={conversation.id}
              className={`p-3 cursor-pointer hover:bg-accent transition-colors ${
                activeConversationId === conversation.id
                  ? "bg-accent border-primary"
                  : ""
              }`}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="font-medium truncate text-sm">
                {conversation.title || "Untitled Chat"}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {new Date(conversation.updated_at).toLocaleDateString()}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
