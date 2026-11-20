"""Provedor OpenAI (Chat Completions + function calling)."""

import json

from openai import AsyncOpenAI

from app.services.ai.base import AgentInput, AgentOutput, LLMProvider
from app.services.ai.prompts import build_context_block
from app.services.tools import openai_tools, run_tool

MAX_TOOL_ROUNDS = 5


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=60.0, max_retries=2)
        self.model = model

    async def respond(self, data: AgentInput) -> AgentOutput:
        out = AgentOutput(text="", provider=self.name, model=self.model)
        context = build_context_block(data.ctx.contact, data.ctx.conversation, len(data.ctx.contact.orders))
        messages: list[dict] = [{"role": "system", "content": f"{data.system_prompt}\n\n{context}"}]
        messages += data.history + [{"role": "user", "content": data.message}]
        usage = {"input_tokens": 0, "output_tokens": 0}

        for _ in range(MAX_TOOL_ROUNDS):
            resp = await self.client.chat.completions.create(
                model=self.model, messages=messages, tools=openai_tools()
            )
            if resp.usage:
                usage["input_tokens"] += resp.usage.prompt_tokens
                usage["output_tokens"] += resp.usage.completion_tokens
            msg = resp.choices[0].message
            if not msg.tool_calls:
                out.text = (msg.content or "").strip()
                break
            messages.append(msg.model_dump(exclude_none=True))
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                call = run_tool(data.ctx, tc.function.name, args)
                out.tool_calls.append(call)
                if tc.function.name == "buscar_base_conhecimento" and call.result:
                    out.sources.extend(call.result["resultados"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(call.result if call.error is None else {"erro": call.error},
                                          ensure_ascii=False),
                })
        else:
            out.text = "Estou verificando algumas informações. Um especialista vai te responder em instantes."

        out.usage = usage
        out.confidence = 0.9 if out.text else 0.3
        return out

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip()
