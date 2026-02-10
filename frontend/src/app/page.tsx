"use client";

import { useState, useEffect, useRef } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import SuggestedQuestions from "@/components/SuggestedQuestions";
import Sidebar from "@/components/Sidebar";
import { sendMessage, fetchSuggestedQuestions } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSuggestedQuestions().then(setSuggestedQuestions);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const data = await sendMessage(text, conversationId);
      setConversationId(data.conversation_id);
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content:
          err instanceof Error
            ? err.message
            : "Sorry, something went wrong. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  return (
    <div className="flex h-screen">
      <Sidebar onNewChat={handleNewChat} />
      <main className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full pt-20">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  AbiaCS Assistant
                </h2>
                <p className="text-gray-500 mb-8 text-center max-w-md">
                  Ask any question about Abia State Civil Service rules,
                  regulations, promotions, leave, pensions, and more.
                </p>
                <SuggestedQuestions
                  questions={suggestedQuestions}
                  onSelect={handleSend}
                />
              </div>
            ) : (
              messages.map((msg, i) => (
                <ChatMessage
                  key={i}
                  role={msg.role}
                  content={msg.content}
                  sources={msg.sources}
                />
              ))
            )}
            {loading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                  <span className="text-sm text-gray-400 typing-cursor">
                    Thinking
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <ChatInput onSend={handleSend} disabled={loading} />
      </main>
    </div>
  );
}
