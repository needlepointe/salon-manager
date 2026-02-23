import { useState, useRef, useEffect } from "react";
import { Send, MessageSquare, Plus } from "lucide-react";
import Spinner from "../components/ui/Spinner";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Chat() {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startSession = async () => {
    setCreating(true);
    try {
      const res = await fetch("/api/v1/chat/session", { method: "POST" });
      const data = await res.json();
      setSessionToken(data.session_token);
      setMessages([]);
    } finally {
      setCreating(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionToken || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch(`/api/v1/chat/session/${sessionToken}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!response.body) return;

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let text = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const raw = decoder.decode(value, { stream: true });
        // Strip SSE "data: " prefix lines
        const lines = raw.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            text += line.slice(6);
          } else if (line.trim()) {
            text += line;
          }
        }
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: text,
          };
          return updated;
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-brand-600" />
          <span className="text-sm text-gray-500">
            FAQ Chatbot — powered by Claude AI
          </span>
        </div>
        <button
          onClick={startSession}
          disabled={creating}
          className="btn-secondary text-sm"
        >
          {creating ? <Spinner size="sm" /> : <Plus className="w-4 h-4" />}
          New Session
        </button>
      </div>

      <div className="flex-1 card overflow-y-auto space-y-4 p-4">
        {!sessionToken ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <MessageSquare className="w-12 h-12 text-gray-300" />
            <p className="text-sm text-gray-500">
              Start a new session to chat with the AI
            </p>
            <button onClick={startSession} disabled={creating} className="btn-primary">
              {creating ? <Spinner size="sm" /> : null}
              Start Chat
            </button>
          </div>
        ) : messages.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            Session active — ask about pricing, availability, aftercare...
          </p>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-900 rounded-bl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-4 flex gap-2">
        <input
          className="input flex-1"
          placeholder={
            sessionToken ? "Ask about pricing, booking, aftercare..." : "Start a session first"
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!sessionToken || loading}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />
        <button
          onClick={sendMessage}
          disabled={!sessionToken || loading || !input.trim()}
          className="btn-primary px-3"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
