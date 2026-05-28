"use client";

import { useEffect, useState } from "react";
import { useChatStore } from "../store/useChatStore";
import { Sidebar } from "../components/sidebar";
import { ChatArea } from "../components/chat-area";
import { ContextPanel } from "../components/context-panel";
import { SettingsDialog } from "../components/settings-dialog";
import { EvaluationDashboard } from "../components/evaluation-dashboard";
import { AuthModal } from "../components/auth-modal";
import { StrategyAnalysis } from "../components/strategy-analysis";

export default function WorkspacePage() {
  const initChat = useChatStore((state) => state.initChat);
  const initAuth = useChatStore((state) => state.initAuth);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Initialize chat sessions and mounted check on mount
  useEffect(() => {
    setMounted(true);
    initAuth().then(() => initChat());
  }, [initChat, initAuth]);

  if (!mounted) {
    return (
      <div className="h-screen w-screen bg-zinc-950 flex flex-col items-center justify-center text-zinc-500 gap-3">
        <div className="w-6 h-6 border-2 border-zinc-700 border-t-blue-500 rounded-full animate-spin"></div>
        <span className="text-xs font-medium tracking-wider">LOADING WORKSPACE...</span>
      </div>
    );
  }

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100">
      {/* 1. Left Sidebar Panel */}
      <Sidebar 
        onOpenSettings={() => setSettingsOpen(true)} 
        onOpenDashboard={() => setDashboardOpen(true)} 
      />

      {/* 2. Center Chat Panel */}
      <ChatArea />

      {/* 3. Right Context Metadata Panel */}
      <ContextPanel />

      {/* Overlays / Modals */}
      <SettingsDialog 
        isOpen={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />

      <EvaluationDashboard 
        isOpen={dashboardOpen} 
        onClose={() => setDashboardOpen(false)} 
      />
      
      <AuthModal />
      <StrategyAnalysis />
    </main>
  );
}
