"""Ferramentas que o agente de IA pode chamar (function calling).

Cada ferramenta tem um schema JSON único, convertido para o formato de cada
provedor (Anthropic, OpenAI). O motor offline chama as mesmas funções — então
o trace exibido no painel é idêntico, seja qual for o provedor.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Contact, Conversation, Order, Product, Ticket
from app.services.retrieval import knowledge_index
from app.utils import brl, normalize, utcnow

ORDER_STATUS_LABEL = {
    "pago": "Pagamento aprovado",
    "separacao": "Em separação no estoque",
    "enviado": "Enviado",
    "entregue": "Entregue",
    "cancelado": "Cancelado",
}


@dataclass
class ToolContext:
    db: Session
    contact: Contact
    conversation: Conversation


@dataclass
class ToolCall:
    name: str
    args: dict
    result: Any
    duration_ms: float
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "args": self.args,
            "result": self.result,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]
    side_effects: dict = field(default_factory=dict)


# ─── Implementações ──────────────────────────────────────────────────────────


def _order_payload(o: Order) -> dict:
    return {
        "codigo": o.code,
        "status": o.status,
        "status_descricao": ORDER_STATUS_LABEL.get(o.status, o.status),
        "total": brl(o.total),
        "itens": [f"{i['qty']}x {i['name']}" for i in o.items],
        "pagamento": o.payment_method,
        "transportadora": o.carrier,
        "codigo_rastreio": o.tracking_code,
        "previsao_entrega": o.eta.strftime("%d/%m/%Y") if o.eta else None,
        "data_compra": o.created_at.strftime("%d/%m/%Y"),
        "atrasado": bool(o.eta and o.status == "enviado" and o.eta < utcnow()),
    }


def buscar_base_conhecimento(ctx: ToolContext, consulta: str) -> dict:
    hits = knowledge_index.search(ctx.db, consulta, k=3, min_score=0.2)
    return {"resultados": [h.as_dict() for h in hits]}


def consultar_pedido(ctx: ToolContext, codigo: str | None = None) -> dict:
    q = select(Order)
    if codigo:
        digits = "".join(c for c in codigo if c.isdigit())
        q = q.where(Order.code == f"AUR-{digits}")
        order = ctx.db.scalars(q).first()
        if not order:
            return {"encontrado": False, "mensagem": f"Nenhum pedido com o código {codigo}."}
        if order.contact_id != ctx.contact.id:
            # proteção básica de dados: só exibe pedidos do próprio cliente
            return {"encontrado": False, "mensagem": "Pedido não pertence a este cliente."}
        return {"encontrado": True, "pedidos": [_order_payload(order)]}

    orders = ctx.db.scalars(
        q.where(Order.contact_id == ctx.contact.id).order_by(Order.created_at.desc()).limit(3)
    ).all()
    if not orders:
        return {"encontrado": False, "mensagem": "Cliente não possui pedidos."}
    return {"encontrado": True, "pedidos": [_order_payload(o) for o in orders]}


def consultar_produto(ctx: ToolContext, termo: str) -> dict:
    words = [w for w in normalize(termo).split() if len(w) > 2]
    if not words:
        return {"produtos": []}
    conditions = []
    for w in words:
        like = f"%{w}%"
        conditions += [func.lower(Product.name).like(like), func.lower(Product.category).like(like),
                       func.lower(Product.description).like(like)]
    products = ctx.db.scalars(select(Product).where(or_(*conditions)).limit(12)).all()

    def relevance(p: Product) -> int:
        hay = normalize(f"{p.name} {p.category} {p.description}")
        return sum(w in hay for w in words) * 2 + sum(w in normalize(p.name) for w in words)

    ranked = sorted(products, key=relevance, reverse=True)[:3]
    return {
        "produtos": [
            {
                "sku": p.sku,
                "nome": p.name,
                "categoria": p.category,
                "preco": brl(p.price),
                "em_estoque": p.stock > 0,
                "estoque": p.stock,
                "descricao": p.description,
            }
            for p in ranked
        ]
    }


def abrir_solicitacao(ctx: ToolContext, tipo: str, descricao: str, codigo_pedido: str | None = None) -> dict:
    count = ctx.db.scalar(select(func.count(Ticket.id))) or 0
    protocol = f"OF-{utcnow():%y%m}-{count + 1:04d}"
    ticket = Ticket(
        protocol=protocol,
        conversation_id=ctx.conversation.id,
        contact_id=ctx.contact.id,
        kind=tipo,
        description=descricao,
        order_code=codigo_pedido,
        created_by="ai",
    )
    ctx.db.add(ticket)
    ctx.db.flush()
    prazo = {"troca": "até 2 dias úteis", "devolucao": "até 2 dias úteis", "financeiro": "até 3 dias úteis"}
    return {"protocolo": protocol, "tipo": tipo, "prazo_retorno": prazo.get(tipo, "até 1 dia útil")}


def transferir_para_humano(ctx: ToolContext, motivo: str, prioridade: str = "normal") -> dict:
    # o orquestrador lê esta chamada e aplica a mudança de status da conversa
    return {"transferido": True, "motivo": motivo, "prioridade": prioridade}


# ─── Registro ────────────────────────────────────────────────────────────────

TOOLS: dict[str, ToolSpec] = {
    t.name: t
    for t in [
        ToolSpec(
            "buscar_base_conhecimento",
            "Busca na base de conhecimento oficial da Aurora Cosméticos (políticas de troca, frete, "
            "pagamento, prazos, cupons, cuidados com produtos). Use antes de responder qualquer dúvida "
            "sobre regras ou políticas; nunca invente políticas.",
            {
                "type": "object",
                "properties": {"consulta": {"type": "string", "description": "Pergunta ou palavras-chave"}},
                "required": ["consulta"],
            },
            buscar_base_conhecimento,
        ),
        ToolSpec(
            "consultar_pedido",
            "Consulta pedidos do cliente atual: status, itens, rastreio e previsão de entrega. "
            "Sem código, retorna os 3 pedidos mais recentes do cliente.",
            {
                "type": "object",
                "properties": {"codigo": {"type": "string", "description": "Código do pedido, ex.: AUR-10234"}},
                "required": [],
            },
            consultar_pedido,
        ),
        ToolSpec(
            "consultar_produto",
            "Busca produtos no catálogo por nome, categoria ou necessidade (ex.: 'sérum pele oleosa'). "
            "Retorna preço e disponibilidade em estoque.",
            {
                "type": "object",
                "properties": {"termo": {"type": "string"}},
                "required": ["termo"],
            },
            consultar_produto,
        ),
        ToolSpec(
            "abrir_solicitacao",
            "Abre uma solicitação formal (troca, devolução, reclamação ou financeiro) e gera protocolo. "
            "Use quando o cliente confirmar que deseja seguir com a troca/devolução ou reportar problema.",
            {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["troca", "devolucao", "reclamacao", "financeiro", "outro"]},
                    "descricao": {"type": "string", "description": "Resumo objetivo do pedido do cliente"},
                    "codigo_pedido": {"type": "string"},
                },
                "required": ["tipo", "descricao"],
            },
            abrir_solicitacao,
        ),
        ToolSpec(
            "transferir_para_humano",
            "Transfere a conversa para um atendente humano. Use quando o cliente pedir, estiver muito "
            "insatisfeito, citar órgãos de defesa do consumidor, ou quando você não puder resolver.",
            {
                "type": "object",
                "properties": {
                    "motivo": {"type": "string"},
                    "prioridade": {"type": "string", "enum": ["normal", "high", "urgent"]},
                },
                "required": ["motivo"],
            },
            transferir_para_humano,
        ),
    ]
}


def run_tool(ctx: ToolContext, name: str, args: dict) -> ToolCall:
    start = time.perf_counter()
    spec = TOOLS.get(name)
    if not spec:
        return ToolCall(name, args, None, 0, error=f"Ferramenta desconhecida: {name}")
    try:
        result = spec.handler(ctx, **args)
        return ToolCall(name, args, result, (time.perf_counter() - start) * 1000)
    except TypeError as exc:  # argumentos inválidos vindos do modelo
        return ToolCall(name, args, None, (time.perf_counter() - start) * 1000, error=str(exc))


def anthropic_tools() -> list[dict]:
    return [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in TOOLS.values()]


def openai_tools() -> list[dict]:
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
        for t in TOOLS.values()
    ]
