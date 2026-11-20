import clsx from "clsx";
import { Check, CheckCircle2, CircleDashed, Save } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { ChannelIcon, PageHeader, Spinner, Toggle } from "../components/ui";
import { api } from "../lib/api";
import { num, PROVIDER_LABEL } from "../lib/format";
import type { AgentSettings, EngineInfo } from "../lib/types";

const TONES: { key: AgentSettings["tone"]; label: string; example: string }[] = [
  { key: "amigavel", label: "Amigável", example: "Oi, Ju! Já encontrei seu pedido 😊" },
  { key: "profissional", label: "Profissional", example: "Olá, Juliana. Localizei o seu pedido." },
  { key: "descontraido", label: "Descontraído", example: "Achei! Seu pedido tá voando até você 🚀" },
];
const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function Section({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="card grid grid-cols-1 gap-6 p-6 lg:grid-cols-[260px_1fr]">
      <div>
        <h2 className="font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-800">{label}</span>
      {hint && <span className="mb-1.5 block text-xs text-slate-500">{hint}</span>}
      <div className={clsx(!hint && "mt-1.5")}>{children}</div>
    </label>
  );
}

function Integration({ ok, name, detail, icon }: { ok: boolean; name: string; detail: string; icon: ReactNode }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 p-3">
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">{icon}</span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{name}</p>
        <p className="truncate text-xs text-slate-500">{detail}</p>
      </div>
      {ok ? (
        <span className="flex items-center gap-1 text-xs font-medium text-emerald-600">
          <CheckCircle2 size={14} /> Conectado
        </span>
      ) : (
        <span className="flex items-center gap-1 text-xs text-slate-400">
          <CircleDashed size={14} /> Não configurado
        </span>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [form, setForm] = useState<AgentSettings | null>(null);
  const [engine, setEngine] = useState<EngineInfo | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.settings().then((s) => {
      setForm(s.agent);
      setEngine(s.engine);
    });
  }, []);

  if (!form || !engine) return <div className="p-8"><Spinner /></div>;

  const set = <K extends keyof AgentSettings>(k: K, v: AgentSettings[K]) => {
    setForm({ ...form, [k]: v });
    setSaved(false);
  };

  const save = async () => {
    setSaving(true);
    const r = await api.saveSettings(form).finally(() => setSaving(false));
    setForm(r.agent);
    setSaved(true);
  };

  return (
    <div className="scroll-thin h-full overflow-y-auto p-8">
      <PageHeader
        title="Agente de IA"
        subtitle="Personalidade, regras de transbordo e integrações do assistente virtual."
        actions={
          <button className="btn-primary" onClick={save} disabled={saving}>
            {saving ? <Spinner className="h-3.5 w-3.5" /> : saved ? <Check size={15} /> : <Save size={15} />}
            {saved ? "Salvo" : "Salvar alterações"}
          </button>
        }
      />
      <div className="space-y-5">
        <Section title="Persona" subtitle="Como o assistente se apresenta e conversa com os clientes.">
          <Field label="Nome do assistente">
            <input className="input max-w-xs" value={form.bot_name} onChange={(e) => set("bot_name", e.target.value)} />
          </Field>
          <Field label="Tom de voz">
            <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
              {TONES.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => set("tone", t.key)}
                  className={clsx(
                    "rounded-xl border p-3 text-left transition",
                    form.tone === t.key ? "border-brand-400 bg-brand-50 ring-4 ring-brand-100" : "border-slate-200 hover:border-slate-300",
                  )}
                >
                  <p className="text-sm font-medium">{t.label}</p>
                  <p className="mt-1 text-xs text-slate-500 italic">“{t.example}”</p>
                </button>
              ))}
            </div>
          </Field>
          <Field label="Mensagem de saudação" hint="Use {nome} e {bot}. Vazio = padrão do sistema.">
            <textarea className="input" rows={2} value={form.greeting} onChange={(e) => set("greeting", e.target.value)} />
          </Field>
          <Field label="Instruções da empresa" hint="Regras extras enviadas ao modelo (ex.: campanhas vigentes, assuntos proibidos).">
            <textarea
              className="input"
              rows={4}
              value={form.custom_instructions}
              placeholder="Ex.: Durante a Black Friday, informe que os prazos de entrega podem ter 2 dias úteis a mais."
              onChange={(e) => set("custom_instructions", e.target.value)}
            />
          </Field>
        </Section>

        <Section title="Transbordo para humanos" subtitle="Quando a IA deve passar a conversa para a equipe.">
          <Field
            label={`Limite de sentimento: ${num(form.handoff_sentiment_threshold, 2)}`}
            hint="Abaixo deste valor (−1 muito negativo … 0 neutro), a conversa vai para a fila com prioridade alta."
          >
            <input
              type="range"
              min={-1}
              max={0}
              step={0.05}
              value={form.handoff_sentiment_threshold}
              onChange={(e) => set("handoff_sentiment_threshold", Number(e.target.value))}
              className="w-full max-w-md accent-brand-600"
            />
          </Field>
          <Field label="Transferir após respostas sem confiança" hint="Quantas vezes seguidas a IA pode não encontrar resposta confiável.">
            <select
              className="input max-w-[120px]"
              value={form.handoff_after_failures}
              onChange={(e) => set("handoff_after_failures", Number(e.target.value))}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </Field>
          <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium">Encerrar automaticamente ao agradecer</p>
              <p className="text-xs text-slate-500">Quando o cliente agradece após ser atendido, a IA encerra a conversa.</p>
            </div>
            <Toggle checked={form.auto_resolve_on_thanks} onChange={(v) => set("auto_resolve_on_thanks", v)} label="Encerrar ao agradecer" />
          </div>
          <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium">Pesquisa de satisfação (CSAT)</p>
              <p className="text-xs text-slate-500">Pede uma nota de 1 a 5 ao encerrar o atendimento.</p>
            </div>
            <Toggle checked={form.csat_enabled} onChange={(v) => set("csat_enabled", v)} label="CSAT" />
          </div>
        </Section>

        <Section title="Horário da equipe" subtitle="A IA atende 24/7. Fora deste horário, o transbordo avisa o cliente.">
          <div className="flex flex-wrap items-center gap-4">
            <Field label="Início">
              <input
                type="time"
                className="input w-32"
                value={form.business_hours.start}
                onChange={(e) => set("business_hours", { ...form.business_hours, start: e.target.value })}
              />
            </Field>
            <Field label="Fim">
              <input
                type="time"
                className="input w-32"
                value={form.business_hours.end}
                onChange={(e) => set("business_hours", { ...form.business_hours, end: e.target.value })}
              />
            </Field>
          </div>
          <div className="flex gap-1.5">
            {DAYS.map((d, i) => {
              const on = form.business_hours.days.includes(i);
              return (
                <button
                  key={d}
                  type="button"
                  onClick={() =>
                    set("business_hours", {
                      ...form.business_hours,
                      days: on ? form.business_hours.days.filter((x) => x !== i) : [...form.business_hours.days, i].sort(),
                    })
                  }
                  className={clsx(
                    "h-9 w-12 rounded-lg text-xs font-medium",
                    on ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-500",
                  )}
                >
                  {d}
                </button>
              );
            })}
          </div>
        </Section>

        <Section title="Motor e integrações" subtitle="Configurados por variáveis de ambiente no servidor.">
          <div className="rounded-xl bg-slate-950 p-4 text-slate-300">
            <p className="text-xs text-slate-500">Motor em uso</p>
            <p className="mt-0.5 text-lg font-semibold text-white">{PROVIDER_LABEL[engine.provider] ?? engine.provider}</p>
            <p className="font-mono text-xs text-slate-400">{engine.model}</p>
            <p className="mt-2 text-xs text-slate-500">
              Sem chave de API, o OmniFlow usa o motor local (NLU + busca BM25), e a demo funciona offline. Se o provedor
              falhar, o motor local responde automaticamente.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <Integration ok={engine.anthropic_configured} name="Anthropic Claude" detail="ANTHROPIC_API_KEY" icon={<span className="text-sm font-bold text-[#d97757]">A</span>} />
            <Integration ok={engine.openai_configured} name="OpenAI" detail="OPENAI_API_KEY" icon={<span className="text-sm font-bold">O</span>} />
            <Integration ok={engine.whatsapp_configured} name="WhatsApp Cloud API" detail="Webhook: /webhooks/whatsapp" icon={<ChannelIcon channel="whatsapp" size={16} />} />
            <Integration ok name="Webchat" detail="Widget para o site" icon={<ChannelIcon channel="webchat" size={16} />} />
          </div>
        </Section>
      </div>
    </div>
  );
}
