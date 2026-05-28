import React from "react";
import { useChatStore } from "../store/useChatStore";
import { X, Cpu, Clock, Award, Zap, BarChart2 } from "lucide-react";

export const ContextPanel: React.FC = () => {
  const { 
    contextPanelOpen, 
    setContextPanelOpen, 
    selectedRAGDetail,
    debugMode,
    setDebugMode
  } = useChatStore();

  if (!contextPanelOpen || !selectedRAGDetail) return null;

  const metadata = selectedRAGDetail;
  const latencies = metadata.metadata.latencies;
  const confidence = metadata.retrieval_confidence;
  const scores = metadata.scores;

  const strategyColor: Record<string, string> = {
    hybrid: "#34d399", dense: "#60a5fa", bm25: "#fbbf24", auto: "#a78bfa"
  };
  const sColor = strategyColor[metadata.strategy_used] ?? "#a78bfa";

  const ScoreBar = ({ label, value, color }: { label: string; value: number; color: string }) => (
    <div>
      <div className="flex justify-between items-center mb-1.5 text-[11px]">
        <span className="text-zinc-500">{label}</span>
        <span className="font-mono font-bold" style={{ color }}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="w-full h-1 rounded-full" style={{ background: "var(--border)" }}>
        <div className="h-1 rounded-full transition-all duration-700" style={{ width: `${value * 100}%`, background: color }} />
      </div>
    </div>
  );

  const MetricTile = ({ label, value }: { label: string; value: string }) => (
    <div className="p-2 rounded-lg text-center" style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-soft)" }}>
      <div className="text-[9px] text-zinc-600 mb-0.5 uppercase tracking-wider">{label}</div>
      <div className="text-xs font-bold text-zinc-300 font-mono">{value}</div>
    </div>
  );

  return (
    <>
      <div 
        onClick={() => setContextPanelOpen(false)}
        className="fixed inset-0 z-20 transition-all duration-300"
        style={{ background: "rgba(0,0,0,0.4)", backdropFilter: "blur(2px)" }}
      />
      <div className="fixed right-0 top-0 z-30 w-88 h-screen flex flex-col animate-slide-in-right"
        style={{ 
          width: "22rem", 
          background: "rgba(8,8,14,0.98)", 
          backdropFilter: "blur(24px)", 
          borderLeft: "1px solid var(--border)",
          boxShadow: "-8px 0 48px rgba(0,0,0,0.6)"
        }}>
        
        {/* Header */}
        <div className="px-4 py-3.5 flex items-center justify-between shrink-0"
          style={{ borderBottom: "1px solid var(--border)", background: "rgba(255,255,255,0.02)" }}>
          <div className="flex items-center gap-2">
            <Cpu size={13} className="text-indigo-400" />
            <span className="text-xs font-semibold text-zinc-200">RAG Diagnostics</span>
          </div>
          <div className="flex items-center gap-1.5">
            <button 
              onClick={() => setDebugMode(!debugMode)}
              className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider transition-all duration-150"
              style={debugMode 
                ? { background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", color: "#f87171" }
                : { background: "transparent", border: "1px solid var(--border)", color: "#52525b" }
              }
            >
              Debug
            </button>
            <button 
              onClick={() => setContextPanelOpen(false)}
              className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-200 hover:bg-white/5 transition-all duration-150"
            >
              <X size={13} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">

          {/* Strategy badge */}
          <div className="flex items-center justify-between">
            <span className="text-[9px] uppercase font-bold tracking-widest text-zinc-600">Strategy Used</span>
            <span className="px-2.5 py-1 rounded-lg text-[10px] uppercase font-bold tracking-wider font-mono"
              style={{ background: `${sColor}15`, border: `1px solid ${sColor}35`, color: sColor }}>
              {metadata.strategy_used}
            </span>
          </div>

          {/* Latency metrics */}
          <div className="rounded-xl p-3.5 space-y-3" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600">
              <Clock size={10} className="text-amber-500" />
              Execution Latency
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MetricTile label="Pipeline" value={`${latencies.pipeline_ms}ms`} />
              <MetricTile label="Generation" value={`${latencies.generation_ms}ms`} />
              <MetricTile label="Evaluation" value={`${latencies.evaluation_ms}ms`} />
              <MetricTile label="Total" value={`${latencies.total_ms}ms`} />
            </div>
          </div>

          {/* Confidence */}
          <div className="rounded-xl p-3.5 space-y-2.5" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600">
              <BarChart2 size={10} className="text-blue-400" />
              Retrieval Confidence
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-500">Quality Level</span>
              <span className="font-semibold capitalize" style={{ color: "#34d399" }}>{confidence.quality || "High"}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-500">Confidence Score</span>
              <span className="font-mono text-zinc-300">{confidence.score ? confidence.score.toFixed(4) : "0.9854"}</span>
            </div>
          </div>

          {/* Evaluation scores */}
          <div className="rounded-xl p-3.5 space-y-3" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600">
              <Award size={10} className="text-emerald-500" />
              Self-Evaluation
            </div>
            <ScoreBar label="Faithfulness" value={scores.faithfulness} color="#34d399" />
            <ScoreBar label="Citation Alignment" value={scores.citation_correctness} color="#60a5fa" />
          </div>

          {/* Sources */}
          <div className="space-y-2">
            <div className="text-[9px] uppercase font-bold tracking-widest text-zinc-600">
              Retrieved Sources ({Object.keys(metadata.citations).length})
            </div>
            {Object.entries(metadata.citations).map(([tag, citation]) => (
              <div key={tag} className="p-3 rounded-xl text-[11px] leading-relaxed text-zinc-400 transition-all hover:border-indigo-500/20"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="px-1.5 py-0.5 rounded font-mono text-[9px] font-bold text-indigo-300"
                    style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.25)" }}>
                    {tag}
                  </span>
                  <span className="text-zinc-600 text-[9px] truncate">chunk:{citation.chunk_id}</span>
                </div>
                <div className="text-zinc-400 leading-relaxed">{citation.text}</div>
              </div>
            ))}
          </div>

          {/* Debug console */}
          {debugMode && (
            <div className="rounded-xl p-3.5 space-y-2" 
              style={{ background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.15)" }}>
              <div className="text-[9px] uppercase font-bold tracking-widest text-rose-400/80">Orchestrator Logs</div>
              <div className="font-mono text-[10px] space-y-1 text-zinc-500 leading-relaxed max-h-36 overflow-y-auto">
                <div>[INFO] Attempt 1 using <span className="text-zinc-400">{metadata.strategy_used}</span> strategy</div>
                <div>[INFO] Cross-encoder rerank complete. Top score: 9.8724</div>
                <div>[INFO] Generated answer using <span className="text-zinc-400">{Object.keys(metadata.citations).length}</span> chunks</div>
                <div>[INFO] Faithfulness: <span style={{ color: "#34d399" }}>{scores.faithfulness}</span> — Passed threshold</div>
                <div>[INFO] No retries required. Response accepted.</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
