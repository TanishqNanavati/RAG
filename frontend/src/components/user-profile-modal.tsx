import React, { useEffect, useState } from "react";
import { X, User as UserIcon, Activity, Database, Zap, Clock, TrendingUp } from "lucide-react";
import { useChatStore } from "../store/useChatStore";
import { api } from "../services/api";

export const UserProfileModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { user } = useChatStore();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await api.getUserStats();
        setStats(data);
      } catch (e) {
        console.error("Failed to load user stats", e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStats();
  }, [user]);

  if (!user) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-2xl overflow-hidden glass shadow-2xl relative animate-in zoom-in-95 duration-300"
        style={{ border: "1px solid var(--border-soft)", background: "rgba(15, 15, 20, 0.95)" }}
      >
        {/* Header */}
        <div className="px-6 py-5 flex justify-between items-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-20 bg-gradient-to-r from-indigo-500 to-blue-500 blur-xl pointer-events-none" />
          
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg text-white shadow-lg"
              style={{ background: "linear-gradient(135deg,#6366f1,#3b82f6)" }}>
              {user.username.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">{user.username}</h2>
              <p className="text-xs text-zinc-400">
                {user.created_at ? `Member since ${new Date(user.created_at).toLocaleDateString()}` : "RAG Workspace User"}
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="p-2 rounded-full text-zinc-400 hover:text-white hover:bg-white/10 transition-colors z-10"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 bg-zinc-950/50">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-4">
            Account Statistics
          </h3>
          
          {loading ? (
            <div className="flex flex-col gap-3">
              <div className="h-20 rounded-xl bg-white/5 animate-pulse" />
              <div className="h-20 rounded-xl bg-white/5 animate-pulse" />
            </div>
          ) : stats ? (
            <div className="grid grid-cols-2 gap-3">
              {/* Stat Card 1 */}
              <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-2">
                  <Database size={14} className="text-indigo-400" />
                  <span className="text-xs text-zinc-400 font-medium">Total Chats</span>
                </div>
                <div className="text-2xl font-bold text-white">{stats.total_sessions}</div>
              </div>

              {/* Stat Card 2 */}
              <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-2">
                  <Activity size={14} className="text-blue-400" />
                  <span className="text-xs text-zinc-400 font-medium">Queries Asked</span>
                </div>
                <div className="text-2xl font-bold text-white">{stats.total_queries}</div>
              </div>

              {/* Stat Card 3 */}
              <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-2">
                  <Zap size={14} className="text-amber-400" />
                  <span className="text-xs text-zinc-400 font-medium">Avg Faithfulness</span>
                </div>
                <div className="text-2xl font-bold text-white">{(stats.avg_faithfulness * 100).toFixed(1)}%</div>
              </div>

              {/* Stat Card 4 */}
              <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp size={14} className="text-emerald-400" />
                  <span className="text-xs text-zinc-400 font-medium">Citation Accuracy</span>
                </div>
                <div className="text-2xl font-bold text-white">{(stats.avg_citation_accuracy * 100).toFixed(1)}%</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-sm text-zinc-500 py-6 border border-white/5 rounded-xl border-dashed">
              Failed to load statistics
            </div>
          )}

          <div className="mt-6 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
            <div className="flex items-start gap-3">
              <Clock size={16} className="text-indigo-400 mt-0.5 shrink-0" />
              <p className="text-xs text-indigo-200/70 leading-relaxed">
                Your queries are processed by the RAG orchestration engine using semantic cache, dense retrieval, and cross-encoder reranking. You have an overall fallback rate of <strong className="text-indigo-300 font-medium">{((stats?.fallback_rate || 0) * 100).toFixed(1)}%</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 bg-zinc-950/80 flex justify-end">
          <button
            onClick={() => {
              useChatStore.getState().logout();
              onClose();
            }}
            className="px-4 py-2 rounded-lg text-sm font-medium text-rose-400 hover:text-white hover:bg-rose-500 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};
