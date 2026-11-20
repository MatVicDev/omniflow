export type Channel = "whatsapp" | "instagram" | "webchat" | "email";
export type ConvStatus = "bot" | "waiting" | "human" | "resolved";
export type Priority = "low" | "normal" | "high" | "urgent";
export type Sender = "contact" | "bot" | "agent" | "system";

export interface Agent {
  id: number;
  name: string;
  email: string;
  role: string;
  team: string;
  status: "online" | "away" | "offline";
  avatar_color: string;
}

export interface Contact {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  instagram: string | null;
  city: string | null;
  tags: string[];
  lifetime_value: number;
  created_at: string;
}

export interface Conversation {
  id: number;
  channel: Channel;
  status: ConvStatus;
  priority: Priority;
  intent: string | null;
  intent_label: string | null;
  sentiment: number;
  summary: string | null;
  handoff_reason: string | null;
  resolved_by: "ai" | "human" | null;
  csat: number | null;
  unread: number;
  tags: string[];
  first_response_seconds: number | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  contact: Contact;
  agent: Agent | null;
  last_message: { content: string; sender: Sender; created_at: string } | null;
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result: unknown;
  duration_ms: number;
  error: string | null;
}

export interface Source {
  article_id: number;
  title: string;
  category: string;
  text: string;
  score: number;
}

export interface NLU {
  intent: string;
  intent_label: string;
  confidence: number;
  sentiment: number;
  sentiment_label: "positivo" | "neutro" | "negativo";
  entities: Record<string, string>;
  critical: boolean;
  matched: string[];
}

export interface AiTrace {
  kind?: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  confidence?: number;
  nlu?: NLU;
  tool_calls?: ToolCall[];
  sources?: Source[];
  flows?: { key: string; name: string; detail: string }[];
  guardrail?: string | null;
  handoff?: { motivo?: string; prioridade?: string } | null;
  usage?: Record<string, number>;
  fallback_error?: string | null;
  off_hours?: boolean;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender: Sender;
  content: string;
  agent: { id: number; name: string; avatar_color: string } | null;
  meta: AiTrace;
  created_at: string;
}

export interface Order {
  id: number;
  code: string;
  status: string;
  status_label: string;
  total: number;
  items: { sku: string; name: string; qty: number; price: number }[];
  payment_method: string;
  carrier: string | null;
  tracking_code: string | null;
  eta: string | null;
  created_at: string;
}

export interface Ticket {
  id: number;
  protocol: string;
  kind: string;
  description: string;
  order_code: string | null;
  status: string;
  created_by: string;
  conversation_id: number | null;
  created_at: string;
  contact: { id: number; name: string };
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
  contact: Contact;
  orders: Order[];
  tickets: Ticket[];
  previous_conversations: {
    id: number;
    channel: Channel;
    status: ConvStatus;
    intent: string | null;
    created_at: string;
    csat: number | null;
  }[];
}

export interface Article {
  id: number;
  title: string;
  category: string;
  content: string;
  tags: string[];
  active: boolean;
  hits: number;
  updated_at: string;
}

export interface FlowNode {
  id: string;
  type: "trigger" | "condition" | "ai" | "action" | "message" | "handoff" | "end";
  label: string;
  detail: string;
  x: number;
  y: number;
}

export interface Flow {
  id: number;
  key: string;
  name: string;
  description: string;
  trigger: { type: string; label: string };
  nodes: FlowNode[];
  edges: { from: string; to: string; label?: string }[];
  active: boolean;
  runs: number;
  updated_at: string;
}

export interface AgentSettings {
  bot_name: string;
  tone: "amigavel" | "profissional" | "descontraido";
  greeting: string;
  custom_instructions: string;
  handoff_sentiment_threshold: number;
  handoff_after_failures: number;
  auto_resolve_on_thanks: boolean;
  csat_enabled: boolean;
  business_hours: { start: string; end: string; days: number[] };
  timezone: string;
}

export interface EngineInfo {
  provider: string;
  model: string;
  anthropic_configured: boolean;
  openai_configured: boolean;
  whatsapp_configured: boolean;
}

export interface Persona {
  key: string;
  channel: Channel;
  headline: string;
  skills: string[];
  suggestions: string[];
  contact: Contact | null;
}

export interface Overview {
  period_days: number;
  kpis: {
    conversations: number;
    resolved: number;
    ai_resolved: number;
    ai_resolution_rate: number;
    avg_first_response_s: number;
    avg_resolution_min: number;
    csat: number;
    csat_responses: number;
    hours_saved: number;
    cost_saved: number;
  };
  deltas: Record<string, number | null>;
  daily: ({ date: string; ai: number; human: number } & Record<Channel, number>)[];
  channels: { channel: Channel; count: number }[];
  intents: { intent: string; label: string; count: number }[];
  sentiment: { label: string; count: number }[];
  handoff_reasons: { reason: string; count: number }[];
  heatmap: { weekday: number; hour: number; count: number }[];
  team: {
    id: number;
    name: string;
    status: string;
    avatar_color: string;
    conversations: number;
    resolved: number;
    open: number;
    csat: number | null;
  }[];
  live: { bot: number; waiting: number; human: number };
  ai_latency_ms: number | null;
}
