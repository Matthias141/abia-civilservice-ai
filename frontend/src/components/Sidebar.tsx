"use client";

interface SidebarProps {
  onNewChat: () => void;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
  return (
    <aside className="w-64 bg-green-900 text-white flex flex-col h-full">
      <div className="p-4 border-b border-green-800">
        <h1 className="text-lg font-bold">AbiaCS Assistant</h1>
        <p className="text-xs text-green-300 mt-1">
          Abia State Civil Service AI
        </p>
      </div>
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full rounded-lg border border-green-700 px-3 py-2 text-sm hover:bg-green-800 transition-colors text-left"
        >
          + New Chat
        </button>
      </div>
      <div className="flex-1" />
      <div className="p-4 border-t border-green-800">
        <p className="text-xs text-green-400">
          Powered by RAG + Claude AI
        </p>
      </div>
    </aside>
  );
}
