import type { Channel, ConvStatus, Priority } from "./types";

/** A API devolve datas UTC sem fuso — normaliza para Date local. */
export const toDate = (iso: string) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);

export function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - toDate(iso).getTime()) / 1000);
  if (s < 45) return "agora";
  if (s < 3600) return `${Math.round(s / 60)} min`;
  if (s < 86400) return `${Math.round(s / 3600)} h`;
  if (s < 86400 * 7) return `${Math.round(s / 86400)} d`;
  return toDate(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

/** Frase relativa: "agora", "há 5 min", "em 15 de out." */
export function since(iso: string): string {
  const rel = timeAgo(iso);
  if (rel === "agora") return rel;
  return /\d+ (min|h|d)$/.test(rel) ? `há ${rel}` : `em ${rel}`;
}

export const clock = (iso: string) => toDate(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
export const shortDate = (iso: string) =>
  toDate(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });

export const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
export const num = (v: number, digits = 0) =>
  v.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export function duration(seconds: number): string {
  if (seconds < 60) return `${num(seconds, seconds < 10 ? 1 : 0)}s`;
  const m = Math.floor(seconds / 60);
  return `${m}min ${Math.round(seconds % 60)}s`;
}

export const initials = (name: string) =>
  name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");

/** Paleta categórica validada (CVD) — mesma cor do canal em ícones e gráficos. */
export const CHANNELS: Record<Channel, { label: string; color: string; soft: string }> = {
  webchat: { label: "Webchat", color: "#2a78d6", soft: "#e8f1fc" },
  instagram: { label: "Instagram", color: "#eb6834", soft: "#fdeee7" },
  whatsapp: { label: "WhatsApp", color: "#1baf7a", soft: "#e4f6ef" },
  email: { label: "E-mail", color: "#eda100", soft: "#fdf3dc" },
};
export const CHANNEL_ORDER: Channel[] = ["webchat", "instagram", "whatsapp", "email"];

export const STATUS: Record<ConvStatus, { label: string; cls: string }> = {
  bot: { label: "IA atendendo", cls: "bg-violet-50 text-violet-700 ring-violet-200" },
  waiting: { label: "Na fila", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
  human: { label: "Com humano", cls: "bg-sky-50 text-sky-700 ring-sky-200" },
  resolved: { label: "Encerrada", cls: "bg-slate-100 text-slate-600 ring-slate-200" },
};

export const PRIORITY: Record<Priority, { label: string; cls: string } | null> = {
  low: null,
  normal: null,
  high: { label: "Alta", cls: "bg-orange-50 text-orange-700 ring-orange-200" },
  urgent: { label: "Urgente", cls: "bg-red-50 text-red-700 ring-red-200" },
};

export function sentimentInfo(v: number) {
  if (v <= -0.25) return { label: "Negativo", emoji: "😟", cls: "text-red-600" };
  if (v >= 0.25) return { label: "Positivo", emoji: "😊", cls: "text-emerald-600" };
  return { label: "Neutro", emoji: "😐", cls: "text-slate-500" };
}

export const PROVIDER_LABEL: Record<string, string> = {
  anthropic: "Claude",
  openai: "OpenAI",
  offline: "Motor local",
  guardrail: "Guardrail",
};

export const TOOL_LABEL: Record<string, string> = {
  buscar_base_conhecimento: "Base de conhecimento",
  consultar_pedido: "Consulta de pedido",
  consultar_produto: "Catálogo de produtos",
  abrir_solicitacao: "Abertura de protocolo",
  transferir_para_humano: "Transferência p/ humano",
};

/** Formatação leve estilo WhatsApp: *negrito*, preservando quebras de linha. */
export function richText(text: string): string {
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc.replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>");
}
