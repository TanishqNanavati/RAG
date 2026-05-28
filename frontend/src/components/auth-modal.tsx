import React, { useState } from "react";
import { X, Lock, User as UserIcon, Loader2, Sparkles } from "lucide-react";
import { useChatStore } from "../store/useChatStore";
import { api } from "../services/api";

export const AuthModal: React.FC = () => {
  const { authModalOpen, setAuthModalOpen, initAuth } = useChatStore();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!authModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isLogin) {
        await api.login(username, password);
      } else {
        await api.register(username, password);
      }
      await initAuth();
      setAuthModalOpen(false);
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(12px)" }}>
      <div className="w-full max-w-sm overflow-hidden animate-slide-up"
        style={{
          background: "rgba(10,10,16,0.98)",
          border: "1px solid var(--border)",
          borderRadius: "20px",
          boxShadow: "0 32px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(99,102,241,0.1)"
        }}>

        {/* Brand top */}
        <div className="pt-7 pb-4 px-6 text-center"
          style={{ borderBottom: "1px solid var(--border)", background: "rgba(255,255,255,0.015)" }}>
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3"
            style={{ 
              background: "linear-gradient(135deg,#3b82f6,#6366f1)",
              boxShadow: "0 8px 24px rgba(99,102,241,0.35)"
            }}>
            <Sparkles size={20} className="text-white" />
          </div>
          <h2 className="text-sm font-bold text-zinc-100 mb-0.5">
            {isLogin ? "Welcome back" : "Create account"}
          </h2>
          <p className="text-[11px] text-zinc-500">
            {isLogin ? "Sign in to your RAG workspace" : "Start your RAG intelligence workspace"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="px-3.5 py-2.5 rounded-xl text-xs text-rose-300 flex items-start gap-2"
              style={{ background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)" }}>
              <X size={12} className="shrink-0 mt-0.5 text-rose-400" />
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Username</label>
            <div className="relative">
              <UserIcon size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full pl-9 pr-3 py-2.5 rounded-xl text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none transition-all"
                style={{ 
                  background: "rgba(255,255,255,0.04)", 
                  border: "1px solid var(--border)",
                  outlineColor: "rgba(99,102,241,0.5)"
                }}
                placeholder="Your username"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Password</label>
            <div className="relative">
              <Lock size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-9 pr-3 py-2.5 rounded-xl text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none transition-all"
                style={{ 
                  background: "rgba(255,255,255,0.04)", 
                  border: "1px solid var(--border)",
                  outlineColor: "rgba(99,102,241,0.5)"
                }}
                placeholder="Your password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold text-white transition-all duration-200 disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
            style={{ 
              background: "linear-gradient(135deg,#3b82f6,#6366f1)",
              boxShadow: "0 6px 20px rgba(99,102,241,0.35)"
            }}
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : null}
            {isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>

        <div className="pb-5 text-center" style={{ borderTop: "1px solid var(--border)" }}>
          <button
            onClick={() => { setIsLogin(!isLogin); setError(""); }}
            className="text-[11px] transition-colors mt-4"
            style={{ color: "#818cf8" }}
          >
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <span className="font-bold hover:text-indigo-300">
              {isLogin ? "Sign up" : "Sign in"}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
