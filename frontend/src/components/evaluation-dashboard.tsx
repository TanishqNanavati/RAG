import React from "react";
import { X, Award, Zap, Database, BarChart3, AlertTriangle } from "lucide-react";
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, 
  Tooltip, PieChart, Pie, Cell, BarChart, Bar, Legend 
} from "recharts";

interface EvaluationDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

// Mock statistics for the RAG evaluation Dashboard
const latencyData = [
  { time: "10:00", search: 80, generation: 210, evaluation: 150 },
  { time: "11:00", search: 110, generation: 320, evaluation: 180 },
  { time: "12:00", search: 90, generation: 190, evaluation: 140 },
  { time: "13:00", search: 140, generation: 410, evaluation: 210 },
  { time: "14:00", search: 100, generation: 220, evaluation: 160 },
  { time: "15:00", search: 95, generation: 180, evaluation: 130 },
  { time: "16:00", search: 115, generation: 250, evaluation: 175 },
];

const cacheData = [
  { name: "Cache Hits", value: 342, color: "#10b981" },
  { name: "Cache Misses", value: 158, color: "#f59e0b" },
];

const strategyDistribution = [
  { name: "Hybrid Search", count: 280 },
  { name: "Dense semantic", count: 170 },
  { name: "BM25 keyword", count: 50 },
];

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
      <div className="w-full max-w-4xl h-[85vh] bg-zinc-900 border border-border rounded-2xl flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between bg-zinc-950/20">
          <div className="flex items-center gap-2">
            <BarChart3 className="text-blue-500" size={18} />
            <span className="text-sm font-bold text-zinc-100">RAG Analytics & Evaluation Dashboard</span>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200"
          >
            <X size={16} />
          </button>
        </div>

        {/* Dashboard Grid */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Card Overview Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            <div className="p-3 bg-zinc-950 border border-border rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-bold uppercase">
                <Award size={12} className="text-emerald-500" />
                <span>Avg Faithfulness</span>
              </div>
              <div className="text-xl font-bold text-zinc-100 font-mono">0.962</div>
              <div className="text-[9px] text-emerald-500">+1.2% from yesterday</div>
            </div>

            <div className="p-3 bg-zinc-950 border border-border rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-bold uppercase">
                <AlertTriangle size={12} className="text-rose-500" />
                <span>Hallucination Rate</span>
              </div>
              <div className="text-xl font-bold text-zinc-100 font-mono">2.4%</div>
              <div className="text-[9px] text-rose-500">-0.8% decrease (improved)</div>
            </div>

            <div className="p-3 bg-zinc-950 border border-border rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-bold uppercase">
                <Database size={12} className="text-blue-500" />
                <span>Cache Hit Rate</span>
              </div>
              <div className="text-xl font-bold text-zinc-100 font-mono">68.4%</div>
              <div className="text-[9px] text-blue-500">500 total cached calls</div>
            </div>

            <div className="p-3 bg-zinc-950 border border-border rounded-xl space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-bold uppercase">
                <Zap size={12} className="text-amber-500" />
                <span>Avg Latency</span>
              </div>
              <div className="text-xl font-bold text-zinc-100 font-mono">482ms</div>
              <div className="text-[9px] text-amber-500">Skip rate: 10% on evaluation</div>
            </div>

          </div>

          {/* Charts Layout */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Latency Area Chart */}
            <div className="md:col-span-2 p-4 bg-zinc-950 border border-border rounded-xl space-y-3">
              <div className="text-xs font-bold text-zinc-300">RAG Latency Breakdown (Search vs Gen vs Eval)</div>
              <div className="h-48 w-full text-[9px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={latencyData}>
                    <XAxis dataKey="time" stroke="#52525b" />
                    <YAxis stroke="#52525b" unit="ms" />
                    <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }} />
                    <Legend />
                    <Area type="monotone" dataKey="search" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="Search (FAISS/BM25)" />
                    <Area type="monotone" dataKey="generation" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} name="LLM Generation" />
                    <Area type="monotone" dataKey="evaluation" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} name="Self Evaluation" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Cache Pie Chart */}
            <div className="p-4 bg-zinc-950 border border-border rounded-xl space-y-3">
              <div className="text-xs font-bold text-zinc-300">Redis Cache Hit Distribution</div>
              <div className="h-48 w-full flex flex-col justify-center items-center">
                <ResponsiveContainer width="100%" height="80%">
                  <PieChart>
                    <Pie
                      data={cacheData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={60}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {cacheData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex gap-4 text-[10px] text-zinc-400 mt-2">
                  <div className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                    <span>Hits: 342</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                    <span>Misses: 158</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Distribution Bar Chart */}
            <div className="md:col-span-3 p-4 bg-zinc-950 border border-border rounded-xl space-y-3">
              <div className="text-xs font-bold text-zinc-300">Orchestrator Search Strategy Distribution</div>
              <div className="h-40 w-full text-[9px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={strategyDistribution} layout="vertical">
                    <XAxis type="number" stroke="#52525b" />
                    <YAxis dataKey="name" type="category" stroke="#52525b" width={90} />
                    <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Queries Routed" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
};
