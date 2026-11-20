import type {
  Agent, AgentSettings, Article, Channel, Conversation, ConversationDetail, EngineInfo, Flow, Message,
  Overview, Persona, Source, Ticket,
} from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* corpo vazio */
    }
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  health: () => request<{ status: string; ai_provider: string; ai_model: string }>("/api/health"),

  conversations: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as [string, string][],
    );
    return request<{ items: Conversation[]; counts: Record<string, number> }>(`/api/conversations?${qs}`);
  },
  conversation: (id: number) => request<ConversationDetail>(`/api/conversations/${id}`),
  sendAgentMessage: (id: number, agentId: number, content: string) =>
    post<Message>(`/api/conversations/${id}/messages`, { agent_id: agentId, content }),
  assign: (id: number, agentId: number) => post<Conversation>(`/api/conversations/${id}/assign`, { agent_id: agentId }),
  resolve: (id: number) => post<Conversation>(`/api/conversations/${id}/resolve`),
  returnToBot: (id: number) => post<Conversation>(`/api/conversations/${id}/return-to-bot`),
  markRead: (id: number) => post(`/api/conversations/${id}/read`),
  suggest: (id: number) =>
    post<{ text: string; sources: Source[]; provider: string }>(`/api/conversations/${id}/copilot/suggest`),
  summarize: (id: number) => post<{ summary: string }>(`/api/conversations/${id}/copilot/summarize`),

  inbound: (channel: Channel, body: Record<string, unknown>) =>
    post<{ conversation_id: number; reply: Message | null }>(`/api/channels/${channel}/inbound`, body),

  overview: (days: number) => request<Overview>(`/api/analytics/overview?days=${days}`),

  articles: () => request<Article[]>("/api/knowledge"),
  createArticle: (a: Partial<Article>) => post<Article>("/api/knowledge", a),
  updateArticle: (id: number, a: Partial<Article>) =>
    request<Article>(`/api/knowledge/${id}`, { method: "PUT", body: JSON.stringify(a) }),
  deleteArticle: (id: number) => request<void>(`/api/knowledge/${id}`, { method: "DELETE" }),
  searchKnowledge: (query: string) =>
    post<{ query: string; took_ms: number; chunks_indexed: number; results: Source[] }>("/api/knowledge/search", {
      query,
    }),

  flows: () => request<Flow[]>("/api/flows"),
  toggleFlow: (id: number, active: boolean) =>
    request(`/api/flows/${id}`, { method: "PATCH", body: JSON.stringify({ active }) }),

  settings: () => request<{ agent: AgentSettings; engine: EngineInfo }>("/api/settings"),
  saveSettings: (patch: Partial<AgentSettings>) =>
    request<{ agent: AgentSettings }>("/api/settings", { method: "PATCH", body: JSON.stringify(patch) }),

  agents: () => request<Agent[]>("/api/agents"),
  tickets: () => request<Ticket[]>("/api/tickets"),
  personas: () => request<Persona[]>("/api/demo/personas"),
  resetDemo: () => post("/api/demo/reset"),
};
