import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useChatStore } from "../store/useChatStore";
import { X, Activity, Clock, Zap, TrendingUp } from "lucide-react";

const PALETTE = ["#6366f1", "#34d399", "#f59e0b", "#60a5fa"];

export const StrategyAnalysis: React.FC = () => {
  const { strategyAnalysisOpen, setStrategyAnalysisOpen, selectedRAGDetail } = useChatStore();

  if (!strategyAnalysisOpen || !selectedRAGDetail) return null;

  const latencies = selectedRAGDetail.metadata.latencies;
  const metricsData = [
    { name: "Generation",  value: latencies.generation_ms },
    { name: "Evaluation",  value: latencies.evaluation_ms },
    { name: "Pipeline",    value: latencies.pipeline_ms   },
  ];
  const scoresData = [
    { name: "Faithfulness",       value: selectedRAGDetail.scores.faithfulness * 100 },
    { name: "Citation Accuracy",  value: selectedRAGDetail.scores.citation_correctness * 100 },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="px-3 py-2 rounded-xl text-xs" 
          style={{ background: "#0e0e18", border: "1px solid #1f1f30", color: "#e4e4f0" }}>
          <span className="font-bold" style={{ color: payload[0].payload.fill ?? payload[0].fill }}>
            {payload[0].name}
          </span>
          <span className="ml-2 font-mono text-zinc-400">{payload[0].value}{payload[0].name?.includes("%") ? "%" : ""}</span>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(12px)" }}>
      <div className="w-full max-w-xl overflow-hidden flex flex-col animate-slide-up"
        style={{
          maxHeight: "85vh",
          background: "rgba(8,8,14,0.98)",
          border: "1px solid var(--border)",
          borderRadius: "20px",
          boxShadow: "0 32px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(99,102,241,0.1)"
        }}>

        {/* Header */}
        <div className="px-5 py-4 flex items-center justify-between shrink-0"
          style={{ borderBottom: "1px solid var(--border)", background: "rgba(255,255,255,0.02)" }}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.25)" }}>
              <Activity size={15} className="text-indigo-400" />
            </div>
            <div>
              <div className="text-sm font-bold text-zinc-100">Strategy Analysis</div>
              <div className="text-[10px] text-zinc-600">Performance breakdown for this query</div>
            </div>
          </div>
          <button 
            onClick={() => setStrategyAnalysisOpen(false)}
            className="p-2 rounded-xl text-zinc-600 hover:text-zinc-200 hover:bg-white/5 transition-all duration-150"
          >
            <X size={14} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          
          {/* Stats pills */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total Time",    value: `${latencies.total_ms}ms`,    color: "#a78bfa", icon: Clock },
              { label: "Strategy",      value: selectedRAGDetail.strategy_used.toUpperCase(), color: "#34d399", icon: TrendingUp },
              { label: "Faithfulness",  value: `${(selectedRAGDetail.scores.faithfulness * 100).toFixed(0)}%`, color: "#fbbf24", icon: Zap },
            ].map(({ label, value, color, icon: Icon }) => (
              <div key={label} className="p-3 rounded-xl text-center transition-all"
                style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
                <Icon size={12} className="mx-auto mb-1.5" style={{ color }} />
                <div className="text-xs font-bold font-mono" style={{ color }}>{value}</div>
                <div className="text-[9px] uppercase tracking-wider text-zinc-600 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-4">
            {/* Latency pie */}
            <div className="p-4 rounded-xl" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600 mb-4">
                <Clock size={9} className="text-amber-500" />
                Execution Time
              </div>
              <div style={{ height: "140px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={metricsData} cx="50%" cy="50%" innerRadius={35} outerRadius={58} paddingAngle={3} dataKey="value">
                      {metricsData.map((_, i) => (
                        <Cell key={i} fill={PALETTE[i % PALETTE.length]} strokeWidth={0} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {metricsData.map((item, i) => (
                  <div key={item.name} className="flex items-center justify-between text-[10px]">
                    <span className="flex items-center gap-1.5 text-zinc-400">
                      <span className="w-2 h-2 rounded-sm" style={{ background: PALETTE[i] }} />
                      {item.name}
                    </span>
                    <span className="font-mono text-zinc-500">{item.value}ms</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Scores pie */}
            <div className="p-4 rounded-xl" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold tracking-widest text-zinc-600 mb-4">
                <Zap size={9} className="text-emerald-500" />
                Eval Scores
              </div>
              <div style={{ height: "140px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={scoresData} cx="50%" cy="50%" innerRadius={35} outerRadius={58} paddingAngle={3} dataKey="value">
                      {scoresData.map((_, i) => (
                        <Cell key={i} fill={PALETTE[(i + 2) % PALETTE.length]} strokeWidth={0} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} formatter={(v: number) => [`${v.toFixed(1)}%`]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {scoresData.map((item, i) => (
                  <div key={item.name} className="flex items-center justify-between text-[10px]">
                    <span className="flex items-center gap-1.5 text-zinc-400">
                      <span className="w-2 h-2 rounded-sm" style={{ background: PALETTE[(i + 2) % PALETTE.length] }} />
                      {item.name}
                    </span>
                    <span className="font-mono text-zinc-500">{item.value.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Summary callout */}
          <div className="px-4 py-3.5 rounded-xl"
            style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.18)" }}>
            <div className="text-[9px] uppercase font-bold tracking-widest text-indigo-400/70 mb-1.5">Query Summary</div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              Executed via <span className="font-bold capitalize" style={{ color: "#a78bfa" }}>{selectedRAGDetail.strategy_used}</span> strategy 
              in <span className="font-mono font-bold text-emerald-400">{latencies.total_ms}ms</span> total. 
              Faithfulness score is <span className="font-mono font-bold text-amber-400">{(selectedRAGDetail.scores.faithfulness * 100).toFixed(1)}%</span> 
              {" "}and citation accuracy is <span className="font-mono font-bold text-blue-400">{(selectedRAGDetail.scores.citation_correctness * 100).toFixed(1)}%</span>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
