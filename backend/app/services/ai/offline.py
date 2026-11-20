"""Motor offline: NLU + RAG (BM25) + ferramentas, com respostas por templates.

Garante que a demo funcione sem chave de API e sem internet, usando o mesmo
pipeline (ferramentas, fontes, trace) dos provedores LLM.
"""

import random
import re

from app.services.ai.base import AgentInput, AgentOutput, LLMProvider
from app.services.tools import ToolCall, run_tool
from app.utils import first_name, normalize

_OPENERS = ["Claro!", "Pode deixar!", "Vamos lá!", "Com certeza!"]
_KB_THRESHOLD = 0.38


class OfflineProvider(LLMProvider):
    name = "offline"
    model = "omniflow-nlu-rag-v1"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    # ─── API pública ─────────────────────────────────────────────────────────

    async def respond(self, data: AgentInput) -> AgentOutput:
        out = AgentOutput(text="", provider=self.name, model=self.model)
        intent = data.nlu.intent
        entities = data.nlu.entities

        # Contexto: cliente respondeu só com o código do pedido que a IA pediu
        if intent in ("outro", "saudacao") and "order_code" in entities and data.previous_intent:
            intent = data.previous_intent if data.previous_intent in (
                "rastreio", "troca_devolucao", "cancelamento") else "rastreio"

        handler = getattr(self, f"_on_{intent}", self._on_knowledge)
        text = handler(data, out)
        out.text = self._format_for_channel(text, data)
        return out

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        # usado pelo copiloto; o serviço de copiloto tem heurísticas próprias no modo offline
        return prompt[:max_tokens]

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _tool(self, data: AgentInput, out: AgentOutput, name: str, **args) -> ToolCall:
        call = run_tool(data.ctx, name, args)
        out.tool_calls.append(call)
        if name == "buscar_base_conhecimento" and call.result:
            out.sources.extend(call.result["resultados"])
        return call

    def _bot(self, data: AgentInput) -> str:
        return data.settings.get("bot_name", "Aurora")

    def _name(self, data: AgentInput) -> str:
        return first_name(data.ctx.contact.name)

    def _format_for_channel(self, text: str, data: AgentInput) -> str:
        channel = data.ctx.conversation.channel
        if channel == "email":
            clean = re.sub(r"[\U0001F300-\U0001FAFF✨💜📦🚚]", "", text).replace("*", "").strip()
            return (f"Olá, {self._name(data)}!\n\n{clean}\n\nAtenciosamente,\n"
                    f"{self._bot(data)} — Atendimento Aurora Cosméticos")
        if channel == "webchat":
            return text.replace("*", "")
        return text

    def _kb_answer(self, data: AgentInput, out: AgentOutput, query: str) -> str | None:
        call = self._tool(data, out, "buscar_base_conhecimento", consulta=query)
        hits = call.result["resultados"] if call.result else []
        if not hits or hits[0]["score"] < _KB_THRESHOLD:
            return None
        out.confidence = hits[0]["score"]
        answer = hits[0]["text"]
        # complementa com um segundo trecho do mesmo artigo se for curto e relevante
        if len(hits) > 1 and hits[1]["article_id"] == hits[0]["article_id"] and len(answer) < 260:
            answer += "\n\n" + hits[1]["text"]
        return answer

    def _fallback(self, data: AgentInput, out: AgentOutput) -> str:
        out.confidence = 0.2
        return ("Hmm, não encontrei essa informação com segurança na nossa base 🤔 "
                "Pode me contar com mais detalhes? Se preferir, transfiro você para um especialista.")

    # ─── Intenções ───────────────────────────────────────────────────────────

    def _on_saudacao(self, data: AgentInput, out: AgentOutput) -> str:
        out.confidence = 0.95
        greeting = data.settings.get("greeting") or (
            "Oi, {nome}! Eu sou a {bot}, assistente virtual da Aurora Cosméticos ✨ "
            "Posso ajudar com pedidos, trocas, produtos e dúvidas. Como posso te ajudar hoje?"
        )
        return greeting.format(nome=self._name(data), bot=self._bot(data))

    def _on_agradecimento(self, data: AgentInput, out: AgentOutput) -> str:
        out.confidence = 0.95
        out.resolved_hint = True
        return f"Imagina, {self._name(data)}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."

    def _on_horario(self, data: AgentInput, out: AgentOutput) -> str:
        return self._kb_answer(data, out, "horário de atendimento") or self._fallback(data, out)

    def _on_rastreio(self, data: AgentInput, out: AgentOutput) -> str:
        code = data.nlu.entities.get("order_code")
        call = self._tool(data, out, "consultar_pedido", **({"codigo": code} if code else {}))
        res = call.result or {}
        if not res.get("encontrado"):
            out.confidence = 0.6
            if code:
                return (f"Não localizei o pedido *{code}* no seu cadastro 😕 Confere o número pra mim? "
                        "Ele aparece no e-mail de confirmação da compra (formato AUR-12345).")
            return "Não encontrei pedidos no seu cadastro. Você tem o código do pedido (formato AUR-12345)?"

        orders = res["pedidos"]
        active = [o for o in orders if o["status"] not in ("entregue", "cancelado")]
        if not code and len(active) > 1:
            out.confidence = 0.8
            lines = "\n".join(f"• *{o['codigo']}* — {o['status_descricao']} ({o['total']})" for o in active)
            return f"Encontrei estes pedidos em andamento:\n{lines}\n\nQual deles você quer acompanhar?"

        order = (active or orders)[0]
        out.confidence = 0.93
        text = f"Encontrei seu pedido *{order['codigo']}* 📦\n• Status: *{order['status_descricao']}*"
        if order["codigo_rastreio"]:
            text += f"\n• {order['transportadora']} — rastreio: {order['codigo_rastreio']}"
        if order["previsao_entrega"] and order["status"] != "entregue":
            text += f"\n• Previsão de entrega: {order['previsao_entrega']}"
        if order["atrasado"]:
            text += ("\n\nPeço desculpas: a entrega passou do prazo previsto 😔 Já sinalizei para a "
                     "transportadora. Se não chegar em 2 dias úteis, você pode pedir reenvio ou reembolso integral.")
        elif order["status"] == "entregue":
            text += "\n\nO pedido consta como entregue. Se teve algum problema, me conta que eu te ajudo!"
        elif order["status"] in ("pago", "separacao"):
            text += "\n\nAssim que for despachado você recebe o código de rastreio por e-mail e aqui."
        return text

    def _on_troca_devolucao(self, data: AgentInput, out: AgentOutput) -> str:
        norm = normalize(data.message)
        code = data.nlu.entities.get("order_code")
        problem = any(k in norm for k in ("defeito", "quebrad", "vazad", "errado", "alergia", "irrit"))
        if code or (problem and data.previous_intent == "troca_devolucao"):
            kind = "devolucao" if any(k in norm for k in ("devolv", "devoluc", "reembolso", "arrepend")) else "troca"
            call = self._tool(data, out, "abrir_solicitacao", tipo=kind, descricao=data.message[:280],
                              **({"codigo_pedido": code} if code else {}))
            out.confidence = 0.9
            r = call.result
            return (f"Pronto, {self._name(data)}! Abri sua solicitação de {kind.replace('devolucao', 'devolução')} "
                    f"✅\n• Protocolo: *{r['protocolo']}*\n• Retorno da equipe: {r['prazo_retorno']}\n\n"
                    "Você vai receber por e-mail a etiqueta de postagem gratuita. Posso ajudar em algo mais?")

        policy = self._kb_answer(data, out, f"troca devolução {data.message}")
        ask = "\n\nSe quiser que eu já abra a solicitação, me envie o *código do pedido* e o motivo 🙂"
        if problem:
            return ("Sinto muito pelo transtorno! 😔 Produtos com defeito ou avaria têm troca garantida, "
                    "sem custo de frete." + ask)
        return (policy or "Você pode solicitar troca ou devolução em até 30 dias após o recebimento.") + ask

    def _on_cancelamento(self, data: AgentInput, out: AgentOutput) -> str:
        code = data.nlu.entities.get("order_code")
        if not code:
            policy = self._kb_answer(data, out, "cancelamento pedido")
            return (policy or "Consigo te ajudar com o cancelamento.") + \
                "\n\nMe informa o *código do pedido* que você quer cancelar?"
        call = self._tool(data, out, "consultar_pedido", codigo=code)
        res = call.result or {}
        if not res.get("encontrado"):
            return f"Não localizei o pedido *{code}* no seu cadastro. Pode conferir o número?"
        order = res["pedidos"][0]
        if order["status"] in ("pago", "separacao"):
            t = self._tool(data, out, "abrir_solicitacao", tipo="financeiro",
                           descricao=f"Cancelamento do pedido {code} solicitado pelo cliente.", codigo_pedido=code)
            out.confidence = 0.92
            return (f"Feito! Solicitei o cancelamento do pedido *{code}* ✅\n• Protocolo: *{t.result['protocolo']}*\n"
                    f"• Estorno de {order['total']} na mesma forma de pagamento ({order['pagamento']}).\n\n"
                    "Pix é estornado em até 24h; cartão, em até 2 faturas.")
        if order["status"] == "enviado":
            out.confidence = 0.85
            return (f"O pedido *{code}* já foi enviado 🚚, então não dá mais para cancelar pelo sistema. "
                    "Você pode recusar a entrega ou, ao receber, solicitar a devolução gratuita em até 7 dias "
                    "(direito de arrependimento) — o reembolso é integral.")
        out.confidence = 0.8
        return f"O pedido *{code}* está com status *{order['status_descricao']}*. Quer que eu abra uma devolução?"

    def _on_produto(self, data: AgentInput, out: AgentOutput) -> str:
        call = self._tool(data, out, "consultar_produto", termo=data.message)
        products = (call.result or {}).get("produtos", [])
        norm = normalize(data.message)
        if any(k in norm for k in ("vegano", "crueldade", "testado", "ingrediente")):
            kb = self._kb_answer(data, out, data.message)
            if kb:
                return kb
        if not products:
            return self._kb_answer(data, out, data.message) or self._fallback(data, out)
        out.confidence = 0.88
        lines = []
        for p in products:
            stock = "em estoque" if p["em_estoque"] else "esgotado no momento"
            lines.append(f"• *{p['nome']}* — {p['preco']} ({stock})\n  {p['descricao']}")
        return f"{self._rng.choice(_OPENERS)} Separei estas opções pra você:\n\n" + "\n".join(lines) + \
            "\n\nQuer que eu te mande o link de algum deles?"

    def _on_reclamacao(self, data: AgentInput, out: AgentOutput) -> str:
        self._tool(data, out, "transferir_para_humano", motivo="Cliente insatisfeito", prioridade="high")
        return ("Sinto muito pela experiência, de verdade. 😔 Vou chamar agora um especialista da nossa equipe "
                "para cuidar pessoalmente do seu caso.")

    def _on_falar_humano(self, data: AgentInput, out: AgentOutput) -> str:
        self._tool(data, out, "transferir_para_humano", motivo="Cliente pediu atendente", prioridade="normal")
        return "Claro! Já estou chamando um especialista da equipe. Em instantes alguém continua com você 🙂"

    def _on_knowledge(self, data: AgentInput, out: AgentOutput) -> str:
        answer = self._kb_answer(data, out, data.message)
        if not answer:
            return self._fallback(data, out)
        return f"{self._rng.choice(_OPENERS)} {answer}"

    _on_frete_prazo = _on_pagamento = _on_promocao = _on_outro = _on_knowledge
