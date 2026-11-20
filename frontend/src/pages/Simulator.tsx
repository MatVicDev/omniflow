import clsx from "clsx";
import { ArrowUpRight, ChevronLeft, Lock, RotateCcw, SendHorizontal, Sparkles, UserRound } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AiTrace from "../components/AiTrace";
import { Avatar, ChannelIcon, Spinner, StatusPill, TypingDots } from "../components/ui";
import { api } from "../lib/api";
import { CHANNELS, clock, richText } from "../lib/format";
import { useEvent } from "../lib/realtime";
import type { Channel, Conversation, ConvStatus, Message, Persona } from "../lib/types";

/** Tema visual do "aparelho" de cada canal, do ponto de vista do cliente. */
const DEVICE: Record<Channel, { header: string; bg: string; mine: string; theirs: string; name: string }> = {
  whatsapp: {
    header: "bg-[#075e54] text-white",
    bg: "bg-[#efeae2]",
    mine: "bg-[#d9fdd3] text-slate-800",
    theirs: "bg-white text-slate-800",
    name: "Aurora Cosméticos",
  },
  instagram: {
    header: "bg-white text-slate-900 border-b border-slate-200",
    bg: "bg-white",
    mine: "bg-gradient-to-br from-[#7c3aed] to-[#db2777] text-white",
    theirs: "bg-slate-100 text-slate-800",
    name: "aurora.cosmeticos",
  },
  webchat: {
    header: "bg-gradient-to-r from-brand-600 to-indigo-600 text-white",
    bg: "bg-slate-50",
    mine: "bg-brand-600 text-white",
    theirs: "bg-white text-slate-800 ring-1 ring-slate-200",
    name: "Atendimento Aurora",
  },
  email: {
    header: "bg-slate-800 text-white",
    bg: "bg-white",
    mine: "bg-slate-50 text-slate-800 ring-1 ring-slate-200",
    theirs: "bg-white text-slate-800 ring-1 ring-slate-200",
    name: "atendimento@aurora.com.br",
  },
};

function visitorIdentity() {
  const id = Math.random().toString(36).slice(2, 7);
  return { name: `Visitante ${id.toUpperCase()}`, email: `visitante.${id}@demo.omniflow` };
}

export default function Simulator() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [channel, setChannel] = useState<Channel>("whatsapp");
  const [visitor, setVisitor] = useState(visitorIdentity);
  const [convId, setConvId] = useState<number | null>(null);
  const [status, setStatus] = useState<ConvStatus | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [typing, setTyping] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.personas().then((p) => {
      setPersonas(p);
      choose(p[0]);
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, typing]);

  const choose = async (p: Persona, ch?: Channel) => {
    const nextChannel = ch ?? p.channel;
    setPersona(p);
    setChannel(nextChannel);
    setMessages([]);
    setConvId(null);
    setStatus(null);
    setSelectedTrace(null);
    if (!p.contact) return;
    // retoma a conversa aberta da persona neste canal, se existir
    const open = await api.conversations({ status: "open", q: p.contact.name, channel: nextChannel, limit: 1 });
    const conv = open.items[0];
    if (conv) {
      const d = await api.conversation(conv.id);
      setConvId(conv.id);
      setStatus(conv.status);
      setMessages(d.messages);
    }
  };

  const send = async (msg: string) => {
    if (!msg.trim() || !persona) return;
    setSending(true);
    setText("");
    try {
      const ident = persona.contact ? { contact_id: persona.contact.id } : visitor;
      const res = await api.inbound(channel, { text: msg, ...ident });
      if (res.conversation_id !== convId) {
        const d = await api.conversation(res.conversation_id);
        setConvId(res.conversation_id);
        setStatus(d.conversation.status);
        setMessages(d.messages);
      }
      if (res.reply) setSelectedTrace(res.reply.id);
    } finally {
      setSending(false);
    }
  };

  const restart = () => {
    if (persona && !persona.contact) setVisitor(visitorIdentity());
    setMessages([]);
    setConvId(null);
    setStatus(null);
    setSelectedTrace(null);
  };

  useEvent("message.created", (m: Message) => {
    if (m.conversation_id !== convId) return;
    if (m.sender !== "contact") setTyping(false);
    setMessages((list) => (list.some((x) => x.id === m.id) ? list : [...list, m]));
  });
  useEvent("conversation.updated", (c: Conversation) => {
    if (c.id === convId) setStatus(c.status);
  });
  useEvent("typing", (t: { conversation_id: number }) => {
    if (t.conversation_id === convId || convId === null) setTyping(true);
  });

  const visible = messages.filter((m) => m.sender !== "system");
  const botReplies = messages.filter((m) => m.sender === "bot" && m.meta?.kind === "ai_reply");
  const trace = useMemo(
    () => botReplies.find((m) => m.id === selectedTrace) ?? botReplies[botReplies.length - 1],
    [botReplies, selectedTrace],
  );
  const theme = DEVICE[channel];
  const displayName = persona?.contact?.name ?? visitor.name;

  return (
    <div className="scroll-thin h-full overflow-y-auto p-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Simulador de canais</h1>
          <p className="mt-1 text-sm text-slate-500">
            Converse como um cliente e veja, em tempo real, como o agente de IA entende, decide e age.
          </p>
        </div>
        <Link to={convId ? `/inbox/${convId}` : "/inbox"} className="btn-secondary">
          Ver no Inbox <ArrowUpRight size={15} />
        </Link>
      </div>

      <div className="grid grid-cols-[280px_minmax(360px,420px)_1fr] gap-6">
        {/* Personas */}
        <div className="space-y-3">
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Escolha um cenário</p>
          {personas.map((p) => (
            <button
              key={p.key}
              onClick={() => choose(p)}
              className={clsx(
                "card w-full p-3 text-left transition hover:border-brand-300",
                persona?.key === p.key && "border-brand-400 ring-4 ring-brand-100",
              )}
            >
              <div className="flex items-center gap-2.5">
                {p.contact ? (
                  <Avatar name={p.contact.name} size={34} channel={p.channel} />
                ) : (
                  <span className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full bg-slate-200 text-slate-500">
                    <UserRound size={16} />
                  </span>
                )}
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{p.contact?.name ?? "Visitante anônimo"}</p>
                  <p className="truncate text-xs text-slate-500">{p.headline}</p>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {p.skills.map((s) => (
                  <span key={s} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10.5px] text-slate-600">
                    {s}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>

        {/* Aparelho */}
        <div>
          <div className="mb-3 flex gap-1 rounded-lg bg-slate-200/60 p-1">
            {(["whatsapp", "instagram", "webchat", "email"] as Channel[]).map((ch) => (
              <button
                key={ch}
                onClick={() => persona && choose(persona, ch)}
                className={clsx(
                  "flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-medium transition",
                  channel === ch ? "bg-white shadow-sm" : "text-slate-500 hover:text-slate-700",
                )}
              >
                <ChannelIcon channel={ch} size={13} /> {CHANNELS[ch].label}
              </button>
            ))}
          </div>

          <div className="overflow-hidden rounded-[2rem] border-[10px] border-slate-900 bg-slate-900 shadow-2xl">
            <div className={clsx("flex items-center gap-2.5 px-4 py-3", theme.header)}>
              <ChevronLeft size={18} className="opacity-70" />
              <img src="/logo.svg" className="h-8 w-8 rounded-full" alt="" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{theme.name}</p>
                <p className="text-[11px] opacity-75">
                  {typing ? "digitando…" : status === "human" || status === "waiting" ? "equipe de atendimento" : "online"}
                </p>
              </div>
              <button onClick={restart} title="Nova conversa" className="rounded p-1 opacity-70 hover:opacity-100">
                <RotateCcw size={15} />
              </button>
            </div>

            <div className={clsx("scroll-thin h-[480px] overflow-y-auto px-3 py-4", theme.bg)}>
              {channel === "webchat" && visible.length === 0 && (
                <p className="mx-auto mb-3 max-w-[85%] rounded-xl bg-white p-3 text-center text-xs text-slate-500 ring-1 ring-slate-200">
                  Olá! 👋 Sou a assistente virtual da Aurora. Como posso ajudar?
                </p>
              )}
              {visible.length === 0 && channel !== "webchat" && (
                <p className="mt-20 flex items-center justify-center gap-1.5 text-center text-xs text-slate-500">
                  <Lock size={11} /> Envie uma mensagem para começar
                </p>
              )}
              {visible.map((m) => {
                const mine = m.sender === "contact";
                return (
                  <div key={m.id} className={clsx("animate-pop mb-2 flex", mine ? "justify-end" : "justify-start")}>
                    <button
                      onClick={() => m.sender === "bot" && setSelectedTrace(m.id)}
                      className={clsx(
                        "max-w-[82%] rounded-2xl px-3 py-2 text-left text-[13.5px] leading-snug whitespace-pre-wrap shadow-sm",
                        mine ? theme.mine : theme.theirs,
                        mine ? "rounded-br-md" : "rounded-bl-md",
                        m.sender === "bot" && trace?.id === m.id && "ring-2 ring-brand-400",
                        m.sender === "bot" ? "cursor-pointer" : "cursor-default",
                      )}
                    >
                      {m.sender === "agent" && (
                        <span className="mb-0.5 block text-[11px] font-semibold text-sky-700">{m.agent?.name} · equipe</span>
                      )}
                      <span dangerouslySetInnerHTML={{ __html: richText(m.content) }} />
                      <span className="mt-1 block text-right text-[10px] opacity-60">{clock(m.created_at)}</span>
                    </button>
                  </div>
                );
              })}
              {typing && (
                <div className="mb-2 flex">
                  <span className={clsx("rounded-2xl rounded-bl-md px-4 py-3 shadow-sm", theme.theirs)}>
                    <TypingDots />
                  </span>
                </div>
              )}
              <div ref={endRef} />
            </div>

            <div className="bg-white p-2.5">
              <div className="scroll-thin mb-2 flex gap-1.5 overflow-x-auto pb-1">
                {persona?.suggestions.map((s) => (
                  <button
                    key={s}
                    disabled={sending}
                    onClick={() => send(s)}
                    className="shrink-0 rounded-full border border-slate-200 px-2.5 py-1 text-[11.5px] text-slate-600 hover:border-brand-300 hover:text-brand-700"
                  >
                    {s}
                  </button>
                ))}
              </div>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  send(text);
                }}
                className="flex items-center gap-2"
              >
                <input
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={`Mensagem como ${displayName.split(" ")[0]}…`}
                  className="input rounded-full"
                />
                <button
                  type="submit"
                  disabled={sending || !text.trim()}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white disabled:opacity-40"
                  aria-label="Enviar"
                >
                  {sending ? <Spinner className="h-3.5 w-3.5" /> : <SendHorizontal size={15} />}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Bastidores */}
        <div className="card flex min-h-[600px] flex-col">
          <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
            <span className="rounded-lg bg-brand-100 p-1.5 text-brand-700">
              <Sparkles size={15} />
            </span>
            <div>
              <h2 className="text-sm font-semibold">Bastidores da IA</h2>
              <p className="text-xs text-slate-500">Clique em uma resposta da IA no aparelho para inspecioná-la</p>
            </div>
            {status && (
              <span className="ml-auto">
                <StatusPill status={status} />
              </span>
            )}
          </div>
          <div className="scroll-thin flex-1 overflow-y-auto p-5">
            {trace ? (
              <>
                <div className="mb-4 rounded-xl bg-slate-50 p-3 text-[13px] text-slate-600">
                  <p className="mb-1 text-[11px] font-semibold text-slate-400 uppercase">Mensagem do cliente</p>
                  {[...messages].reverse().find((m) => m.sender === "contact" && m.id < trace.id)?.content}
                </div>
                <AiTrace trace={trace.meta} />
              </>
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-center text-sm text-slate-400">
                <Sparkles size={28} className="mb-3 text-brand-300" />
                <p className="max-w-xs">
                  Envie uma mensagem para ver o pipeline completo: entendimento, regras, ferramentas, fontes da base de
                  conhecimento e a decisão final.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
