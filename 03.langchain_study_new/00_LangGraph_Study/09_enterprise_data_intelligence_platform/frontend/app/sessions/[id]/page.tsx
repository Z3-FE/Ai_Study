import ChatSessionView from "@/components/insight-agent/chat-session-view";

interface SessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function SessionPage({ params }: SessionPageProps) {
  const { id } = await params;
  return <ChatSessionView conversationId={id} />;
}
