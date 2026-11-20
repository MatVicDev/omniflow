import clsx from "clsx";
import {
  ArrowLeftRight, Bot, CheckCheck, ClipboardList, Inbox as InboxIcon, MapPin, Package, RefreshCw, Search,
  SendHorizontal, Sparkles, UserCheck, Wand2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CURRENT_AGENT } from "../App";
import MessageBubble from "../components/MessageBubble";
import {
  Avatar, ChannelIcon, EmptyState, PriorityPill, Spinner, StatusPill, Tag, TypingDots,
} from "../components/ui";
import { api } from "../lib/api";
import { brl, CHANNEL_ORDER, CHANNELS, sentimentInfo, shortDate, timeAgo } from "../lib/format";
import { useEvent } from "../lib/realtime";
import type { Channel, Conversation, ConversationDetail, Message } from "../lib/types";

type Tab = "waiting" | "mine" | "bot" | "open" | "resolved";

const TABS: { key: Tab; label: string }[] = [
  { key: "waiting", label: "Fila" },
  { key: "mine", label: "Comigo" },
  { key: "bot", label: "IA" },
  { key: "open", label: "Abertas" },
  { key: "resolved", label: "Encerradas" },
];

const PRIORITY_RANK = { urgent: 0, high: 1, normal: 2, low: 3 };

function tabParams(tab: Tab) {
  switch (tab) {
    case "mine":
      return { status: "human", assigned_to: CURRENT_AGENT.id };
    case "open":
      return { status: "open" };
    default:
      return { status: tab };
  }
}

function matchesTab(c: Conversation, tab: Tab, channel: Channel | "") {
  if (channel && c.channel !== channel) return false;
  if (tab === "mine") return c.status === "human" && c.agent?.id === CURRENT_AGENT.id;
  if (tab === "open") return c.status !== "resolved";
  return c.status === tab;
}

function sortConvs(list: Conversation[], tab: Tab) {
  return [...list].sort((a, b) => {
    if (tab === "waiting" && a.priority !== b.priority) return PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
    return b.updated_at.localeCompare(a.updated_at);
  });
}

// ─── Lista ───────────────────────────────────────────────────────────────────

function ConversationItem({ c, active, onClick }: { c: Conversation; active: boolean; onClick: () => void }) {
  const senti = sentimentInfo(c.sentiment);
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex w-full gap-3 border-b border-slate-100 px-4 py-3 text-left transition",
        active ? "bg-brand-50/70" : "hover:bg-slate-50",
      )}
    >
      <Avatar name={c.contact.name} channel={c.channel} size={38} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className={clsx("truncate text-sm", c.unread ? "font-semibold text-slate-900" : "font-medium text-slate-700")}>
            {c.contact.name}
          </p>
          <span className="ml-auto shrink-0 text-[11px] text-slate-400">{timeAgo(c.updated_at)}</span>
        </div>
        <p className="mt-0.5 line-clamp-1 text-[13px] text-slate-500">
          {c.last_message?.sender === "bot" && <span className="text-brand-600">IA: </span>}
          {c.last_message?.sender === "agent" && <span className="text-slate-700">Você: </span>}
          {c.last_message?.content.replace(/\*/g, "")}
        </p>
        <div className="mt-1.5 flex items-center gap-1.5">
          <StatusPill status={c.status} />
          <PriorityPill priority={c.priority} />
          {c.intent_label && <span className="truncate text-[11px] text-slate-400">{c.intent_label}</span>}
          <span className="ml-auto" title={`Sentimento ${senti.label}`}>
            {senti.emoji}
          </span>
          {c.unread > 0 && (
            <span className="rounded-full bg-brand-600 px-1.5 text-[10.5px] font-semibold text-white">{c.unread}</span>
          )}
        </div>
      </div>
    </button>
  );
}

// ─── Painel lateral ──────────────────────────────────────────────────────────

function ContactPanel({ detail, onSummarize }: { detail: ConversationDetail; onSummarize: () => Promise<void> }) {
  const { contact, conversation: conv, orders, tickets, previous_conversations } = detail;
  const [loading, setLoading] = useState(false);
  return (
    <aside className="scroll-thin w-80 shrink-0 space-y-4 overflow-y-auto border-l border-slate-200 bg-white p-4">
      <div className="flex flex-col items-center pt-2 text-center">
        <Avatar name={contact.name} size={56} />
        <p className="mt-2 font-semibold">{contact.name}</p>
        <p className="flex items-center gap-1 text-xs text-slate-500">
          <MapPin size={12} /> {contact.city ?? "—"}
        </p>
        <div className="mt-2 flex flex-wrap justify-center gap-1">
          {contact.tags.map((t) => (
            <Tag key={t} tone={t === "cliente-vip" ? "brand" : "slate"}>
              {t}
            </Tag>
          ))}
          {conv.tags.map((t) => (
            <Tag key={t} tone="red">
              {t}
            </Tag>
          ))}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-2 text-xs">
        {[
          ["Telefone", contact.phone ?? "—"],
          ["E-mail", contact.email ?? "—"],
          ["Instagram", contact.instagram ?? "—"],
          ["Total comprado", brl(contact.lifetime_value)],
        ].map(([k, v]) => (
          <div key={k} className="rounded-lg bg-slate-50 px-2.5 py-2">
            <dt className="text-slate-400">{k}</dt>
            <dd className="truncate font-medium text-slate-700" title={v}>
              {v}
            </dd>
          </div>
        ))}
      </dl>

      <section className="rounded-xl border border-brand-100 bg-gradient-to-b from-brand-50 to-white p-3">
        <div className="mb-1.5 flex items-center gap-1.5">
          <Sparkles size={14} className="text-brand-600" />
          <h3 className="text-xs font-semibold text-brand-800">Resumo da IA</h3>
          <button
            onClick={async () => {
              setLoading(true);
              await onSummarize().finally(() => setLoading(false));
            }}
            className="ml-auto rounded p-1 text-brand-500 hover:bg-brand-100"
            title="Gerar novamente"
          >
            {loading ? <Spinner className="h-3 w-3" /> : <RefreshCw size={12} />}
          </button>
        </div>
        {conv.handoff_reason && (
          <p className="mb-1.5 text-[11.5px] font-medium text-amber-700">Transbordo: {conv.handoff_reason}</p>
        )}
        <p className="text-[12.5px] leading-relaxed whitespace-pre-line text-slate-700">
          {conv.summary ?? "Clique em atualizar para gerar um resumo deste atendimento."}
        </p>
      </section>

      <section>
        <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase">
          <Package size={13} /> Pedidos
        </h3>
        {orders.length === 0 && <p className="text-xs text-slate-400">Nenhum pedido.</p>}
        <ul className="space-y-1.5">
          {orders.map((o) => (
            <li key={o.id} className="rounded-lg border border-slate-200 px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[12.5px] font-medium">{o.code}</span>
                <span className="text-[12.5px] font-medium">{brl(o.total)}</span>
              </div>
              <div className="mt-0.5 flex items-center justify-between text-[11.5px] text-slate-500">
                <span
                  className={clsx(
                    o.status === "entregue" && "text-emerald-600",
                    o.status === "enviado" && "text-sky-600",
                    o.status === "cancelado" && "text-red-500",
                  )}
                >
                  {o.status_label}
                </span>
                <span>{shortDate(o.created_at)}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {tickets.length > 0 && (
        <section>
          <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase">
            <ClipboardList size={13} /> Protocolos
          </h3>
          <ul className="space-y-1.5">
            {tickets.map((t) => (
              <li key={t.id} className="rounded-lg bg-slate-50 px-3 py-2 text-[12px]">
                <div className="flex justify-between">
                  <span className="font-mono font-medium">{t.protocol}</span>
                  <span className="text-slate-500 capitalize">{t.kind}</span>
                </div>
                <p className="mt-0.5 line-clamp-2 text-slate-500">{t.description}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {previous_conversations.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold text-slate-500 uppercase">Histórico</h3>
          <ul className="space-y-1">
            {previous_conversations.map((p) => (
              <li key={p.id} className="flex items-center gap-2 text-[12px] text-slate-600">
                <ChannelIcon channel={p.channel} size={12} />
                <span>{shortDate(p.created_at)}</span>
                <span className="truncate text-slate-400">{p.intent ?? "—"}</span>
                {p.csat && <span className="ml-auto text-amber-500">★ {p.csat}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}

// ─── Conversa ────────────────────────────────────────────────────────────────

function ConversationView({ id }: { id: number }) {
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [typing, setTyping] = useState(false);
  const [suggestionSources, setSuggestionSources] = useState<string[]>([]);
  const endRef = useRef<HTMLDivElement>(null);
  const typingTimer = useRef<number>();

  const [notFound, setNotFound] = useState(false);
  const load = useCallback(
    () =>
      api
        .conversation(id)
        .then(setDetail)
        .catch(() => setNotFound(true)),
    [id],
  );

  useEffect(() => {
    setDetail(null);
    setDraft("");
    setSuggestionSources([]);
    load();
    api.markRead(id).catch(() => {});
  }, [id, load]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [detail?.messages.length, typing]);

  useEvent("message.created", (m: Message) => {
    if (m.conversation_id !== id) return;
    if (m.sender === "bot") setTyping(false);
    setDetail((d) => (d && !d.messages.some((x) => x.id === m.id) ? { ...d, messages: [...d.messages, m] } : d));
    if (m.sender === "contact") api.markRead(id).catch(() => {});
  });
  useEvent("conversation.updated", (c: Conversation) => {
    if (c.id !== id) return;
    setDetail((d) => (d ? { ...d, conversation: c } : d));
  });
  useEvent("typing", (t: { conversation_id: number }) => {
    if (t.conversation_id !== id) return;
    setTyping(true);
    window.clearTimeout(typingTimer.current);
    typingTimer.current = window.setTimeout(() => setTyping(false), 6000);
  });

  if (notFound) {
    return (
      <div className="flex flex-1 items-center justify-center bg-slate-50">
        <EmptyState icon={InboxIcon} title="Conversa não encontrada" text="Ela pode ter sido removida ao reiniciar a demo." />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex flex-1 items-center justify-center text-slate-400">
        <Spinner />
      </div>
    );
  }

  const conv = detail.conversation;
  const canReply = conv.status === "human" && conv.agent?.id === CURRENT_AGENT.id;
  const senti = sentimentInfo(conv.sentiment);

  const run = async (key: string, fn: () => Promise<unknown>) => {
    setBusy(key);
    try {
      await fn();
    } finally {
      setBusy(null);
    }
  };

  const send = () =>
    draft.trim() &&
    run("send", async () => {
      await api.sendAgentMessage(id, CURRENT_AGENT.id, draft);
      setDraft("");
      setSuggestionSources([]);
    });

  return (
    <div className="flex min-w-0 flex-1">
      <section className="flex min-w-0 flex-1 flex-col bg-slate-50/60">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-5 py-3">
          <Avatar name={conv.contact.name} channel={conv.channel} size={40} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="truncate font-semibold">{conv.contact.name}</h2>
              <StatusPill status={conv.status} />
              <PriorityPill priority={conv.priority} />
            </div>
            <p className="flex items-center gap-2 text-xs text-slate-500">
              <span>{CHANNELS[conv.channel].label}</span>·<span>{conv.intent_label ?? "Sem intenção definida"}</span>·
              <span className={senti.cls}>
                {senti.emoji} {senti.label}
              </span>
              {conv.agent && (
                <>
                  ·<span>Responsável: {conv.agent.name}</span>
                </>
              )}
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            {conv.status !== "resolved" && !canReply && (
              <button className="btn-primary" disabled={!!busy} onClick={() => run("assign", () => api.assign(id, CURRENT_AGENT.id))}>
                <UserCheck size={15} /> Assumir
              </button>
            )}
            {conv.status === "human" && (
              <button className="btn-secondary" disabled={!!busy} onClick={() => run("bot", () => api.returnToBot(id))}>
                <Bot size={15} /> Devolver à IA
              </button>
            )}
            {conv.status !== "resolved" && (
              <button className="btn-secondary" disabled={!!busy} onClick={() => run("resolve", () => api.resolve(id))}>
                <CheckCheck size={15} /> Encerrar
              </button>
            )}
          </div>
        </header>

        <div className="scroll-thin flex-1 overflow-y-auto px-6 py-4">
          {detail.messages.map((m) => (
            <MessageBubble key={m.id} msg={m} contactName={conv.contact.name} />
          ))}
          {typing && (
            <div className="my-2 flex flex-row-reverse items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-600 text-white">
                <Sparkles size={13} />
              </span>
              <span className="rounded-2xl bg-brand-50 px-4 py-3 ring-1 ring-brand-100">
                <TypingDots />
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <footer className="border-t border-slate-200 bg-white p-3">
          {conv.status === "resolved" ? (
            <p className="py-2 text-center text-sm text-slate-500">
              Conversa encerrada {conv.resolved_by === "ai" ? "pela IA" : "pela equipe"}
              {conv.csat ? ` · avaliação ${conv.csat}/5 ★` : ""}
            </p>
          ) : !canReply ? (
            <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
              <span className="flex items-center gap-2">
                {conv.status === "bot" ? (
                  <>
                    <Sparkles size={15} className="text-brand-600" /> A IA está conduzindo este atendimento.
                  </>
                ) : conv.status === "waiting" ? (
                  <>
                    <InboxIcon size={15} className="text-amber-600" /> Aguardando um atendente assumir.
                  </>
                ) : (
                  <>
                    <ArrowLeftRight size={15} /> Em atendimento com {conv.agent?.name}.
                  </>
                )}
              </span>
              <button className="btn-primary" disabled={!!busy} onClick={() => run("assign", () => api.assign(id, CURRENT_AGENT.id))}>
                Assumir conversa
              </button>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-100">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                rows={3}
                placeholder="Escreva sua resposta… (Enter envia, Shift+Enter quebra linha)"
                className="w-full resize-none rounded-t-xl px-3 py-2.5 text-sm focus:outline-none"
              />
              <div className="flex items-center gap-2 border-t border-slate-100 px-2 py-1.5">
                <button
                  className="btn-ghost text-brand-700"
                  disabled={!!busy}
                  onClick={() =>
                    run("suggest", async () => {
                      const s = await api.suggest(id);
                      setDraft(s.text);
                      setSuggestionSources(s.sources.map((x) => x.title));
                    })
                  }
                >
                  {busy === "suggest" ? <Spinner className="h-3.5 w-3.5" /> : <Wand2 size={15} />}
                  Sugerir resposta
                </button>
                {suggestionSources.length > 0 && (
                  <span className="truncate text-[11px] text-slate-400">Baseado em: {suggestionSources.join(", ")}</span>
                )}
                <button className="btn-primary ml-auto" disabled={!draft.trim() || !!busy} onClick={send}>
                  <SendHorizontal size={15} /> Enviar
                </button>
              </div>
            </div>
          )}
        </footer>
      </section>
      <ContactPanel
        detail={detail}
        onSummarize={async () => {
          const r = await api.summarize(id);
          setDetail((d) => (d ? { ...d, conversation: { ...d.conversation, summary: r.summary } } : d));
        }}
      />
    </div>
  );
}

// ─── Página ──────────────────────────────────────────────────────────────────

export default function Inbox() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("open");
  const [channel, setChannel] = useState<Channel | "">("");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Conversation[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [flashIds, setFlashIds] = useState<Set<number>>(new Set());

  const fetchList = useCallback(() => {
    return api
      .conversations({ ...tabParams(tab), channel, q, limit: 80 })
      .then((r) => {
        setItems(r.items);
        setCounts(r.counts);
      })
      .finally(() => setLoading(false));
  }, [tab, channel, q]);

  useEffect(() => {
    setLoading(true);
    const t = window.setTimeout(fetchList, q ? 250 : 0);
    return () => window.clearTimeout(t);
  }, [fetchList, q]);

  useEvent("conversation.updated", (c: Conversation) => {
    setItems((list) => {
      const rest = list.filter((x) => x.id !== c.id);
      return matchesTab(c, tab, channel) ? [c, ...rest] : rest;
    });
    setFlashIds((s) => new Set(s).add(c.id));
    window.setTimeout(() => setFlashIds((s) => {
      const n = new Set(s);
      n.delete(c.id);
      return n;
    }), 1600);
    api.conversations({ status: "waiting", limit: 1 }).then((r) => setCounts(r.counts));
  });
  useEvent("demo.reset", fetchList);

  const sorted = useMemo(() => sortConvs(items, tab), [items, tab]);
  const selected = id ? Number(id) : null;

  return (
    <div className="flex h-full">
      <section className="flex w-[360px] shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="space-y-3 border-b border-slate-200 p-4">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold">Inbox</h1>
            <span className="text-xs text-slate-500">
              {counts.bot ?? 0} com IA · {counts.waiting ?? 0} na fila · {counts.human ?? 0} com humanos
            </span>
          </div>
          <div className="relative">
            <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar cliente…" className="input pl-9" />
          </div>
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={clsx(
                  "flex-1 rounded-md px-1.5 py-1 text-[12.5px] font-medium transition",
                  tab === t.key ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700",
                )}
              >
                {t.label}
                {t.key === "waiting" && (counts.waiting ?? 0) > 0 && (
                  <span className="ml-1 rounded-full bg-amber-400 px-1 text-[10px] text-slate-900">{counts.waiting}</span>
                )}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setChannel("")}
              className={clsx("pill", channel === "" ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-600 ring-slate-200")}
            >
              Todos
            </button>
            {CHANNEL_ORDER.map((ch) => (
              <button
                key={ch}
                onClick={() => setChannel(channel === ch ? "" : ch)}
                className={clsx("pill", channel === ch ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-600 ring-slate-200")}
              >
                <ChannelIcon channel={ch} size={11} /> {CHANNELS[ch].label}
              </button>
            ))}
          </div>
        </div>
        <div className="scroll-thin flex-1 overflow-y-auto">
          {loading && items.length === 0 ? (
            <div className="flex justify-center p-8 text-slate-400">
              <Spinner />
            </div>
          ) : sorted.length === 0 ? (
            <EmptyState icon={InboxIcon} title="Nada por aqui" text="Nenhuma conversa corresponde aos filtros." />
          ) : (
            sorted.map((c) => (
              <div key={c.id} className={clsx(flashIds.has(c.id) && "animate-flash")}>
                <ConversationItem c={c} active={c.id === selected} onClick={() => navigate(`/inbox/${c.id}`)} />
              </div>
            ))
          )}
        </div>
      </section>
      {selected ? (
        <ConversationView key={selected} id={selected} />
      ) : (
        <div className="flex flex-1 items-center justify-center bg-slate-50">
          <EmptyState
            icon={Sparkles}
            title="Selecione uma conversa"
            text="A IA resolve a maioria dos atendimentos sozinha. Aqui você acompanha, assume quando precisar e conta com o copiloto para responder."
          />
        </div>
      )}
    </div>
  );
}
