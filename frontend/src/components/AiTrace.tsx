import clsx from "clsx";
import {
  ArrowRightLeft, BookOpen, Brain, ChevronDown, Gauge, ShieldAlert, Sparkles, Wrench, Zap,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { num, PROVIDER_LABEL, sentimentInfo, TOOL_LABEL } from "../lib/format";
import type { AiTrace as Trace, ToolCall } from "../lib/types";

function Step({
  icon: Icon,
  title,
  tone = "slate",
  children,
  last,
}: {
  icon: typeof Brain;
  title: string;
  tone?: "slate" | "brand" | "amber" | "red" | "green";
  children: ReactNode;
  last?: boolean;
}) {
  const tones = {
    slate: "bg-slate-100 text-slate-600",
    brand: "bg-brand-100 text-brand-700",
    amber: "bg-amber-100 text-amber-700",
    red: "bg-red-100 text-red-700",
    green: "bg-emerald-100 text-emerald-700",
  };
  return (
    <div className="relative flex gap-3 pb-4">
      {!last && <span className="absolute top-7 bottom-0 left-[13px] w-px bg-slate-200" />}
      <span className={clsx("z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg", tones[tone])}>
        <Icon size={14} />
      </span>
      <div className="min-w-0 flex-1 pt-0.5">
        <p className="text-[12px] font-semibold tracking-wide text-slate-500 uppercase">{title}</p>
        <div className="mt-1 text-sm text-slate-700">{children}</div>
      </div>
    </div>
  );
}

function Bar({ value, className }: { value: number; className?: string }) {
  return (
    <span className="inline-block h-1.5 w-20 overflow-hidden rounded-full bg-slate-100 align-middle">
      <span className={clsx("block h-full rounded-full", className ?? "bg-brand-500")} style={{ width: `${value * 100}%` }} />
    </span>
  );
}

function ToolCallItem({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left">
        <code className="font-mono text-[12px] font-medium text-brand-700">{call.name}</code>
        <span className="truncate text-[11px] text-slate-500">{TOOL_LABEL[call.name]}</span>
        <span className="ml-auto shrink-0 font-mono text-[10.5px] text-slate-400">{num(call.duration_ms, 1)} ms</span>
        <ChevronDown size={13} className={clsx("shrink-0 text-slate-400 transition", open && "rotate-180")} />
      </button>
      {open && (
        <div className="space-y-1.5 border-t border-slate-200 px-2.5 py-2">
          <p className="text-[10.5px] font-semibold text-slate-400 uppercase">Argumentos</p>
          <pre className="scroll-thin max-h-28 overflow-auto rounded bg-slate-900 p-2 font-mono text-[11px] text-emerald-300">
            {JSON.stringify(call.args, null, 2)}
          </pre>
          <p className="text-[10.5px] font-semibold text-slate-400 uppercase">Resultado</p>
          <pre className="scroll-thin max-h-48 overflow-auto rounded bg-slate-900 p-2 font-mono text-[11px] text-sky-200">
            {call.error ? `Erro: ${call.error}` : JSON.stringify(call.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/** Linha do tempo do raciocínio da IA para uma resposta: NLU → regras → ferramentas → RAG → decisão. */
export default function AiTrace({ trace, compact = false }: { trace: Trace; compact?: boolean }) {
  const nlu = trace.nlu;
  const tools = (trace.tool_calls ?? []).filter((t) => t.name !== "buscar_base_conhecimento" || !compact);
  const sources = trace.sources ?? [];
  const senti = nlu ? sentimentInfo(nlu.sentiment) : null;

  return (
    <div className={clsx(compact ? "text-sm" : "")}>
      {nlu && (
        <Step icon={Brain} title="Entendimento (NLU)" tone="brand">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span>
              <span className="font-medium">{nlu.intent_label}</span>{" "}
              <span className="text-xs text-slate-400">· {Math.round(nlu.confidence * 100)}%</span>
            </span>
            <span className={clsx("text-xs font-medium", senti?.cls)}>
              {senti?.emoji} {senti?.label} ({nlu.sentiment > 0 ? "+" : ""}
              {num(nlu.sentiment, 2)})
            </span>
          </div>
          {Object.keys(nlu.entities).length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {Object.entries(nlu.entities).map(([k, v]) => (
                <span key={k} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-600">
                  {k}: {v}
                </span>
              ))}
            </div>
          )}
        </Step>
      )}

      {(trace.guardrail || (trace.flows?.length ?? 0) > 0) && (
        <Step icon={trace.guardrail ? ShieldAlert : Zap} title="Regras e automações" tone={trace.guardrail ? "red" : "amber"}>
          <ul className="space-y-0.5">
            {trace.guardrail && (
              <li className="font-medium text-red-700">Guardrail acionado: {trace.guardrail.replace(/_/g, " ")}</li>
            )}
            {trace.flows?.map((f) => (
              <li key={f.key}>
                <span className="font-medium">{f.name}</span>
                <span className="text-xs text-slate-500"> — {f.detail}</span>
              </li>
            ))}
          </ul>
        </Step>
      )}

      {tools.length > 0 && (
        <Step icon={Wrench} title={`Ferramentas (${tools.length})`}>
          <div className="space-y-1.5">
            {tools.map((c, i) => (
              <ToolCallItem key={i} call={c} />
            ))}
          </div>
        </Step>
      )}

      {sources.length > 0 && (
        <Step icon={BookOpen} title="Fontes consultadas (RAG)">
          <ul className="space-y-1.5">
            {sources.slice(0, compact ? 2 : 4).map((s, i) => (
              <li key={i} className="flex items-center gap-2">
                <Bar value={s.score} className={s.score >= 0.38 ? "bg-emerald-500" : "bg-slate-300"} />
                <span className="font-mono text-[11px] text-slate-400">{Math.round(s.score * 100)}%</span>
                <span className="truncate text-[13px]">{s.title}</span>
              </li>
            ))}
          </ul>
        </Step>
      )}

      <Step
        icon={trace.handoff ? ArrowRightLeft : Sparkles}
        title="Decisão"
        tone={trace.handoff ? "amber" : "green"}
        last
      >
        {trace.handoff ? (
          <p>
            Transferir para humano · <span className="font-medium">{trace.handoff.motivo}</span>
            {trace.handoff.prioridade && trace.handoff.prioridade !== "normal" && (
              <span className="ml-1 text-xs text-red-600">(prioridade {trace.handoff.prioridade})</span>
            )}
          </p>
        ) : (
          <p>Responder automaticamente</p>
        )}
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-slate-500">
          <span className="inline-flex items-center gap-1">
            <Bot2 /> {PROVIDER_LABEL[trace.provider ?? ""] ?? trace.provider}
            <span className="font-mono text-[10.5px] text-slate-400">{trace.model}</span>
          </span>
          {trace.latency_ms !== undefined && (
            <span className="inline-flex items-center gap-1">
              <Gauge size={12} /> {num(trace.latency_ms)} ms
            </span>
          )}
          {trace.confidence !== undefined && <span>Confiança {Math.round(trace.confidence * 100)}%</span>}
          {trace.usage?.input_tokens ? (
            <span>
              {num(trace.usage.input_tokens)} in · {num(trace.usage.output_tokens ?? 0)} out tokens
              {trace.usage.cache_read_input_tokens ? ` · ${num(trace.usage.cache_read_input_tokens)} em cache` : ""}
            </span>
          ) : null}
        </div>
        {trace.fallback_error && (
          <p className="mt-1.5 rounded bg-amber-50 px-2 py-1 text-[11.5px] text-amber-800">
            Provedor indisponível — resposta gerada pelo motor local. ({trace.fallback_error})
          </p>
        )}
      </Step>
    </div>
  );
}

function Bot2() {
  return <Sparkles size={12} className="text-brand-500" />;
}
