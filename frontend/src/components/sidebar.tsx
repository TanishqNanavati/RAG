import React, { useState } from "react";
import { useChatStore } from "../store/useChatStore";
import { 
  Plus, MessageSquare, Trash2, Settings, FileText, 
  ChevronLeft, ChevronRight, Search, FileUp, TrendingUp, Sparkles,
  LogOut, User as UserIcon
} from "lucide-react";
import { UserProfileModal } from "./user-profile-modal";

interface SidebarProps {
  onOpenSettings: () => void;
  onOpenDashboard: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenSettings, onOpenDashboard }) => {
  const {
    sessions,
    currentSessionId,
    sidebarOpen,
    setSidebarOpen,
    createSession,
    selectSession,
    deleteSession,
    renameSession,
    documents,
    uploadFile,
    uploadStatus,
    uploadProgress
  } = useChatStore();

  const [searchTerm, setSearchTerm] = useState("");
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  };

  const filteredSessions = sessions.filter(s => 
    s.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleRenameSubmit = () => {
    if (editingSessionId && editingTitle.trim()) {
      renameSession(editingSessionId, editingTitle.trim(), true);
    }
    setEditingSessionId(null);
  };

  /* ── Collapsed rail ────────────────────────────── */
  if (!sidebarOpen) {
    return (
      <div className="w-14 h-screen flex flex-col items-center py-4 justify-between transition-all duration-300"
        style={{ background: "var(--sidebar-background)", borderRight: "1px solid var(--border)" }}>
        <button 
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-xl text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all duration-200"
          title="Expand sidebar"
        >
          <ChevronRight size={16} />
        </button>
        <div className="flex flex-col gap-3">
          <button 
            onClick={() => createSession()}
            className="p-2.5 rounded-xl text-white transition-all duration-200 hover:scale-105 active:scale-95"
            style={{ background: "linear-gradient(135deg,#3b82f6,#6366f1)", boxShadow: "0 4px 16px rgba(99,102,241,0.3)" }}
            title="New conversation"
          >
            <Plus size={15} />
          </button>
        </div>
        <button onClick={onOpenSettings} className="p-2 rounded-xl text-zinc-600 hover:text-zinc-300 hover:bg-white/5 transition-all duration-200">
          <Settings size={16} />
        </button>
      </div>
    );
  }

  /* ── Full sidebar ──────────────────────────────── */
  return (
    <div 
      className="w-64 h-screen flex flex-col justify-between transition-all duration-300"
      style={{ background: "var(--sidebar-background)", borderRight: "1px solid var(--border)" }}
    >
      {/* ── Top brand / collapse row ── */}
      <div className="px-4 pt-4 pb-3" style={{ borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" 
              style={{ background: "linear-gradient(135deg,#3b82f6,#6366f1)", boxShadow: "0 4px 14px rgba(99,102,241,0.35)" }}>
              <Sparkles size={13} className="text-white" />
            </div>
            <div>
              <div className="text-[11px] font-bold tracking-wider text-zinc-200 uppercase">Workspace</div>
              <div className="text-[9px] text-zinc-600 -mt-0.5">RAG Intelligence</div>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-white/5 transition-all duration-200"
          >
            <ChevronLeft size={14} />
          </button>
        </div>

        <button 
          onClick={() => createSession()}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-[11px] font-semibold text-white transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          style={{ background: "linear-gradient(135deg,#3b82f6,#6366f1)", boxShadow: "0 4px 16px rgba(99,102,241,0.25)" }}
        >
          <Plus size={13} />
          New Conversation
        </button>
      </div>

      {/* ── Search ── */}
      <div className="px-3 py-2.5">
        <div className="relative">
          <Search size={11} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input 
            type="text"
            placeholder="Search conversations…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg text-[11px] text-zinc-300 placeholder-zinc-600 focus:outline-none focus:ring-1 transition-all"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", outlineColor: "rgba(99,102,241,0.5)" }}
          />
        </div>
      </div>

      {/* ── Session list ── */}
      <div className="flex-1 overflow-y-auto px-2 pb-2 flex flex-col gap-0.5">
        <div className="px-2 pb-1.5 pt-0.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600">
          Conversations
        </div>

        {filteredSessions.map(session => (
          <div 
            key={session.id}
            onClick={() => {
              if (editingSessionId !== session.id) selectSession(session.id);
            }}
            onDoubleClick={() => {
              setEditingSessionId(session.id);
              setEditingTitle(session.title);
            }}
            className={`group flex items-center justify-between px-2.5 py-2 rounded-xl cursor-pointer text-xs transition-all duration-150 ${
              currentSessionId === session.id 
                ? "text-zinc-100 font-medium" 
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            style={currentSessionId === session.id 
              ? { background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }
              : { border: "1px solid transparent" }
            }
          >
            <div className="flex items-center gap-2 truncate min-w-0 w-full">
              <MessageSquare size={12} className={`shrink-0 ${currentSessionId === session.id ? "text-indigo-400" : "text-zinc-600"}`} />
              {editingSessionId === session.id ? (
                <input
                  type="text"
                  value={editingTitle}
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onBlur={handleRenameSubmit}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameSubmit();
                    if (e.key === "Escape") setEditingSessionId(null);
                  }}
                  autoFocus
                  className="bg-transparent border-none outline-none text-zinc-100 w-full min-w-0"
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="truncate" title="Double click to rename">{session.title}</span>
              )}
            </div>
            {editingSessionId !== session.id && (
              <button 
                onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-zinc-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-150 shrink-0 ml-1"
              >
                <Trash2 size={11} />
              </button>
            )}
          </div>
        ))}

        {filteredSessions.length === 0 && (
          <div className="text-zinc-600 text-[11px] px-2 py-6 text-center">
            {searchTerm ? "No matches found." : "No conversations yet."}
          </div>
        )}
      </div>

      {/* ── Documents section ── */}
      <div className="px-3 py-3" style={{ borderTop: "1px solid var(--border)", background: "rgba(0,0,0,0.2)" }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[9px] uppercase font-bold tracking-widest text-zinc-600">Documents</span>
          <label className="cursor-pointer p-1.5 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-white/5 transition-all duration-200" title="Upload document">
            <FileUp size={13} />
            <input 
              type="file" 
              accept=".pdf,.txt,.md,.markdown,.docx,.pptx"
              className="hidden" 
              onChange={handleFileUpload}
              disabled={uploadStatus === "uploading" || uploadStatus === "analyzing"}
            />
          </label>
        </div>

        {uploadStatus !== "idle" && (
          <div className="mb-2 px-2 py-1.5 rounded-lg text-[10px]" style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.15)" }}>
            <div className="flex justify-between text-zinc-400 mb-1">
              <span>Indexing…</span>
              <span className="font-mono text-blue-400">{uploadProgress}%</span>
            </div>
            <div className="w-full h-0.5 rounded-full" style={{ background: "var(--border)" }}>
              <div className="h-0.5 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%`, background: "linear-gradient(90deg,#3b82f6,#6366f1)" }} />
            </div>
          </div>
        )}

        <div className="max-h-28 overflow-y-auto flex flex-col gap-1">
          {documents.map(doc => (
            <div key={doc.id} className="flex items-center justify-between px-2 py-1.5 rounded-lg text-[10px] text-zinc-400 transition-colors hover:bg-white/3"
              style={{ border: "1px solid var(--border-soft)" }}>
              <div className="flex items-center gap-1.5 min-w-0 truncate">
                <FileText size={11} className="text-indigo-400 shrink-0" />
                <span className="truncate">{doc.name}</span>
              </div>
              <span className="shrink-0 ml-2 font-mono text-[9px] text-zinc-600">
                {doc.chunksCount ? `${doc.chunksCount}c` : doc.size}
              </span>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="text-[10px] text-zinc-700 py-2 text-center italic">
              No documents indexed.
            </div>
          )}
        </div>
      </div>

      {/* ── Footer: evaluation + user ── */}
      <div className="px-3 pb-3 pt-2 flex flex-col gap-2" style={{ borderTop: "1px solid var(--border)" }}>
        <button 
          onClick={onOpenDashboard}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-[11px] font-semibold text-zinc-400 hover:text-zinc-200 transition-all duration-200 hover:bg-white/5"
          style={{ border: "1px solid var(--border)" }}
        >
          <TrendingUp size={12} className="text-zinc-500" />
          Evaluation Dashboard
        </button>

        {/* User auth area */}
        {useChatStore.getState().user ? (
          <>
            <div 
              className="flex items-center gap-2 px-1 cursor-pointer hover:bg-white/5 rounded-xl py-1 transition-colors"
              onClick={() => setIsProfileModalOpen(true)}
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-[10px] text-white shrink-0"
                style={{ background: "linear-gradient(135deg,#6366f1,#3b82f6)" }}>
                {useChatStore.getState().user?.username.substring(0,2).toUpperCase()}
              </div>
              <span className="text-[11px] font-medium text-zinc-300 truncate flex-1">
                {useChatStore.getState().user?.username}
              </span>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  useChatStore.getState().logout();
                }}
                className="p-1.5 rounded-lg text-zinc-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-200"
                title="Sign out"
              >
                <LogOut size={12} />
              </button>
            </div>
            {isProfileModalOpen && (
              <UserProfileModal onClose={() => setIsProfileModalOpen(false)} />
            )}
          </>
        ) : (
          <button 
            onClick={() => useChatStore.getState().setAuthModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-[11px] font-semibold transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
            style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)", color: "#818cf8" }}
          >
            <UserIcon size={12} />
            Sign In / Register
          </button>
        )}
      </div>
    </div>
  );
};
