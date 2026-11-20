import clsx from "clsx";
import { ArrowRightLeft, CircleStop, GitBranch, MessageSquare, Play, Sparkles, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { PageHeader, Spinner, Toggle } from "../components/ui";
import { api } from "../lib/api";
import { num, since } from "../lib/format";
import type { Flow, FlowNode } from "../lib/types";

const NODE_W = 190;
const NODE_H = 62;

const NODE_STYLE: Record<FlowNode["type"], { icon: typeof Play; cls: string; label: string }> = {
  trigger: { icon: Play, cls: "border-emerald-300 bg-emerald-50 text-emerald-800", label: "Gatilho" },
  condition: { icon: GitBranch, cls: "border-amber-300 bg-amber-50 text-amber-800", label: "Condição" },
  ai: { icon: Sparkles, cls: "border-brand-300 bg-brand-50 text-brand-800", label: "IA" },
  action: { icon: Wrench, cls: "border-sky-300 bg-sky-50 text-sky-800", label: "Ação" },
  message: { icon: MessageSquare, cls: "border-slate-300 bg-white text-slate-800", label: "Mensagem" },
  handoff: { icon: ArrowRightLeft, cls: "border-orange-300 bg-orange-50 text-orange-800", label: "Humano" },
  end: { icon: CircleStop, cls: "border-slate-300 bg-slate-50 text-slate-600", label: "Fim" },
};

function FlowCanvas({ flow }: { flow: Flow }) {
  const byId = Object.fromEntries(flow.nodes.map((n) => [n.id, n]));
  const width = Math.max(...flow.nodes.map((n) => n.x)) + NODE_W + 40;
  const height = Math.max(...flow.nodes.map((n) => n.y)) + NODE_H + 30;

  return (
    <div
      className="scroll-thin relative overflow-x-auto rounded-xl border border-slate-200"
      style={{
        backgroundImage: "radial-gradient(circle, #e2e8f0 1px, transparent 1px)",
        backgroundSize: "18px 18px",
      }}
    >
      <div className="relative" style={{ width, height }}>
        <svg className="absolute inset-0" width={width} height={height}>
          <defs>
            <marker id={`arrow-${flow.id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="#94a3b8" />
            </marker>
          </defs>
          {flow.edges.map((e, i) => {
            const a = byId[e.from];
            const b = byId[e.to];
            if (!a || !b) return null;
            const x1 = a.x + NODE_W;
            const y1 = a.y + NODE_H / 2;
            const x2 = b.x - 4;
            const y2 = b.y + NODE_H / 2;
            const mx = (x1 + x2) / 2;
            return (
              <g key={i}>
                <path
                  d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
                  fill="none"
                  stroke={flow.active ? "#94a3b8" : "#cbd5e1"}
                  strokeWidth={1.75}
                  markerEnd={`url(#arrow-${flow.id})`}
                />
                {e.label && (
                  <text x={mx} y={(y1 + y2) / 2 - 6} textAnchor="middle" className="fill-slate-500 text-[11px] font-medium">
                    {e.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
        {flow.nodes.map((n) => {
          const s = NODE_STYLE[n.type];
          const Icon = s.icon;
          return (
            <div
              key={n.id}
              className={clsx("absolute flex items-start gap-2 rounded-xl border px-3 py-2 shadow-sm", s.cls, !flow.active && "grayscale")}
              style={{ left: n.x, top: n.y, width: NODE_W, height: NODE_H }}
            >
              <Icon size={14} className="mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] font-semibold tracking-wide uppercase opacity-60">{s.label}</p>
                <p className="truncate text-[12.5px] leading-tight font-medium">{n.label}</p>
                {n.detail && <p className="truncate text-[11px] opacity-70">{n.detail}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Flows() {
  const [flows, setFlows] = useState<Flow[] | null>(null);

  useEffect(() => {
    api.flows().then(setFlows);
  }, []);

  const toggle = async (f: Flow, active: boolean) => {
    setFlows((list) => list?.map((x) => (x.id === f.id ? { ...x, active } : x)) ?? null);
    await api.toggleFlow(f.id, active);
  };

  return (
    <div className="scroll-thin h-full overflow-y-auto p-8">
      <PageHeader
        title="Automações"
        subtitle="Regras que trabalham junto com a IA. Desligue um fluxo e o comportamento muda na próxima mensagem."
      />
      {!flows ? (
        <Spinner />
      ) : (
        <div className="space-y-5">
          {flows.map((f) => (
            <section key={f.id} className="card p-5">
              <div className="mb-4 flex items-start gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold">{f.name}</h2>
                    <span className="pill bg-slate-100 text-slate-600 ring-slate-200">{f.trigger.label}</span>
                  </div>
                  <p className="mt-1 max-w-3xl text-sm text-slate-500">{f.description}</p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <p>
                    <b className="text-slate-900 tabular-nums">{num(f.runs)}</b> execuções
                  </p>
                  <p>editado {since(f.updated_at)}</p>
                </div>
                <Toggle checked={f.active} onChange={(v) => toggle(f, v)} label={`Ativar ${f.name}`} />
              </div>
              <FlowCanvas flow={f} />
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
