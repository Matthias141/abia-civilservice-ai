"use client";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function ChatMessage({
  role,
  content,
  sources,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-green-800 text-white rounded-br-md"
            : "bg-white text-gray-800 border border-gray-200 rounded-bl-md shadow-sm"
        }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-green-700">
              AbiaCS Assistant
            </span>
          </div>
        )}
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {content}
        </div>
        {sources && sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-400 mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {sources.map((source, i) => (
                <span
                  key={i}
                  className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
