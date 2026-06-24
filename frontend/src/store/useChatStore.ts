import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ChatMessage, api, QueryResponse } from "../services/api";

export interface ChatSession {
  id: string;
  title: string;
  isCustomTitle?: boolean;
  created_at: string;
}

export interface DocumentInfo {
  id: string;
  name: string;
  status: "uploading" | "analyzing" | "indexed" | "error";
  chunksCount?: number;
  size?: string;
  uploadedAt: string;
}

interface User {
  id: number;
  username: string;
  created_at?: string;
}

interface ChatState {
  user: User | null;
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  loading: boolean;
  
  // Document uploads
  documents: DocumentInfo[];
  activeDocument: DocumentInfo | null;
  uploadProgress: number;
  uploadStatus: "idle" | "uploading" | "analyzing" | "done" | "error";

  // Panel layout toggles
  sidebarOpen: boolean;
  contextPanelOpen: boolean;
  authModalOpen: boolean;
  strategyAnalysisOpen: boolean;
  selectedRAGDetail: QueryResponse | null;
  debugMode: boolean;

  // Settings
  model: string;
  temperature: number;
  retrievalStrategy: "hybrid" | "dense" | "bm25";
  topK: number;
  rerankerEnabled: boolean;
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  setContextPanelOpen: (open: boolean) => void;
  setAuthModalOpen: (open: boolean) => void;
  setStrategyAnalysisOpen: (open: boolean) => void;
  setSelectedRAGDetail: (detail: QueryResponse | null) => void;
  setDebugMode: (debug: boolean) => void;
  updateSettings: (settings: Partial<Pick<ChatState, "model" | "temperature" | "retrievalStrategy" | "topK" | "rerankerEnabled">>) => void;
  
  initAuth: () => Promise<void>;
  logout: () => void;
  initChat: () => Promise<void>;
  createSession: (title?: string) => string;
  selectSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string, isCustom?: boolean) => void;
  
  sendMessage: (text: string, strategy?: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      user: null,
      sessions: [],
      currentSessionId: null,
      messages: [],
      loading: false,
      
      documents: [],
      activeDocument: null,
      uploadProgress: 0,
      uploadStatus: "idle",
      
      sidebarOpen: true,
      contextPanelOpen: false,
      authModalOpen: false,
      strategyAnalysisOpen: false,
      selectedRAGDetail: null,
      debugMode: false,
      
      model: "gemini-1.5-flash",
      temperature: 0.2,
      retrievalStrategy: "hybrid",
      topK: 10,
      rerankerEnabled: true,
      
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      setContextPanelOpen: (contextPanelOpen) => set({ contextPanelOpen }),
      setAuthModalOpen: (authModalOpen) => set({ authModalOpen }),
      setStrategyAnalysisOpen: (strategyAnalysisOpen) => set({ strategyAnalysisOpen }),
      setSelectedRAGDetail: (selectedRAGDetail) => set({ selectedRAGDetail, contextPanelOpen: !!selectedRAGDetail }),
      setDebugMode: (debugMode) => set({ debugMode }),
      
      updateSettings: (newSettings) => set(newSettings),

      initAuth: async () => {
        try {
          const user = await api.getMe();
          set({ user });
          
          try {
            const sessions = await api.getSessions();
            if (sessions && sessions.length > 0) {
              set({ 
                sessions: sessions.map((s: any) => ({
                  id: s.id,
                  title: s.title || `Chat ${s.id.substring(0,8)}`,
                  isCustomTitle: !!s.title,
                  created_at: s.created_at
                })),
                currentSessionId: sessions[0].id
              });
              await get().selectSession(sessions[0].id);
            }
          } catch (e) {
            console.error("Failed to fetch sessions", e);
          }
        } catch {
          set({ user: null });
        }
      },
      
      logout: () => {
        localStorage.removeItem("token");
        set({ user: null, sessions: [], messages: [], currentSessionId: null });
      },
      
      initChat: async () => {
        const { currentSessionId, selectSession, sessions } = get();
        if (sessions.length === 0) {
          const newId = get().createSession("New Conversation");
          await selectSession(newId);
        } else if (currentSessionId) {
          await selectSession(currentSessionId);
        } else {
          await selectSession(sessions[0].id);
        }
      },
      
      createSession: (title) => {
        const id = "session_" + Math.random().toString(36).substr(2, 9);
        const newSession: ChatSession = {
          id,
          title: title || "New Chat Workspace",
          isCustomTitle: !!title,
          created_at: new Date().toISOString()
        };
        set(state => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: id,
          messages: []
        }));
        return id;
      },
      
      selectSession: async (id) => {
        set({ currentSessionId: id, loading: true });
        try {
          const history = await api.getHistory(id);
          set({ messages: history, loading: false });
        } catch (e) {
          // If session doesn't exist or DB is empty
          set({ messages: [], loading: false });
        }
      },
      
      deleteSession: async (id) => {
        try {
          await api.deleteSession(id);
        } catch (e) {
          console.error("Failed to delete session on backend", e);
        }
        set(state => {
          const newSessions = state.sessions.filter(s => s.id !== id);
          let newActive = state.currentSessionId;
          if (state.currentSessionId === id) {
            newActive = newSessions.length > 0 ? newSessions[0].id : null;
          }
          return {
            sessions: newSessions,
            currentSessionId: newActive,
            messages: []
          };
        });
        const { currentSessionId } = get();
        if (currentSessionId) {
          get().selectSession(currentSessionId);
        }
      },
      
      renameSession: (id, title, isCustom = true) => {
        set(state => ({
          sessions: state.sessions.map(s => 
            s.id === id ? { ...s, title, isCustomTitle: isCustom } : s
          )
        }));
        
        // Background sync to backend
        const { user } = get();
        if (user) {
          api.renameSession(id, title).catch(e => console.error("Failed to rename session on backend", e));
        }
      },
      
      sendMessage: async (text: string, strategy?: string) => {
        const { currentSessionId, messages } = get();
        if (!currentSessionId) return;
        
        const userMsg: ChatMessage = {
          id: "msg_" + Date.now(),
          role: "user",
          content: text
        };
        
        set({ 
          messages: [...messages, userMsg],
          loading: true 
        });
        
        try {
          const result = await api.query(text, currentSessionId, strategy);
          
          const assistantMsg: ChatMessage = {
            id: "msg_" + (Date.now() + 1),
            role: "assistant",
            content: result.answer,
            metadata: result
          };
          
          set(state => ({
            messages: [...state.messages, assistantMsg],
            selectedRAGDetail: result,
            loading: false
          }));

          // Rename session automatically based on first query
          set(state => {
            const curSession = state.sessions.find(s => s.id === currentSessionId);
            if (curSession && curSession.title === "New Conversation") {
              return {
                sessions: state.sessions.map(s => 
                  s.id === currentSessionId 
                    ? { ...s, title: text.length > 30 ? text.substring(0, 30) + "..." : text } 
                    : s
                )
              };
            }
            return {};
          });

        } catch (error: any) {
          const errMsg: ChatMessage = {
            id: "msg_" + (Date.now() + 1),
            role: "system",
            content: `Error: ${error.message || "Failed to fetch response."}`
          };
          set(state => ({
            messages: [...state.messages, errMsg],
            loading: false
          }));
        }
      },
      
      uploadFile: async (file: File) => {
        const { currentSessionId, documents } = get();
        if (!currentSessionId) return;

        const docId = "doc_" + Math.random().toString(36).substr(2, 9);
        const newDoc: DocumentInfo = {
          id: docId,
          name: file.name,
          status: "uploading",
          size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          uploadedAt: new Date().toLocaleTimeString()
        };

        // Add file to workspace docs list
        set(state => ({
          documents: [newDoc, ...state.documents],
          uploadStatus: "uploading",
          uploadProgress: 10
        }));

        // Rename session to document name if it's not a custom title
        set(state => {
          const curSession = state.sessions.find(s => s.id === currentSessionId);
          if (curSession && !curSession.isCustomTitle) {
             return {
               sessions: state.sessions.map(s => 
                 s.id === currentSessionId 
                   ? { ...s, title: file.name.substring(0, 30) + (file.name.length > 30 ? "..." : ""), isCustomTitle: false } 
                   : s
               )
             };
          }
          return {};
        });

        // Append "Analyzing" chat feedback message
        const analyzingMsg: ChatMessage = {
          id: "anal_" + Date.now(),
          role: "system",
          content: `🔄 Analyzing document "${file.name}"... Parsing content, creating chunks, and saving embeddings to memory database.`
        };
        set(state => ({ messages: [...state.messages, analyzingMsg] }));

        try {
          // Trigger actual indexing
          set({ uploadStatus: "analyzing", uploadProgress: 50 });
          const res = await api.uploadDocument(file, (pct) => {
            set({ uploadProgress: 30 + Math.round(pct * 0.6) }); // Scale progress 30-90%
          });

          set(state => ({
            uploadStatus: "done",
            uploadProgress: 100,
            documents: state.documents.map(d => 
              d.id === docId 
                ? { ...d, status: "indexed", chunksCount: res.chunks_indexed } 
                : d
            )
          }));

          // Append "Analyzing Done" message
          const doneMsg: ChatMessage = {
            id: "done_" + Date.now(),
            role: "system",
            content: `✅ Analyzing done! ${res.chunks_indexed} semantic chunks successfully indexed in FAISS vector database. You can now ask questions related to "${file.name}"!`
          };
          set(state => ({ messages: [...state.messages, doneMsg] }));

        } catch (error: any) {
          set(state => ({
            uploadStatus: "error",
            documents: state.documents.map(d => 
              d.id === docId 
                ? { ...d, status: "error" } 
                : d
            )
          }));

          const errorMsg: ChatMessage = {
            id: "error_" + Date.now(),
            role: "system",
            content: `❌ Ingestion failed for "${file.name}": ${error.message || "Failed to process document."}`
          };
          set(state => ({ messages: [...state.messages, errorMsg] }));
        } finally {
          setTimeout(() => {
            set({ uploadStatus: "idle", uploadProgress: 0 });
          }, 3000);
        }
      }
    }),
    {
      name: "rag-chat-config-store",
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        sidebarOpen: state.sidebarOpen,
        debugMode: state.debugMode,
        model: state.model,
        temperature: state.temperature,
        retrievalStrategy: state.retrievalStrategy,
        topK: state.topK,
        rerankerEnabled: state.rerankerEnabled
      })
    }
  )
);
