import React from "react";
import { useChatStore } from "../store/useChatStore";
import { X, Settings, Sliders, Database, Layers } from "lucide-react";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ isOpen, onClose }) => {
  const {
    model,
    temperature,
    retrievalStrategy,
    topK,
    rerankerEnabled,
    updateSettings
  } = useChatStore();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-zinc-900 border border-border rounded-2xl flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between bg-zinc-950/20">
          <div className="flex items-center gap-2">
            <Settings className="text-zinc-400" size={16} />
            <span className="text-xs font-bold text-zinc-200">System Pipeline Parameters</span>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200"
          >
            <X size={15} />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-5 overflow-y-auto">
          
          {/* LLM Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-500 uppercase tracking-wide">
              <Sliders size={12} className="text-blue-500" />
              <span>Generation Agent (LLM)</span>
            </div>
            
            <div className="space-y-2.5">
              <div className="space-y-1">
                <label className="text-[10px] text-zinc-400">Target Foundation Model</label>
                <select 
                  value={model}
                  onChange={(e) => updateSettings({ model: e.target.value })}
                  className="w-full text-xs bg-zinc-950 border border-border rounded-lg p-2 focus:outline-none focus:border-zinc-700 text-zinc-200"
                >
                  <option value="gemini-1.5-flash">Gemini 1.5 Flash (Default)</option>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro (Complex Reasoning)</option>
                  <option value="gpt-4o-mini">GPT-4o Mini (Speed)</option>
                  <option value="gpt-4o">GPT-4o (Premium Precision)</option>
                </select>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-zinc-400">
                  <span>Temperature</span>
                  <span className="font-mono text-zinc-300">{temperature}</span>
                </div>
                <input 
                  type="range" 
                  min="0.0" 
                  max="1.0" 
                  step="0.05"
                  value={temperature}
                  onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
                  className="w-full accent-blue-500 h-1 bg-zinc-850 rounded-lg cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Retrieval Section */}
          <div className="space-y-3 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-500 uppercase tracking-wide">
              <Database size={12} className="text-amber-500" />
              <span>Search & Index (Retriever)</span>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] text-zinc-400">Retrieval Routing Strategy</label>
                <select 
                  value={retrievalStrategy}
                  onChange={(e) => updateSettings({ retrievalStrategy: e.target.value as any })}
                  className="w-full text-xs bg-zinc-950 border border-border rounded-lg p-2 focus:outline-none focus:border-zinc-700 text-zinc-200"
                >
                  <option value="hybrid">Hybrid (Dense Cosine + Sparse BM25)</option>
                  <option value="dense">Dense Semantic (FAISS Vector Store)</option>
                  <option value="bm25">Sparse Keyword (Okapi BM25 Index)</option>
                </select>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-zinc-400">
                  <span>Recall Size (Top-k Chunks)</span>
                  <span className="font-mono text-zinc-300">{topK}</span>
                </div>
                <input 
                  type="range" 
                  min="3" 
                  max="20" 
                  step="1"
                  value={topK}
                  onChange={(e) => updateSettings({ topK: parseInt(e.target.value) })}
                  className="w-full accent-blue-500 h-1 bg-zinc-850 rounded-lg cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Reranker Section */}
          <div className="space-y-3 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-500 uppercase tracking-wide">
              <Layers size={12} className="text-emerald-500" />
              <span>Stage-2 Cross-Encoder</span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 pr-4">
                <div className="text-[11px] font-medium text-zinc-200">Enable Re-ranking</div>
                <div className="text-[9px] text-zinc-500 leading-normal">
                  Reranks top retrieved chunks using a neural Cross-Encoder model to maximize precision.
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input 
                  type="checkbox" 
                  checked={rerankerEnabled} 
                  onChange={(e) => updateSettings({ rerankerEnabled: e.target.checked })}
                  className="sr-only peer" 
                />
                <div className="w-9 h-5 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-zinc-400 after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600 peer-checked:after:bg-white peer-checked:after:border-blue-600"></div>
              </label>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border bg-zinc-950/20 flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs font-semibold rounded-lg text-white transition-colors"
          >
            Save Parameters
          </button>
        </div>
      </div>
    </div>
  );
};
