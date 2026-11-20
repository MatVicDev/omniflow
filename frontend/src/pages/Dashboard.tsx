import clsx from "clsx";
import {
  Bot, Clock, Coins, Hourglass, MessagesSquare, Smile, TrendingDown, TrendingUp, Zap,
} from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Avatar, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { brl, CHANNEL_ORDER, CHANNELS, duration, num, toDate } from "../lib/format";
import { useEvent } from "../lib/realtime";
import type { Overview } from "../lib/types";

const INK = { primary: "#0f172a", secondary: "#475569", muted: "#94a3b8", grid: "#eef2f6" };
// rampa sequencial (azul) para o mapa de calor
const SEQ = ["#f1f5f9", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"];
const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function Delta({ value, inverse = false }: { value: number | null | undefined; inverse?: boolean }) {
  if (value === null || value === undefined) return null;
  if (Math.abs(value) < 0.05) return <span className="text-xs font-medium text-slate-400">estável</span>;
  const good = inverse ? value < 0 : value > 0;
  const Icon = value >= 0 ? TrendingUp : TrendingDown;
  return (
    <span className={clsx("inline-flex items-center gap-0.5 text-xs font-medium", good ? "text-emerald-600" : "text-red-600")}>
      <Icon size={12} /> {value > 0 ? "+" : ""}
      {num(value, 1)}%
    </span>
  );
}

function Kpi({
  icon: Icon,
  label,
  value,
  delta,
  inverse,
  hint,
}: {
  icon: typeof Bot;
  label: string;
  value: string;
  delta?: number | null;
  inverse?: boolean;
  hint?: string;
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-[13px] text-slate-500">
        <Icon size={15} className="text-slate-400" /> {label}
      </div>
      <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-slate-900">{value}</p>
      <div className="mt-2 flex items-center gap-2">
        <Delta value={delta} inverse={inverse} />
        {hint && <span className="text-[11.5px] text-slate-400">{hint}</span>}
      </div>
    </div>
  );
}

function Panel({ title, subtitle, children, className }: { title: string; subtitle?: string; children: ReactNode; className?: string }) {
  return (
    <section className={clsx("card p-5", className)}>
      <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
      {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

/** Barras horizontais de série única: rótulo + valor em tinta de texto, barra com ponta arredondada. */
function HBars({ rows, color = "#2a78d6" }: { rows: { label: string; value: number; color?: string }[]; color?: string }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <ul className="space-y-2.5">
      {rows.map((r) => (
        <li key={r.label} className="group" title={`${r.label}: ${r.value}`}>
          <div className="mb-1 flex justify-between text-[12.5px]">
            <span className="text-slate-600">{r.label}</span>
            <span className="font-medium text-slate-900 tabular-nums">{num(r.value)}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full transition-all group-hover:opacity-80"
              style={{ width: `${(r.value / max) * 100}%`, background: r.color ?? color }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function VolumeTooltip({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number }[]; label?: string }) {
  if (!active || !payload?.length || !label) return null;
  const total = payload.reduce((s, p) => s + p.value, 0);
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-slate-900">
        {toDate(label).toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" })} · {total} conversas
      </p>
      {[...payload].reverse().map((p) => (
        <p key={p.dataKey} className="flex items-center gap-2 text-slate-600">
          <span className="h-2 w-2 rounded-full" style={{ background: CHANNELS[p.dataKey as keyof typeof CHANNELS].color }} />
          {CHANNELS[p.dataKey as keyof typeof CHANNELS].label}
          <span className="ml-auto pl-4 font-medium text-slate-900 tabular-nums">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

function Heatmap({ data }: { data: Overview["heatmap"] }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  const [hover, setHover] = useState<{ weekday: number; hour: number; count: number } | null>(null);
  return (
    <div>
      <div className="grid grid-cols-[32px_repeat(24,minmax(0,1fr))] gap-[2px]">
        <span />
        {Array.from({ length: 24 }, (_, h) => (
          <span key={h} className="text-center text-[9.5px] text-slate-400">
            {h % 3 === 0 ? `${h}h` : ""}
          </span>
        ))}
        {WEEKDAYS.map((wd, d) => (
          <div key={wd} className="contents">
            <span className="pr-1 text-right text-[10.5px] leading-[18px] text-slate-500">{wd}</span>
            {data
              .filter((c) => c.weekday === d)
              .map((c) => {
                const step = c.count === 0 ? 0 : Math.min(SEQ.length - 1, 1 + Math.floor((c.count / max) * (SEQ.length - 1)));
                return (
                  <span
                    key={c.hour}
                    onMouseEnter={() => setHover(c)}
                    onMouseLeave={() => setHover(null)}
                    className="h-[18px] rounded-[3px] hover:ring-2 hover:ring-slate-900/20"
                    style={{ background: SEQ[step] }}
                  />
                );
              })}
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
        <span>{hover ? `${WEEKDAYS[hover.weekday]}, ${hover.hour}h–${hover.hour + 1}h: ${hover.count} conversas` : "Passe o mouse sobre as células"}</span>
        <span className="flex items-center gap-1">
          menos
          {SEQ.slice(1).map((c) => (
            <span key={c} className="h-2.5 w-2.5 rounded-[2px]" style={{ background: c }} />
          ))}
          mais
        </span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Overview | null>(null);

  const load = useCallback(() => api.overview(days).then(setData), [days]);
  useEffect(() => {
    load();
  }, [load]);
  useEvent("conversation.updated", () => {
    // atualiza o painel ao vivo sem recarregar a página (com folga para rajadas de eventos)
    window.clearTimeout((window as unknown as { __ovT?: number }).__ovT);
    (window as unknown as { __ovT?: number }).__ovT = window.setTimeout(load, 1200);
  });

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        <Spinner />
      </div>
    );
  }

  const k = data.kpis;
  const d = data.deltas;
  const totalChannels = data.channels.reduce((s, c) => s + c.count, 0);
  const sentimentTotal = data.sentiment.reduce((s, x) => s + x.count, 0);

  return (
    <div className="scroll-thin h-full overflow-y-auto p-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Visão geral</h1>
          <p className="mt-1 text-sm text-slate-500">
            Desempenho do atendimento e do agente de IA nos últimos {days} dias, comparado ao período anterior.
          </p>
        </div>
        <div className="flex gap-1 rounded-lg bg-slate-200/60 p-1">
          {[7, 30, 60].map((n) => (
            <button
              key={n}
              onClick={() => setDays(n)}
              className={clsx(
                "rounded-md px-3 py-1 text-xs font-medium",
                days === n ? "bg-white shadow-sm" : "text-slate-500 hover:text-slate-700",
              )}
            >
              {n} dias
            </button>
          ))}
        </div>
      </div>

      {/* ao vivo */}
      <div className="mb-6 flex flex-wrap items-center gap-x-8 gap-y-2 rounded-2xl bg-slate-950 px-5 py-3.5 text-sm text-slate-300">
        <span className="flex items-center gap-2 font-medium text-white">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          Agora
        </span>
        <span>
          <b className="text-white">{data.live.bot}</b> com a IA
        </span>
        <span>
          <b className="text-amber-300">{data.live.waiting}</b> na fila humana
        </span>
        <span>
          <b className="text-white">{data.live.human}</b> com atendentes
        </span>
        {data.ai_latency_ms && (
          <span className="ml-auto flex items-center gap-1.5">
            <Zap size={14} className="text-brand-300" /> Latência média da IA:{" "}
            <b className="text-white">{num(data.ai_latency_ms)} ms</b>
          </span>
        )}
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <Kpi icon={MessagesSquare} label="Conversas" value={num(k.conversations)} delta={d.conversations} />
        <Kpi icon={Bot} label="Resolvidas pela IA" value={`${num(k.ai_resolution_rate, 1)}%`} delta={d.ai_resolution_rate} hint={`${k.ai_resolved} conversas`} />
        <Kpi icon={Clock} label="1ª resposta (média)" value={duration(k.avg_first_response_s)} delta={d.avg_first_response_s} inverse />
        <Kpi icon={Smile} label="CSAT" value={`${num(k.csat, 2)} / 5`} delta={d.csat} hint={`${k.csat_responses} avaliações`} />
        <Kpi icon={Hourglass} label="Horas poupadas" value={`${num(k.hours_saved, 1)} h`} delta={d.hours_saved} hint="do time humano" />
        <Kpi icon={Coins} label="Economia estimada" value={brl(k.cost_saved)} delta={d.cost_saved} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Panel title="Volume de conversas por canal" subtitle="Novas conversas por dia" className="xl:col-span-2">
          <div className="mb-3 flex flex-wrap gap-4">
            {CHANNEL_ORDER.map((ch) => (
              <span key={ch} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: CHANNELS[ch].color }} />
                {CHANNELS[ch].label}
              </span>
            ))}
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.daily} margin={{ top: 4, right: 4, bottom: 0, left: -24 }} barCategoryGap={days > 30 ? 1 : 3}>
                <CartesianGrid vertical={false} stroke={INK.grid} />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: INK.muted, fontSize: 11 }}
                  tickFormatter={(v: string) => toDate(v).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
                  interval={Math.ceil(data.daily.length / 8)}
                />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: INK.muted, fontSize: 11 }} allowDecimals={false} />
                <Tooltip content={<VolumeTooltip />} cursor={{ fill: "rgba(15,23,42,0.04)" }} />
                {CHANNEL_ORDER.map((ch, i) => (
                  <Bar
                    key={ch}
                    dataKey={ch}
                    stackId="v"
                    fill={CHANNELS[ch].color}
                    stroke="#fff"
                    strokeWidth={1}
                    radius={i === CHANNEL_ORDER.length - 1 ? [3, 3, 0, 0] : 0}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Distribuição por canal" subtitle={`${num(totalChannels)} conversas no período`}>
          <HBars
            rows={data.channels
              .slice()
              .sort((a, b) => b.count - a.count)
              .map((c) => ({ label: CHANNELS[c.channel].label, value: c.count, color: CHANNELS[c.channel].color }))}
          />
          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="mb-2 text-xs font-medium text-slate-500">Sentimento dos clientes</p>
            <div className="flex h-2.5 gap-[2px] overflow-hidden rounded-full">
              {data.sentiment.map((s) => (
                <div
                  key={s.label}
                  title={`${s.label}: ${s.count}`}
                  style={{
                    width: `${(s.count / Math.max(1, sentimentTotal)) * 100}%`,
                    background: s.label === "positivo" ? "#1baf7a" : s.label === "negativo" ? "#e34948" : "#cbd5e1",
                  }}
                />
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[11.5px] text-slate-600">
              {data.sentiment.map((s) => (
                <span key={s.label} className="capitalize">
                  {s.label} <b className="text-slate-900">{Math.round((s.count / Math.max(1, sentimentTotal)) * 100)}%</b>
                </span>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Panel title="Principais assuntos" subtitle="Intenção detectada pela IA">
          <HBars rows={data.intents.map((i) => ({ label: i.label, value: i.count }))} />
        </Panel>
        <Panel title="Motivos de transbordo" subtitle="Por que a IA passou para um humano">
          {data.handoff_reasons.length ? (
            <HBars rows={data.handoff_reasons.map((h) => ({ label: h.reason, value: h.count }))} color="#6250d6" />
          ) : (
            <p className="text-sm text-slate-400">Nenhum transbordo no período.</p>
          )}
        </Panel>
        <Panel title="Horários de pico" subtitle="Conversas por dia da semana e hora (Brasília)">
          <Heatmap data={data.heatmap} />
        </Panel>
      </div>

      <Panel title="Equipe humana" subtitle="Atendimentos assumidos após transbordo">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-xs text-slate-500">
              <th className="pb-2 font-medium">Atendente</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 text-right font-medium">Conversas</th>
              <th className="pb-2 text-right font-medium">Resolvidas</th>
              <th className="pb-2 text-right font-medium">Em aberto</th>
              <th className="pb-2 text-right font-medium">CSAT</th>
            </tr>
          </thead>
          <tbody>
            {data.team.map((a) => (
              <tr key={a.id} className="border-b border-slate-50 last:border-0">
                <td className="py-2.5">
                  <span className="flex items-center gap-2.5">
                    <Avatar name={a.name} color={a.avatar_color} size={28} />
                    {a.name}
                  </span>
                </td>
                <td>
                  <span className="flex items-center gap-1.5 text-xs text-slate-600">
                    <span
                      className={clsx(
                        "h-2 w-2 rounded-full",
                        a.status === "online" ? "bg-emerald-500" : a.status === "away" ? "bg-amber-400" : "bg-slate-300",
                      )}
                    />
                    {{ online: "Online", away: "Ausente", offline: "Offline" }[a.status] ?? a.status}
                  </span>
                </td>
                <td className="text-right tabular-nums">{a.conversations}</td>
                <td className="text-right tabular-nums">{a.resolved}</td>
                <td className="text-right tabular-nums">{a.open}</td>
                <td className="text-right tabular-nums">{a.csat ? `★ ${num(a.csat, 1)}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
