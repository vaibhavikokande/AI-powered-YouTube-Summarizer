import { useState } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Streams tokens from POST /api/v1/chat's SSE response. Uses raw fetch
 * rather than axios — axios doesn't expose a readable stream in the
 * browser the way the Fetch API's response.body does.
 */
export function ChatPanel({ videoUrl }: { videoUrl: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  async function sendMessage() {
    const question = input.trim();
    if (!question || isStreaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }, { role: "assistant", content: "" }]);
    setIsStreaming(true);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ url: videoUrl, session_id: sessionId, message: question }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          if (!event.startsWith("data: ")) continue;
          const payload = JSON.parse(event.slice("data: ".length));

          if (payload.token) {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, content: last.content + payload.token };
              return next;
            });
          }
          if (payload.done) {
            setSessionId(payload.session_id);
          }
        }
      }
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask about this video</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex max-h-80 flex-col gap-3 overflow-y-auto">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Ask a question like &quot;What was the conclusion?&quot;
            </p>
          )}
          {messages.map((message, i) => (
            <div
              key={i}
              className={cn(
                "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                message.role === "user"
                  ? "self-end bg-primary text-primary-foreground"
                  : "self-start bg-muted"
              )}
            >
              {message.content || (isStreaming && i === messages.length - 1 && <Spinner />)}
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask a question..."
            disabled={isStreaming}
          />
          <Button onClick={sendMessage} disabled={isStreaming || !input.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
