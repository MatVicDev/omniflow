import clsx from "clsx";
import { Globe, Instagram, Mail, MessageCircle, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { CHANNELS, initials, PRIORITY, STATUS } from "../lib/format";
import type { Channel, ConvStatus, Priority } from "../lib/types";

const CHANNEL_ICON: Record<Channel, LucideIcon> = {
  whatsapp: MessageCircle,
  instagram: Instagram,
  webchat: Globe,
  email: Mail,
};

export function ChannelIcon({ channel, size = 14, boxed = false }: { channel: Channel; size?: number; boxed?: boolean }) {
  const Icon = CHANNEL_ICON[channel];
  const c = CHANNELS[channel];
  if (!boxed) return <Icon size={size} style={{ color: c.color }} aria-label={c.label} />;
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center rounded-md"
      style={{ background: c.soft, width: size + 10, height: size + 10 }}
      title={c.label}
    >
      <Icon size={size} style={{ color: c.color }} aria-label={c.label} />
    </span>
  );
}

export function Avatar({
  name,
  color,
  size = 36,
  channel,
}: {
  name: string;
  color?: string;
  size?: number;
  channel?: Channel;
}) {
  // cor determinística por nome (estável entre renders e sessões)
  const hue = [...name].reduce((a, ch) => a + ch.charCodeAt(0), 0) % 360;
  return (
    <span className="relative inline-flex h-fit shrink-0 self-start">
      <span
        className="inline-flex items-center justify-center rounded-full font-semibold text-white"
        style={{
          width: size,
          height: size,
          fontSize: size * 0.36,
          background: color ?? `linear-gradient(135deg, hsl(${hue} 55% 58%), hsl(${(hue + 40) % 360} 60% 48%))`,
        }}
      >
        {initials(name)}
      </span>
      {channel && (
        <span className="absolute -right-1 -bottom-1 rounded-full bg-white p-[3px] shadow-sm ring-1 ring-slate-200">
          <ChannelIcon channel={channel} size={10} />
        </span>
      )}
    </span>
  );
}

export function StatusPill({ status }: { status: ConvStatus }) {
  const s = STATUS[status];
  return <span className={clsx("pill", s.cls)}>{s.label}</span>;
}

export function PriorityPill({ priority }: { priority: Priority }) {
  const p = PRIORITY[priority];
  if (!p) return null;
  return <span className={clsx("pill", p.cls)}>{p.label}</span>;
}

export function Tag({ children, tone = "slate" }: { children: ReactNode; tone?: "slate" | "brand" | "red" | "green" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-600 ring-slate-200",
    brand: "bg-brand-50 text-brand-700 ring-brand-200",
    red: "bg-red-50 text-red-700 ring-red-200",
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  };
  return <span className={clsx("pill", tones[tone])}>{children}</span>;
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={clsx(
        "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors",
        checked ? "bg-brand-600" : "bg-slate-300",
      )}
    >
      <span
        className={clsx(
          "inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform",
          checked ? "translate-x-5" : "translate-x-0.5",
        )}
      />
    </button>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={clsx("inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent", className)}
      aria-label="Carregando"
    />
  );
}

export function EmptyState({ icon: Icon, title, text }: { icon: LucideIcon; title: string; text?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center">
      <span className="rounded-2xl bg-brand-50 p-3 text-brand-600">
        <Icon size={22} />
      </span>
      <p className="font-medium text-slate-700">{title}</p>
      {text && <p className="max-w-xs text-sm text-slate-500">{text}</p>}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1">
      {[0, 150, 300].map((d) => (
        <span key={d} className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" style={{ animationDelay: `${d}ms` }} />
      ))}
    </span>
  );
}
