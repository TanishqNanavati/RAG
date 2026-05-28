// API Service Layer for RAG system

const API_BASE_URL = "http://localhost:8000/api/v1"; // Update to match backend port

export interface QueryResponse {
  query: string;
  session_id: string | null;
  answer: string;
  citations: Record<
    string,
    {
      chunk_id: string;
      text: string;
    }
  >;
  strategy_used: string;
  scores: {
    faithfulness: number;
    citation_correctness: number;
  };
  retrieval_confidence: {
    score: number | null;
    quality: string | null;
  };
  metadata: {
    retries: number;
    selected_strategy: string;
    latencies: {
      pipeline_ms: number;
      generation_ms: number;
      evaluation_ms: number;
      total_ms: number;
    };
    retrieval_filtered: boolean;
    filter_reason: string | null;
  };
  is_cached: boolean;
}

export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
  // Metadata for RAG visualization
  metadata?: QueryResponse;
}

export const api = {
  // Helper to get headers
  getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    const token = localStorage.getItem("token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    // Guest session ID
    let guestSession = localStorage.getItem("guest_session_id");
    if (!guestSession) {
      guestSession = "guest_" + Math.random().toString(36).substring(2, 15);
      localStorage.setItem("guest_session_id", guestSession);
    }
    headers["X-Session-ID"] = guestSession;
    
    return headers;
  },

  async login(username: string, password: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Login failed");
    }
    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    return data;
  },

  async register(username: string, password: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Registration failed");
    }
    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    return data;
  },

  async getMe(): Promise<{ id: number, username: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Not authenticated");
    }
    return response.json();
  },

  /**
   * Run RAG Query
   */
  async query(queryText: string, sessionId?: string | null, strategy?: string): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        query: queryText,
        session_id: sessionId || null,
        strategy: strategy || "auto"
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Query execution failed.");
    }

    return response.json();
  },

  /**
   * Fetch Conversation History
   */
  async getHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await fetch(`${API_BASE_URL}/history/${sessionId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to load chat history.");
    }
    const data = await response.json();
    return data.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      created_at: msg.created_at,
    }));
  },

  /**
   * Fetch All User Sessions
   */
  async getSessions(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to load chat sessions.");
    }
    return response.json();
  },

  /**
   * Fetch User Stats
   */
  async getUserStats(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/me/stats`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to load user stats.");
    }
    return response.json();
  },

  /**
   * Rename User Session
   */
  async renameSession(sessionId: string, title: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: JSON.stringify({ title }),
    });
    if (!response.ok) {
      throw new Error("Failed to rename chat session.");
    }
    return response.json();
  },

  /**
   * Ingest and Index Document
   * We use the Hybrid indexing endpoint to add it to both stores!
   */
  async uploadDocument(file: File, onProgress?: (pct: number) => void): Promise<{ status: string; chunks_indexed: number }> {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    return new Promise((resolve, reject) => {
      // Actually we should hit /ingest, because orchestration_routes /ingest is what we modified
      // Let's use /ingest endpoint for documents
      xhr.open("POST", `${API_BASE_URL}/ingest`, true);
      
      const token = localStorage.getItem("token");
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      let guestSession = localStorage.getItem("guest_session_id");
      if (guestSession) {
        xhr.setRequestHeader("X-Session-ID", guestSession);
      }

      // Track progress
      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            onProgress(percentComplete);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const res = JSON.parse(xhr.responseText);
            // It returns num_chunks, adjust to chunks_indexed
            resolve({ status: res.status, chunks_indexed: res.num_chunks });
          } catch (e) {
            reject(new Error("Invalid server response."));
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || "Document upload/indexing failed."));
          } catch (e) {
            reject(new Error("Server error during ingestion."));
          }
        }
      };

      xhr.onerror = () => reject(new Error("Network error during document upload."));
      xhr.send(formData);
    });
  },
};
