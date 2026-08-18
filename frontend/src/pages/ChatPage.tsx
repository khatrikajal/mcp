import { useState, useEffect } from "react";
import { useAuthStore } from "../stores/authStore";
import { api } from "../services/api";
import type { Agent, Conversation, Message } from "../types";
import { ConversationList } from "../components/chat/ConversationList";
import { MessageList } from "../components/chat/MessageList";
import { MessageInput } from "../components/chat/MessageInput";
import { AgentSelector } from "../components/agents/AgentSelector";
import { Button } from "../components/ui/Button";

export function ChatPage() {
  const { user, logout } = useAuthStore();

  // State
  const [agents, setAgents] = useState<Agent[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
    loadConversations();
  }, []);

  // Load messages when conversation changes
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
    }
  }, [activeConversationId]);

  const loadAgents = async () => {
    try {
      const agentList = await api.getAgents();
      setAgents(agentList);
      // Auto-select first agent if available
      if (agentList.length > 0 && !selectedAgentId) {
        setSelectedAgentId(agentList[0].id);
      }
    } catch (err) {
      console.error("Failed to load agents:", err);
      setError("Failed to load agents");
    }
  };

  const loadConversations = async () => {
    try {
      const convList = await api.getConversations();
      setConversations(convList);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const loadMessages = async (conversationId: number) => {
    try {
      const msgList = await api.getMessages(String(conversationId));
      setMessages(msgList);
    } catch (err) {
      console.error("Failed to load messages:", err);
      setError("Failed to load messages");
    }
  };

  const handleNewConversation = async () => {
    if (!selectedAgentId) {
      setError("Please select an agent first");
      return;
    }

    try {
      const newConv = await api.createConversation({
        agent_id: selectedAgentId,
      });
      setConversations([newConv, ...conversations]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error("Failed to create conversation:", err);
      setError("Failed to create conversation");
    }
  };

  const handleSelectConversation = (conversationId: number) => {
    setActiveConversationId(conversationId);
    setError(null);
  };

  const handleSendMessage = async (content: string) => {
    if (!activeConversationId) {
      // Create new conversation if none selected
      await handleNewConversation();
      // Wait a bit for the conversation to be created
      setTimeout(() => {
        sendMessageToConversation(content);
      }, 100);
      return;
    }

    await sendMessageToConversation(content);
  };

  const sendMessageToConversation = async (content: string) => {
    if (!activeConversationId) return;

    setLoading(true);
    setError(null);

    try {
      // Optimistically add user message
      const tempUserMessage: Message = {
        id: Date.now(),
        conversation_id: activeConversationId,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      setMessages([...messages, tempUserMessage]);

      // Send message and get AI response
      await api.sendMessage(String(activeConversationId), content);

      // Refresh messages to get both user and AI messages
      await loadMessages(activeConversationId);

      // Refresh conversation list (updated timestamp)
      await loadConversations();
    } catch (err: any) {
      console.error("Failed to send message:", err);
      setError(err.response?.data?.detail || "Failed to send message");
      // Reload messages to remove optimistic update
      if (activeConversationId) {
        await loadMessages(activeConversationId);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">AI Workforce Platform - Chat</h1>
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

      {/* Main Chat Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversation List Sidebar */}
        <ConversationList
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Agent Selector */}
          <AgentSelector
            agents={agents}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
          />

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive border-b">
              {error}
            </div>
          )}

          {/* Messages */}
          {activeConversationId ? (
            <>
              <MessageList messages={messages} />
              <MessageInput onSend={handleSendMessage} disabled={loading} />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <p className="text-lg mb-2">Welcome to AI Workforce Platform</p>
                <p className="text-sm">Select an agent and start a new conversation</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
