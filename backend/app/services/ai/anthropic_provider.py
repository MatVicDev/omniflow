"""Provedor Claude (Anthropic) com loop de ferramentas.

- Prompt caching automático: persona + regras + ferramentas formam um prefixo estável.
- Fallback de recusa no servidor (`fallbacks: "default"`), sem lista de modelos para manter.
- Esforço `low`: atendimento é rota de chat, latência importa mais que raciocínio longo.
"""

import json
import logging

import anthropic

from app.services.ai.base import AgentInput, AgentOutput, LLMProvider
from app.services.ai.prompts import build_context_block
from app.services.tools import anthropic_tools, run_tool

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _merge_turns(history: list[dict], message: str) -> list[dict]:
    """A API exige alternância user/assistant — junta turnos consecutivos do mesmo papel."""
    merged: list[dict] = []
    for turn in [*history, {"role": "user", "content": message}]:
        if merged and merged[-1]["role"] == turn["role"]:
            merged[-1]["content"] += "\n\n" + turn["content"]
        else:
            merged.append(dict(turn))
    while merged and merged[0]["role"] != "user":
        merged.pop(0)
    return merged


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=60.0, max_retries=2)
        self.model = model

    async def _create(self, **params):
        return await self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            output_config={"effort": "low"},
            cache_control={"type": "ephemeral"},
            **params,
        )

    async def respond(self, data: AgentInput) -> AgentOutput:
        out = AgentOutput(text="", provider=self.name, model=self.model)
        orders_count = len(data.ctx.contact.orders)
        system = [
            {"type": "text", "text": data.system_prompt},
            {"type": "text", "text": build_context_block(data.ctx.contact, data.ctx.conversation, orders_count)},
        ]
        messages: list[dict] = _merge_turns(data.history, data.message)
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}

        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._create(system=system, tools=anthropic_tools(), messages=messages)
            for key in usage:
                usage[key] += getattr(response.usage, key, 0) or 0

            if response.stop_reason == "refusal":
                out.text = "Vou encaminhar sua mensagem para um especialista da equipe, tudo bem?"
                out.tool_calls.append(run_tool(data.ctx, "transferir_para_humano",
                                               {"motivo": "Assunto fora do escopo da IA", "prioridade": "normal"}))
                break

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason != "tool_use" or not tool_uses:
                out.text = "\n".join(b.text for b in response.content if b.type == "text").strip()
                break

            # devolve o conteúdo completo (inclui blocos de thinking) e todos os resultados numa só mensagem
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in tool_uses:
                args = block.input if isinstance(block.input, dict) else json.loads(block.input or "{}")
                call = run_tool(data.ctx, block.name, args)
                out.tool_calls.append(call)
                if block.name == "buscar_base_conhecimento" and call.result:
                    out.sources.extend(call.result["resultados"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(call.result if call.error is None else {"erro": call.error},
                                          ensure_ascii=False),
                    "is_error": call.error is not None,
                })
            messages.append({"role": "user", "content": results})
        else:
            out.text = "Estou verificando algumas informações. Um especialista vai te responder em instantes."

        out.usage = usage
        out.confidence = 0.92 if out.text else 0.3
        return out

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max(max_tokens, 2048),
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "refusal":
            return ""
        return "\n".join(b.text for b in response.content if b.type == "text").strip()
