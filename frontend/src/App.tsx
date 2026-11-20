import clsx from "clsx";
import {
  BookOpen, Bot, LayoutDashboard, MessagesSquare, RotateCcw, Settings, Smartphone, Workflow,
} from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { Avatar, Spinner } from "./components/ui";
import { api } from "./lib/api";
import { PROVIDER_LABEL } from "./lib/format";
import { useEvent, useRealtime } from "./lib/realtime";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Flows = lazy(() => import("./pages/Flows"));
const Inbox = lazy(() => import("./pages/Inbox"));
const Knowledge = lazy(() => import("./pages/Knowledge"));
const SettingsPage = lazy(() => import("./pages/Settings"));
const Simulator = lazy(() => import("./pages/Simulator"));

/** Usuário logado na demo (supervisora do time). */
export const CURRENT_AGENT = { id: 1, name: "Ana Ribeiro", role: "Supervisora", color: "#7c3aed" };

const NAV = [
  { to: "/", label: "Visão geral", icon: LayoutDashboard, end: true },
  { to: "/inbox", label: "Inbox", icon: MessagesSquare },
  { to: "/simulador", label: "Simulador", icon: Smartphone },
  { to: "/conhecimento", label: "Base de conhecimento", icon: BookOpen },
  { to: "/fluxos", label: "Automações", icon: Workflow },
  { to: "/configuracoes", label: "Agente de IA", icon: Settings },
];

function Sidebar({ waiting }: { waiting: number }) {
  const { connected } = useRealtime();
  const [engine, setEngine] = useState<{ provider: string; model: string } | null>(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    api.health().then((h) => setEngine({ provider: h.ai_provider, model: h.ai_model })).catch(() => setEngine(null));
  }, []);

  const reset = async () => {
    if (!confirm("Restaurar todos os dados de demonstração?")) return;
    setResetting(true);
    await api.resetDemo().finally(() => setResetting(false));
    location.reload();
  };

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-slate-950 text-slate-300">
      <div className="flex items-center gap-2.5 px-5 pt-5 pb-6">
        <img src="/logo.svg" alt="" className="h-9 w-9" />
        <div>
          <p className="text-[15px] leading-tight font-semibold text-white">OmniFlow</p>
          <p className="text-[11px] text-slate-500">Aurora Cosméticos</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                isActive ? "bg-white/10 font-medium text-white" : "hover:bg-white/5 hover:text-white",
              )
            }
          >
            <Icon size={17} />
            <span className="flex-1">{label}</span>
            {to === "/inbox" && waiting > 0 && (
              <span className="rounded-full bg-amber-400 px-1.5 text-[11px] font-semibold text-slate-950">{waiting}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mx-3 mb-3 rounded-xl border border-white/10 bg-white/5 p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-white">
          <Bot size={14} className="text-brand-300" />
          Motor de IA
        </div>
        <p className="mt-1 text-[13px] text-slate-300">
          {engine ? PROVIDER_LABEL[engine.provider] ?? engine.provider : "—"}
        </p>
        <p className="truncate font-mono text-[10.5px] text-slate-500">{engine?.model}</p>
        <div className="mt-2 flex items-center gap-1.5 text-[11px]">
          <span className={clsx("h-1.5 w-1.5 rounded-full", connected ? "bg-emerald-400" : "bg-red-400")} />
          {connected ? "Tempo real conectado" : "Reconectando…"}
        </div>
      </div>

      <div className="flex items-center gap-3 border-t border-white/10 px-4 py-3">
        <Avatar name={CURRENT_AGENT.name} color={CURRENT_AGENT.color} size={32} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-white">{CURRENT_AGENT.name}</p>
          <p className="text-[11px] text-slate-500">{CURRENT_AGENT.role}</p>
        </div>
        <button
          onClick={reset}
          disabled={resetting}
          title="Reiniciar demo"
          className="rounded-md p-1.5 text-slate-500 hover:bg-white/10 hover:text-white"
        >
          <RotateCcw size={15} className={clsx(resetting && "animate-spin")} />
        </button>
      </div>
    </aside>
  );
}

export default function App() {
  const [waiting, setWaiting] = useState(0);
  const refreshCounts = () => api.conversations({ status: "waiting", limit: 1 }).then((r) => setWaiting(r.counts.waiting));

  useEffect(() => {
    refreshCounts();
  }, []);
  useEvent("conversation.updated", refreshCounts);

  return (
    <div className="flex h-full">
      <Sidebar waiting={waiting} />
      <main className="min-w-0 flex-1 overflow-hidden">
        <Suspense
          fallback={
            <div className="flex h-full items-center justify-center text-slate-400">
              <Spinner />
            </div>
          }
        >
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/inbox/:id" element={<Inbox />} />
          <Route path="/simulador" element={<Simulator />} />
          <Route path="/conhecimento" element={<Knowledge />} />
          <Route path="/fluxos" element={<Flows />} />
          <Route path="/configuracoes" element={<SettingsPage />} />
        </Routes>
        </Suspense>
      </main>
    </div>
  );
}
