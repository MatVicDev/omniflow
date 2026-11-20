import clsx from "clsx";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { clock, richText } from "../lib/format";
import type { Message } from "../lib/types";
import AiTrace from "./AiTrace";
import { Avatar } from "./ui";

/** Bolha na visão do atendente: cliente à esquerda; IA e equipe à direita. */
export default function MessageBubble({ msg, contactName }: { msg: Message; contactName: string }) {
  const [showTrace, setShowTrace] = useState(false);

  if (msg.sender === "system") {
    return (
      <div className="animate-pop my-3 flex justify-center">
        <span className="rounded-full bg-slate-100 px-3 py-1 text-[11.5px] text-slate-500">
          {msg.content} · {clock(msg.created_at)}
        </span>
      </div>
    );
  }

  const fromContact = msg.sender === "contact";
  const isBot = msg.sender === "bot";
  const hasTrace = isBot && msg.meta?.kind === "ai_reply" && (msg.meta.nlu || msg.meta.tool_calls);

  return (
    <div className={clsx("animate-pop my-2 flex gap-2.5", fromContact ? "justify-start" : "flex-row-reverse")}>
      {fromContact ? (
        <Avatar name={contactName} size={28} />
      ) : isBot ? (
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-600 text-white">
          <Sparkles size={13} />
        </span>
      ) : (
        <Avatar name={msg.agent?.name ?? "Equipe"} color={msg.agent?.avatar_color} size={28} />
      )}

      <div className={clsx("flex max-w-[72%] flex-col", fromContact ? "items-start" : "items-end")}>
        <div
          className={clsx(
            "rounded-2xl px-3.5 py-2.5 text-[14px] leading-relaxed break-words whitespace-pre-wrap",
            fromContact && "rounded-tl-md bg-white text-slate-800 ring-1 ring-slate-200",
            isBot && "rounded-tr-md bg-brand-50 text-slate-800 ring-1 ring-brand-100",
            msg.sender === "agent" && "rounded-tr-md bg-slate-900 text-white",
          )}
          dangerouslySetInnerHTML={{ __html: richText(msg.content) }}
        />
        <div className="mt-1 flex items-center gap-2 px-1 text-[11px] text-slate-400">
          {isBot && <span className="font-medium text-brand-600">IA</span>}
          {msg.sender === "agent" && <span className="font-medium text-slate-500">{msg.agent?.name}</span>}
          <span>{clock(msg.created_at)}</span>
          {hasTrace && (
            <button onClick={() => setShowTrace(!showTrace)} className="font-medium text-brand-600 hover:underline">
              {showTrace ? "Ocultar raciocínio" : "Ver raciocínio"}
            </button>
          )}
        </div>
        {showTrace && hasTrace && (
          <div className="animate-pop mt-2 w-[420px] max-w-full rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <AiTrace trace={msg.meta} compact />
          </div>
        )}
      </div>
    </div>
  );
}
