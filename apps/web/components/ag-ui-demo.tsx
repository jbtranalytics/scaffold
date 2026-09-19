"use client";

import { useState } from "react";
import { PROTOCOL_VERSION } from "@ag-ui/core";
import { Button } from "@/components/ui/button";
import { MarkdownView } from "@/components/markdown-view";
import { Bot, Send, Sparkles, User } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function AgUiDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Hello! AG-UI Protocol (v${PROTOCOL_VERSION}) & React Markdown are ready.\n\n- Supports **GitHub Flavored Markdown**\n- Ready for \`@assistant-ui/react-ag-ui\` runtime\n- Interoperable with FastAPI backend`,
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    const userText = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userText },
      {
        role: "assistant",
        content: `Echoing via AG-UI message event: **${userText}**\n\n\`\`\`json\n{\n  "protocol": "ag-ui",\n  "version": "${PROTOCOL_VERSION}",\n  "status": "connected"\n}\n\`\`\``,
      },
    ]);
  };

  return (
    <div className="flex flex-col w-full rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
        <div className="flex items-center gap-2 font-medium">
          <Bot className="size-5 text-primary" />
          <span>AG-UI Agent Chat Surface</span>
        </div>
        <span className="text-xs bg-muted px-2.5 py-1 rounded-full text-muted-foreground">
          AG-UI v{PROTOCOL_VERSION}
        </span>
      </div>

      <div className="flex flex-col gap-4 max-h-80 overflow-y-auto pr-1">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 text-sm ${
              msg.role === "assistant" ? "bg-muted/40" : "bg-primary/5"
            } p-3 rounded-lg`}
          >
            {msg.role === "assistant" ? (
              <Sparkles className="size-4 text-primary shrink-0 mt-0.5" />
            ) : (
              <User className="size-4 text-muted-foreground shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <MarkdownView content={msg.content} />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Send a message to AG-UI agent..."
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button onClick={handleSend} size="sm" className="gap-1.5">
          <Send className="size-3.5" />
          Send
        </Button>
      </div>
    </div>
  );
}
