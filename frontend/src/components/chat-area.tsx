import React, { useState, useRef, useEffect } from "react";
import { useChatStore } from "../store/useChatStore";
import { 
  Send, Sparkles, AlertCircle, Copy, Check, ThumbsUp, ThumbsDown, 
  Plus, FileText, User, Database, ChevronRight, MessageSquare, Activity,
  Loader2, Zap
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const ChatArea: React.FC = () => {
  const { 
    messages, 
    loading, 
    sendMessage, 
    setSelectedRAGDetail,
    retrievalStrategy,
    model,
    uploadFile,
    uploadStatus,
    uploadProgress,
    contextPanelOpen,
    setContextPanelOpen,
    setStrategyAnalysisOpen,
    selectedRAGDetail
  } = useChatStore();

  const [input, setInput] = useState("");
  const [copiedId, setCopiedId] = useState<string | number | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim(), retrievalStrategy);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string, id: string | number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleAttachClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  };

  const strategyConfig: Record<string, { label: string; color: string }> = {
    auto:   { label: "Auto", color: "#a78bfa" },
    hybrid: { label: "Hybrid", color: "#34d399" },
    dense:  { label: "Deep", color: "#60a5fa" },
    bm25:   { label: "BM25", color: "#fbbf24" },
  };
  const currentStrategy = strategyConfig[retrievalStrategy] ?? strategyConfig["auto"];

  return (
    <div className="flex-1 flex flex-col h-screen text-zinc-100 relative" style={{ background: "var(--background)" }}>
      
      {/* ── Header ──────────────────────────────────────── */}
      <div className="h-14 flex items-center justify-between px-6 shrink-0"
        style={{ borderBottom: "1px solid var(--border)", background: "rgba(6,6,9,0.85)", backdropFilter: "blur(20px)" }}>
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-emerald-500 pulse-ring" />
          </div>
          <div>
            <h1 className="text-[11px] font-bold tracking-widest text-zinc-300 uppercase">Conversational RAG Workspace</h1>
            <p className="text-[9px] text-zinc-600 font-medium">Vector database connected • Semantic cache active</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {selectedRAGDetail && (
            <button
              onClick={() => setContextPanelOpen(!contextPanelOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200"
              style={contextPanelOpen
                ? { background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)", color: "#a78bfa" }
                : { background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", color: "#a1a1aa" }
              }
            >
              <Database size={11} />
              {contextPanelOpen ? "Hide Sources" : "Inspect RAG"}
            </button>
          )}
        </div>
      </div>

      {/* ── Messages ────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 md:px-16 lg:px-28 py-8 space-y-7">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          const isSystem = msg.role === "system";
          const metadata = msg.metadata;

          /* System / status pill */
          if (isSystem) {
            return (
              <div key={msg.id} className="flex justify-center my-2 animate-slide-up">
                <div className="flex items-start gap-2.5 px-4 py-2.5 rounded-xl text-zinc-400 text-[11px] max-w-lg leading-relaxed"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
                  <AlertCircle size={13} className="text-indigo-400 shrink-0 mt-0.5" />
                  <span>{msg.content}</span>
                </div>
              </div>
            );
          }

          return (
            <div 
              key={msg.id}
              className={`flex gap-3 max-w-3xl animate-slide-up w-full ${
                isUser ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                isUser ? "" : ""
              }`}
                style={isUser
                  ? { background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.2)" }
                  : { background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }
                }
              >
                {isUser 
                  ? <User size={13} className="text-indigo-400" /> 
                  : <Sparkles size={13} className="text-blue-400" />
                }
              </div>

              {/* Content */}
              <div className="flex-1 space-y-2 min-w-0">
                <div className={`text-[9px] font-bold tracking-widest uppercase px-0.5 ${
                  isUser ? "text-right text-indigo-400/60" : "text-left text-blue-400/60"
                }`}>
                  {isUser ? "You" : "RAG Assistant"}
                </div>

                <div className="rounded-2xl text-sm leading-relaxed px-4 py-3.5 transition-all duration-200"
                  style={isUser
                    ? { background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", borderTopRightRadius: "6px", color: "#e2e2ef" }
                    : { background: "rgba(255,255,255,0.034)", border: "1px solid var(--border)", borderTopLeftRadius: "6px", color: "#d4d4e0" }
                  }
                >
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      className="prose-chat"
                      components={{
                        p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                        a: ({ href, children }) => (
                          <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors">
                            {children}
                          </a>
                        ),
                        code: ({ children }) => (
                          <code className="px-1.5 py-0.5 rounded text-xs text-rose-300 font-mono"
                            style={{ background: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.15)" }}>
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="rounded-xl p-4 overflow-x-auto my-3 text-xs font-mono leading-relaxed"
                            style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)" }}>
                            {children}
                          </pre>
                        ),
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-3 space-y-1">{children}</ul>,
                        li: ({ children }) => <li className="text-zinc-300">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold text-zinc-100">{children}</strong>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>

                {/* Diagnostics bar */}
                {!isUser && metadata && (
                  <div className="flex flex-wrap items-center gap-2 px-0.5 text-[10px]">
                    <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] uppercase font-bold tracking-wider font-mono ${
                      metadata.is_cached 
                        ? "text-emerald-400" 
                        : "text-amber-500"
                    }`} style={metadata.is_cached
                      ? { background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }
                      : { background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }
                    }>
                      {metadata.is_cached ? "⚡ Cache Hit" : "◈ Cache Miss"}
                    </span>

                    <span className="text-zinc-600 font-mono">
                      {metadata.metadata.latencies.total_ms}ms
                    </span>

                    <button 
                      onClick={() => setSelectedRAGDetail(metadata)}
                      className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                    >
                      View Sources ({Object.keys(metadata.citations).length})
                      <ChevronRight size={10} />
                    </button>
                    
                    <button 
                      onClick={() => { setSelectedRAGDetail(metadata); setStrategyAnalysisOpen(true); }}
                      className="flex items-center gap-1 font-semibold transition-colors"
                      style={{ color: "#fbbf24" }}
                    >
                      Analysis
                      <Activity size={10} />
                    </button>

                    <div className="flex items-center gap-1 ml-auto" style={{ borderLeft: "1px solid var(--border)", paddingLeft: "10px" }}>
                      <button 
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="p-1 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-white/5 transition-all duration-150"
                        title="Copy"
                      >
                        {copiedId === msg.id ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                      </button>
                      <button className="p-1 rounded-lg text-zinc-600 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all duration-150">
                        <ThumbsUp size={11} />
                      </button>
                      <button className="p-1 rounded-lg text-zinc-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-150">
                        <ThumbsDown size={11} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Thinking indicator */}
        {loading && (
          <div className="flex items-center gap-3 max-w-xs animate-slide-up">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
              <Sparkles size={13} className="text-blue-400" />
            </div>
            <div className="px-4 py-3 rounded-2xl rounded-tl-md"
              style={{ background: "rgba(255,255,255,0.034)", border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1.5">
                {[0, 150, 300].map(delay => (
                  <div key={delay} className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce"
                    style={{ animationDelay: `${delay}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* ── Empty state ─────────────────────────────────── */}
      {messages.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-8 pointer-events-none select-none">
          <div className="max-w-sm text-center space-y-5">
            <div className="relative w-16 h-16 mx-auto animate-float">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white"
                style={{ 
                  background: "linear-gradient(135deg,#3b82f6,#6366f1,#8b5cf6)",
                  boxShadow: "0 8px 32px rgba(99,102,241,0.35), 0 0 0 1px rgba(99,102,241,0.2)" 
                }}>
                <Sparkles size={26} />
              </div>
            </div>
            <div>
              <h2 className="text-lg font-bold text-zinc-100 mb-2">AI RAG Workspace</h2>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Attach documents with <span className="text-indigo-400 font-bold">+</span> and ask anything.
                Multi-turn vector retrieval with cross-encoder reranking.
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-[10px] text-zinc-700">
              <span className="flex items-center gap-1"><Zap size={9} className="text-amber-500/70" /> Semantic Cache</span>
              <span className="flex items-center gap-1"><Database size={9} className="text-blue-500/70" /> FAISS Index</span>
              <span className="flex items-center gap-1"><Activity size={9} className="text-emerald-500/70" /> Self-Eval</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Input area ──────────────────────────────────── */}
      <div className="px-4 md:px-16 lg:px-28 pb-5 pt-3 shrink-0"
        style={{ borderTop: "1px solid var(--border)", background: "rgba(6,6,9,0.8)", backdropFilter: "blur(20px)" }}>

        {/* Upload progress */}
        {uploadStatus !== "idle" && (
          <div className="max-w-2xl mx-auto mb-3 px-3 py-2.5 rounded-xl flex items-center gap-3"
            style={{ background: "rgba(59,130,246,0.06)", border: "1px solid rgba(59,130,246,0.15)" }}>
            <FileText size={13} className="text-blue-400 animate-pulse shrink-0" />
            <div className="flex-1 text-[10px] space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Indexing document…</span>
                <span className="font-mono text-blue-400">{uploadProgress}%</span>
              </div>
              <div className="w-full h-0.5 rounded-full" style={{ background: "var(--border)" }}>
                <div className="h-0.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%`, background: "linear-gradient(90deg,#3b82f6,#6366f1)" }} />
              </div>
            </div>
          </div>
        )}

        {/* Main input box */}
        <div className="max-w-2xl mx-auto flex items-end gap-2 rounded-2xl p-2 input-ring transition-all duration-300"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
          
          {/* Attach */}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".pdf,.txt,.md,.markdown,.docx,.pptx" className="hidden" />
          <button 
            onClick={handleAttachClick}
            disabled={uploadStatus !== "idle"}
            className="p-2 rounded-xl text-zinc-600 hover:text-zinc-300 hover:bg-white/5 transition-all duration-150 shrink-0 disabled:opacity-30"
            title="Attach document"
          >
            <Plus size={15} />
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your documents…"
            rows={1}
            className="flex-1 resize-none bg-transparent py-2 text-sm text-zinc-200 focus:outline-none placeholder-zinc-600 leading-normal"
          />

          {/* Strategy selector */}
          <select 
            value={retrievalStrategy}
            onChange={(e) => useChatStore.getState().updateSettings({ retrievalStrategy: e.target.value as any })}
            className="rounded-lg px-2 py-1.5 text-[10px] font-semibold outline-none cursor-pointer transition-all duration-150 shrink-0 font-mono"
            style={{ 
              background: "rgba(255,255,255,0.05)", 
              border: "1px solid var(--border)", 
              color: currentStrategy.color 
            }}
          >
            <option value="auto">Auto</option>
            <option value="hybrid">Hybrid</option>
            <option value="dense">Deep</option>
            <option value="bm25">BM25</option>
          </select>

          {/* Send */}
          <button 
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl text-white transition-all duration-200 shrink-0 disabled:opacity-30 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
            style={{ background: "linear-gradient(135deg,#3b82f6,#6366f1)", boxShadow: "0 4px 16px rgba(99,102,241,0.3)" }}
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          </button>
        </div>

        <div className="text-center mt-2.5 text-[9px] tracking-widest uppercase font-medium" style={{ color: "#27272f" }}>
          SQLite persisted · Semantic cache · Cross-encoder rerank
        </div>
      </div>
    </div>
  );
};
