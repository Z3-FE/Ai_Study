"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  type AppendMessage,
  type ThreadMessage,
  type ThreadMessageLike,
  useAuiState,
  useExternalStoreRuntime,
  useMessage,
} from "@assistant-ui/react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clock,
  Database,
  Loader2,
  MessageSquare,
  Send,
  User,
} from "lucide-react";
import { apiGet, apiPost } from "../../lib/api";

interface ChatSessionViewProps {
  conversationId: string;
}

interface RunStep {
  step: string;
  name: string;
  status: "running" | "completed" | "failed";
  summary?: string;
}

interface BackendMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
}

interface AssistantChatRuntimeProps {
  messages: ThreadMessageLike[];
  isRunning: boolean;
  children: React.ReactNode;
  onNew: (message: AppendMessage) => Promise<void>;
  onCancel: () => Promise<void>;
}

function formatTime(value?: Date | string) {
  if (!value) return "--";
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function upsertStep(steps: RunStep[], next: RunStep) {
  const index = steps.findIndex((step) => step.step === next.step);
  if (index === -1) return [...steps, next];

  const cloned = [...steps];
  cloned[index] = { ...cloned[index], ...next };
  return cloned;
}

function getMessageText(message: ThreadMessage | ThreadMessageLike) {
  if (typeof message.content === "string") return message.content;

  return message.content
    .map((part) => {
      if ("text" in part && typeof part.text === "string") return part.text;
      return "";
    })
    .join("");
}

function toAssistantMessage(message: BackendMessage): ThreadMessageLike {
  return {
    id: message.id,
    role: message.role,
    content: [{ type: "text", text: message.content }],
    createdAt: message.created_at ? new Date(message.created_at) : new Date(),
  };
}

async function* readRunEvents(eventsUrl: string, abortSignal?: AbortSignal) {
  const response = await fetch(eventsUrl, {
    cache: "no-store",
    headers: {
      Accept: "text/event-stream",
    },
    signal: abortSignal,
  });

  if (!response.ok || !response.body) {
    throw new Error("SSE 连接失败，请检查后端服务是否仍在运行。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const dataLines = chunk
        .split("\n")
        .filter((line) => line.startsWith("data: "))
        .map((line) => line.slice("data: ".length));

      if (dataLines.length === 0) continue;
      yield JSON.parse(dataLines.join("\n"));
    }
  }

  if (buffer.trim()) {
    const dataLines = buffer
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice("data: ".length));

    if (dataLines.length > 0) {
      yield JSON.parse(dataLines.join("\n"));
    }
  }
}

function getAppendMessageText(message: AppendMessage) {
  return message.content
    .map((part) => {
      if (part.type === "text") return part.text;
      return "";
    })
    .join("")
    .trim();
}

// 发送events请求
function AssistantChatRuntime({
  messages,
  isRunning,
  children,
  onNew,
  onCancel,
}: AssistantChatRuntimeProps) {
  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages,
    isRunning,
    onNew,
    onCancel,
    convertMessage: (message) => message as ThreadMessage,
  });

  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>;
}

function AssistantMessageBubble() {
  const message = useMessage();
  const threadIsRunning = useAuiState((state) => state.thread.isRunning);
  const lastMessageId = useAuiState((state) => state.thread.messages.at(-1)?.id);
  const isUser = message.role === "user";
  const showStreamingCursor =
    threadIsRunning &&
    !isUser &&
    message.id === lastMessageId &&
    message.status?.type === "running";

  return (
    <MessagePrimitive.Root className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[70%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-6 whitespace-pre-wrap ${isUser
              ? "bg-blue-600 text-white shadow-sm"
              : "bg-white text-slate-700 border border-slate-200 shadow-sm"
            }`}
        >
          <MessagePrimitive.Content />
          {showStreamingCursor && (
            <span className="ml-1 inline-block w-1.5 h-4 bg-blue-500 animate-pulse align-middle" />
          )}
        </div>
        <span className="text-[10px] text-slate-400 mt-1 px-1">
          {formatTime(message.createdAt)}
        </span>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-600 flex items-center justify-center shrink-0">
          <User className="w-4 h-4" />
        </div>
      )}
    </MessagePrimitive.Root>
  );
}

// 整体页面
function AssistantChatThread() {
  const isRunning = useAuiState((state) => state.thread.isRunning);

  return (
    <ThreadPrimitive.Root className="flex-1 min-h-0 flex flex-col">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        <ThreadPrimitive.Empty>
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
            <Bot className="w-10 h-10 mx-auto text-blue-500 mb-3" />
            <div className="font-extrabold text-slate-800">这是一条真实聊天链路</div>
            <p className="text-sm text-slate-500 mt-2">
              发送一句话，后端会创建 run，LangGraph 执行 chat 节点，并通过 SSE 返回结果。
            </p>
          </div>
        </ThreadPrimitive.Empty>
        {/* 会话信息 */}
        <ThreadPrimitive.Messages components={{ Message: AssistantMessageBubble }} />
      </ThreadPrimitive.Viewport>
      {/* 输入框 */}
      <div className="bg-white border-t border-slate-200 p-4">
        <ComposerPrimitive.Root className="flex gap-3">
          <ComposerPrimitive.Input
            submitMode="enter"
            placeholder="继续提问，例如：先介绍一下你现在能做什么"
            className="min-h-[52px] max-h-[140px] flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-blue-500 focus:bg-white"
          />
          {isRunning ? (
            <ComposerPrimitive.Cancel className="w-12 h-12 rounded-xl bg-slate-700 text-white flex items-center justify-center shadow-sm hover:bg-slate-800 transition-colors">
              <Loader2 className="w-5 h-5 animate-spin" />
            </ComposerPrimitive.Cancel>
          ) : (
            <ComposerPrimitive.Send className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors">
              <Send className="w-5 h-5" />
            </ComposerPrimitive.Send>
          )}
        </ComposerPrimitive.Root>
      </div>
    </ThreadPrimitive.Root>
  );
}

export default function ChatSessionView({ conversationId }: ChatSessionViewProps) {
  const [conversation, setConversation] = useState<any | null>(null);
  const [messages, setMessages] = useState<ThreadMessageLike[]>([]);
  const [steps, setSteps] = useState<RunStep[]>([]);
  const [activeRunId, setActiveRunId] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const pendingStartedRef = useRef(false);
  const activeAbortControllerRef = useRef<AbortController | null>(null);

  const loadConversation = useCallback(async () => {
    const [conversationData, messageData] = await Promise.all([
      apiGet(`/api/conversations/${conversationId}`),
      apiGet(`/api/conversations/${conversationId}/messages`),
    ]);

    setConversation(conversationData.conversation);
    setMessages((messageData.messages ?? []).map(toAssistantMessage));
    setIsLoading(false);
  }, [conversationId]);

  const sendQuestion = useCallback(
    async (question: string, content?: AppendMessage["content"]) => {
      const normalizedQuestion = question.trim();
      if (!normalizedQuestion || isRunning) return;

      const userMessage: ThreadMessageLike = {
        id: `local_user_${crypto.randomUUID()}`,
        role: "user",
        content: content ?? [{ type: "text", text: normalizedQuestion }],
        createdAt: new Date(),
      };
      const assistantMessageId = `local_assistant_${crypto.randomUUID()}`;
      const assistantMessage: ThreadMessageLike = {
        id: assistantMessageId,
        role: "assistant",
        content: [{ type: "text", text: "" }],
        createdAt: new Date(),
        status: { type: "running" },
      } as ThreadMessageLike;

      setError("");
      setSteps([]);
      setActiveRunId("");
      setIsRunning(true);
      setMessages((current) => [...current, userMessage, assistantMessage]);

      const abortController = new AbortController();
      activeAbortControllerRef.current = abortController;

      let assistantText = "";
      let failedMessage = "";

      try {
        const runData = await apiPost(`/api/conversations/${conversationId}/runs`, {
          question: normalizedQuestion,
        });
        setActiveRunId(runData.run_id);

        for await (const runEvent of readRunEvents(runData.events_url, abortController.signal)) {
          const payload = runEvent.data ?? {};

          if (runEvent.type === "step.started") {
            setSteps((current) =>
              upsertStep(current, {
                step: payload.step,
                name: payload.name,
                status: "running",
              }),
            );
          }

          if (runEvent.type === "step.completed") {
            setSteps((current) =>
              upsertStep(current, {
                step: payload.step,
                name: payload.name,
                status: "completed",
                summary: payload.summary,
              }),
            );
          }

          if (runEvent.type === "message.delta" && payload.content) {
            assistantText += payload.content;
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? ({
                      ...message,
                      content: [{ type: "text", text: assistantText }],
                      status: { type: "running" },
                    } as ThreadMessageLike)
                  : message,
              ),
            );
          }

          if (runEvent.type === "run.completed") {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? ({
                      ...message,
                      content: [{ type: "text", text: assistantText }],
                      status: { type: "complete", reason: "stop" },
                    } as ThreadMessageLike)
                  : message,
              ),
            );
            setIsRunning(false);
            await loadConversation();
            break;
          }

          if (runEvent.type === "run.failed") {
            failedMessage = payload.message ?? "运行失败";
            break;
          }
        }

        if (failedMessage) {
          setError(failedMessage);
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? ({
                    ...message,
                    content: [{ type: "text", text: failedMessage }],
                    status: { type: "incomplete", reason: "error" },
                  } as ThreadMessageLike)
                : message,
            ),
          );
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          const message = err instanceof Error ? err.message : "运行失败";
          setError(message);
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantMessageId
                ? ({
                    ...item,
                    content: [{ type: "text", text: message }],
                    status: { type: "incomplete", reason: "error" },
                  } as ThreadMessageLike)
                : item,
            ),
          );
        }
      } finally {
        if (activeAbortControllerRef.current === abortController) {
          activeAbortControllerRef.current = null;
        }
        setIsRunning(false);
      }
    },
    [conversationId, isRunning, loadConversation],
  );

  const handleNewMessage = useCallback(
    async (message: AppendMessage) => {
      const text = getAppendMessageText(message);
      await sendQuestion(text, message.content);
    },
    [sendQuestion],
  );

  const handleCancel = useCallback(async () => {
    activeAbortControllerRef.current?.abort();
    activeAbortControllerRef.current = null;
    setIsRunning(false);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    setError("");
    setSteps([]);
    setActiveRunId("");
    pendingStartedRef.current = false;
    activeAbortControllerRef.current?.abort();
    activeAbortControllerRef.current = null;
    void loadConversation();
  }, [conversationId, loadConversation]);

  useEffect(() => {
    if (isLoading || pendingStartedRef.current) return;

    const pendingKey = `pending_question:${conversationId}`;
    const pendingQuestion = sessionStorage.getItem(pendingKey);
    if (!pendingQuestion) return;

    pendingStartedRef.current = true;
    sessionStorage.removeItem(pendingKey);
    void sendQuestion(pendingQuestion);
  }, [conversationId, isLoading, sendQuestion]);

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-50">
      <section className="flex-1 min-w-0 flex flex-col border-r border-slate-200">
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-[11px] font-bold text-blue-600 mb-1">
                <MessageSquare className="w-4 h-4" />
                <span>普通聊天最小链路</span>
              </div>
              <h2 className="text-xl font-extrabold text-slate-900">
                {conversation?.title ?? "加载会话中..."}
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                当前使用 assistant-ui 接管消息状态和输入框，后端仍通过 run + SSE 驱动执行详情。
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] text-slate-500">
              <div>
                Conversation: <span className="font-mono text-slate-700">{conversationId}</span>
              </div>
              <div>
                Thread:{" "}
                <span className="font-mono text-slate-700">{conversation?.thread_id ?? "--"}</span>
              </div>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center text-sm font-bold text-slate-400">
            加载会话中...
          </div>
        ) : (
          <AssistantChatRuntime
            messages={messages}
            isRunning={isRunning}
            onNew={handleNewMessage}
            onCancel={handleCancel}
          >
            <AssistantChatThread />
          </AssistantChatRuntime>
        )}

        {error && (
          <div className="mx-6 mb-3 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-600 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </section>

      <aside className="w-[360px] bg-white shrink-0 flex flex-col">
        <div className="p-5 border-b border-slate-200">
          <h3 className="text-sm font-extrabold text-slate-900">执行详情</h3>
          <p className="text-xs text-slate-500 mt-1">Phase 4 + Phase 6 最小链路事件</p>
        </div>

        <div className="p-5 space-y-4 overflow-y-auto">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-xs font-extrabold text-slate-700 mb-3">
              <Database className="w-4 h-4 text-emerald-600" />
              <span>当前状态</span>
            </div>
            <div className="space-y-2 text-xs text-slate-500">
              <div className="flex justify-between">
                <span>会话状态</span>
                <span className="font-mono text-slate-700">
                  {isRunning ? "running" : conversation?.status ?? "--"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>当前 Run</span>
                <span className="font-mono text-slate-700 truncate max-w-[180px]">
                  {activeRunId || "--"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>数据源</span>
                <span className="font-mono text-slate-700">{conversation?.data_source_id ?? "olist"}</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="text-xs font-extrabold text-slate-700 uppercase tracking-wider">Steps</div>
            {steps.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-200 px-4 py-6 text-center text-xs text-slate-400">
                等待下一次运行事件
              </div>
            )}
            {steps.map((step) => (
              <div key={step.step} className="rounded-xl border border-slate-200 bg-white p-3">
                <div className="flex items-center gap-2">
                  {step.status === "completed" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-blue-600 animate-pulse" />
                  )}
                  <span className="text-sm font-bold text-slate-800">{step.name}</span>
                  <span className="ml-auto text-[10px] font-mono text-slate-400">{step.status}</span>
                </div>
                {step.summary && <p className="text-xs text-slate-500 mt-2 leading-5">{step.summary}</p>}
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
