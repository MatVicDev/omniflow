# OmniFlow

**Atendimento omnichannel com agente de IA.** WhatsApp, Instagram, chat do site e e-mail chegam numa caixa de entrada única. Um agente de IA responde, consulta pedidos, abre protocolos e, quando precisa, passa a conversa para um humano já com o resumo pronto.

> Projeto fictício de portfólio. A demo simula a **Aurora Cosméticos**, um e-commerce de skincare com 60 dias de histórico, mais de 90 clientes, pedidos reais no banco, catálogo e base de conhecimento.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_18-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_4-06B6D4?logo=tailwindcss&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Opus_5.5-D97757)
![Testes](https://img.shields.io/badge/testes-34_passando-1baf7a)

---

## Sumário

- [O problema e a solução](#o-problema-e-a-solução)
- [Funcionalidades](#funcionalidades)
- [Como rodar](#como-rodar)
- [Motores de IA](#motores-de-ia)
- [Roteiro de demonstração](#roteiro-de-demonstração)
- [Arquitetura](#arquitetura)
- [Como uma mensagem é processada](#como-uma-mensagem-é-processada)
- [Ferramentas do agente](#ferramentas-do-agente-function-calling)
- [Regras de segurança (guardrails)](#regras-de-segurança-guardrails)
- [Automações](#automações)
- [Base de conhecimento e busca (RAG)](#base-de-conhecimento-e-busca-rag)
- [Integração com WhatsApp](#integração-com-whatsapp-cloud-api)
- [API](#api)
- [Tempo real](#tempo-real-websocket)
- [Modelo de dados](#modelo-de-dados)
- [Configuração](#configuração)
- [Qualidade e testes](#qualidade-e-testes)
- [Deploy com Docker](#deploy-com-docker)
- [Decisões técnicas](#decisões-técnicas)
- [Próximos passos](#próximos-passos)

---

## O problema e a solução

Uma loja online que atende por vários canais costuma ter:

- mensagens espalhadas entre o celular do WhatsApp, o Direct do Instagram, o chat do site e a caixa de e-mail;
- a equipe respondendo dezenas de vezes as mesmas perguntas: *"cadê meu pedido?"*, *"posso trocar?"*, *"parcela em quantas vezes?"*;
- cliente irritado esperando na fila enquanto o atendente procura o pedido em outro sistema;
- nenhum número confiável sobre volume, tempo de resposta ou satisfação.

O **OmniFlow** resolve isso em três camadas:

| Camada | O que faz |
|---|---|
| **Agente de IA** | Responde na hora, 24h, no tom de cada canal. Usa a base de conhecimento oficial e consulta dados reais (pedidos, produtos). Nunca inventa política. |
| **Equipe humana** | Recebe só o que precisa de gente, já priorizado e com resumo. Tem um copiloto que sugere respostas. |
| **Gestão** | Painel com indicadores, assuntos mais comuns, motivos de transferência, horários de pico e desempenho da equipe. |

---

## Funcionalidades

### Visão geral (dashboard)
- **Indicadores** comparados ao período anterior: conversas, % resolvidas pela IA, tempo da 1ª resposta, CSAT e horas de equipe economizadas.
- **Ao vivo:** quantas conversas estão com a IA, na fila e com humanos agora.
- **Volume diário por canal** em barras empilhadas, com tooltip.
- **Assuntos mais comuns**, detectados pela IA.
- **Motivos de transferência** para humano.
- **Distribuição de sentimento** dos clientes.
- **Mapa de calor** de horário × dia da semana (fuso de Brasília).
- **Tabela da equipe:** atendimentos, tempo de resposta e CSAT de cada pessoa.
- Filtro de período: 7, 30 ou 60 dias.

### Inbox
- Abas **Fila**, **Comigo**, **IA**, **Abertas** e **Encerradas**, com filtro por canal e busca.
- Atualização **em tempo real**: novas mensagens e mudanças de status aparecem sem recarregar.
- Ordenação por **prioridade** (urgente → alta → normal) e por tempo de espera.
- Ações: **assumir**, **devolver para a IA** e **encerrar**.
- **Copiloto:** sugere a próxima resposta com base no histórico e na base de conhecimento.
- **Ver raciocínio** em cada resposta da IA: intenção detectada, sentimento, regras acionadas, ferramentas chamadas com entrada e saída, trechos da base usados e tempo de resposta.
- **Painel do cliente:** resumo da conversa feito pela IA, pedidos, protocolos abertos e histórico.

### Simulador de canais
A principal peça da demo. Você conversa **como cliente** e vê a IA trabalhando.
- **5 personas** com cenários prontos: cliente VIP com entrega atrasada, produto que chegou vazando, cancelamento de pedido, dúvidas de produto pelo Instagram e visitante anônimo do site.
- Aparelho simulado com o visual de **WhatsApp, Instagram, chat do site ou e-mail**. A resposta muda de formato em cada canal.
- Sugestões de mensagem em um clique.
- **Bastidores da IA**, um painel lateral com a linha do tempo completa de cada decisão.
- As conversas do simulador aparecem na Inbox ao mesmo tempo.

### Base de conhecimento
- Cadastro, edição, ativação e exclusão de artigos, com categoria e tags.
- **Reindexação imediata:** a IA usa a versão nova já na próxima mensagem.
- **Playground de busca (RAG):** digite uma pergunta de cliente e veja quais trechos a IA encontraria e com que pontuação.
- Contador de uso de cada artigo.

### Automações
- 6 fluxos desenhados como diagrama (gatilho → condição → IA → ação → humano).
- **Liga e desliga** com efeito imediato no comportamento do agente.
- Contador de execuções.

### Agente de IA (configurações)
- Nome do assistente, saudação, tom de voz (amigável, profissional ou descontraído) e instruções personalizadas.
- **Sensibilidade do transbordo:** a partir de qual nível de insatisfação a conversa vai para humano.
- Quantas respostas sem confiança a IA tolera antes de transferir.
- Encerramento automático quando o cliente agradece e pesquisa de satisfação (CSAT).
- Horário de atendimento da equipe.
- Status do motor de IA em uso e das integrações.

---

## Como rodar

### Requisitos
- Python **3.11+**
- Node **20+**

### Um comando

```bash
./start.sh
```

| Endereço | O quê |
|---|---|
| http://localhost:5173 | Painel |
| http://localhost:8000/docs | Documentação interativa da API (Swagger) |

Na primeira execução o script cria o ambiente Python (`backend/.venv`), instala as dependências do backend e do frontend e copia `backend/.env.example` para `backend/.env`. O banco SQLite é criado e preenchido com dados de demonstração automaticamente.

**Não precisa de chave de API.** Sem chave, o motor local de IA assume e a demo inteira funciona offline.

### Comandos úteis

| Comando | O que faz |
|---|---|
| `make dev` | O mesmo que `./start.sh` |
| `make test` | Roda os testes do backend (pytest) |
| `make lint` | Lint do backend (ruff) |
| `make typecheck` | Checagem de tipos do frontend (`tsc`) |
| `make build` | Build de produção do frontend |
| `make docker` | Sobe tudo com Docker em http://localhost:8080 |
| `make reset` | Apaga o banco local. Ele é recriado com os dados de demo no próximo start |

O botão **Reiniciar demo**, no rodapé do menu lateral, faz o mesmo reset sem reiniciar o servidor.

### Rodando manualmente

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend, em outro terminal
cd frontend
npm install
npm run dev
```

---

## Motores de IA

A camada de IA não depende de um fornecedor. Os três motores implementam a mesma interface (`LLMProvider`) e usam as mesmas ferramentas.

| Motor | Como ativar | Características |
|---|---|---|
| **Motor local** | Padrão, sem chave | Classificador de intenção e sentimento em PT-BR, extração de entidades (código de pedido, e-mail, CEP), busca BM25 na base de conhecimento e respostas por modelo. Sem custo, sem internet, resposta em milissegundos. |
| **Claude (Anthropic)** | `ANTHROPIC_API_KEY=...` | Modelo `claude-opus-5-5` por padrão. Chamada de ferramentas em várias rodadas, cache de prompt no trecho fixo do sistema, esforço `low` para respostas rápidas e fallback de modelo no servidor. |
| **OpenAI** | `OPENAI_API_KEY=...` | Chat Completions com ferramentas. Modelo configurável em `OPENAI_MODEL`. |

Com `AI_PROVIDER=auto` (padrão), o sistema escolhe nesta ordem: Claude se houver chave, depois OpenAI, depois o motor local. Também dá para forçar um motor com `AI_PROVIDER=anthropic | openai | offline`.

**Tolerância a falhas:** se o provedor externo falhar (chave inválida, limite de uso, rede), o motor local responde no lugar. O cliente não percebe, e o erro fica registrado no raciocínio da mensagem (`fallback_error`) para a equipe ver.

---

## Roteiro de demonstração

Um roteiro de cerca de 5 minutos para apresentar o produto.

1. **Visão geral:** mostre a taxa de resolução da IA subindo, a economia em horas e o mapa de calor.
2. **Simulador → Juliana (WhatsApp, cliente VIP):**
   - *"meu pedido ainda não chegou"* → a IA identifica a cliente, consulta o pedido `AUR-10482` e informa que está atrasado, com a transportadora e o código de rastreio.
   - *"quero o reembolso então"* → a IA explica a política e abre um protocolo.
   - Abra **Bastidores da IA** e mostre a intenção, o sentimento, a ferramenta `consultar_pedido` com o JSON retornado e os trechos da base usados.
3. **Simulador → Fernanda:** *"O sérum chegou vazando, quero trocar"* → protocolo de troca aberto com número `OF-AAMM-####`.
4. **Simulador → Marcos (e-mail):** *"Quero cancelar o pedido AUR-10533"*. A resposta vem com saudação e assinatura, no formato de e-mail.
5. **Escalonamento:** em qualquer persona, escreva *"vou abrir reclamação no Procon"*. A conversa vai para a fila como **urgente**, com a tag `risco-reputacao`.
6. **Inbox:** abra a conversa urgente, mostre o resumo pronto, clique em **Assumir** e use o **Copiloto** para sugerir a resposta. Encerre.
7. **Satisfação:** de volta ao simulador, mande *"obrigada!"*. A IA encerra e pede uma nota de 1 a 5. Responda *"5"*.
8. **Automações:** desligue *Transbordo inteligente* e mostre que a mesma mensagem negativa não transfere mais.
9. **Base de conhecimento:** edite um artigo, salve e pergunte a mesma coisa no simulador. A resposta já reflete a mudança.

---

## Arquitetura

```
┌───────────────── Canais ─────────────────┐
│  WhatsApp (Cloud API) · Instagram ·       │
│  Chat do site · E-mail · Simulador        │
└───────────────────┬──────────────────────┘
                    │ POST /api/channels/{canal}/inbound
                    │ POST /webhooks/whatsapp
                    ▼
┌──────────────────────────────── Backend (FastAPI) ─────────────────────────────┐
│                                                                                │
│   Orquestrador (services/agent.py)                                             │
│     │                                                                          │
│     ├─ NLU ─────────── intenção · sentimento · entidades · termos críticos     │
│     ├─ Guardrails ──── regras fixas de transbordo e prioridade                 │
│     ├─ Motor de IA ─── Claude │ OpenAI │ Motor local  (+ fallback automático)  │
│     │     └─ Ferramentas: base de conhecimento · pedidos · produtos ·          │
│     │                     protocolos · transferência                           │
│     ├─ Fluxos ──────── boas-vindas · fora do horário · rastreio · CSAT …       │
│     └─ Persistência ── conversa, mensagem + raciocínio (trace)                 │
│                                                                                │
│   Hub em tempo real (WebSocket /ws) ──────────────────────────────┐            │
│   Analytics · Copiloto · Base de conhecimento (BM25)              │            │
│   SQLite (WAL) via SQLAlchemy 2.0                                 │            │
└───────────────────────────────────────────────────────────────────┼────────────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
┌──────────────── Frontend (React + TypeScript + Vite) ────────────────┐
│  Visão geral · Inbox · Simulador · Base de conhecimento ·            │
│  Automações · Agente de IA                                           │
└──────────────────────────────────────────────────────────────────────┘
```

### Estrutura de pastas

```
omniflow/
├── backend/
│   ├── app/
│   │   ├── main.py                 Aplicação FastAPI, CORS, rotas, WebSocket, seed na inicialização
│   │   ├── models.py               Modelos SQLAlchemy (tipados com Mapped)
│   │   ├── schemas.py              Contratos Pydantic de entrada
│   │   ├── serializers.py          Saída da API
│   │   ├── realtime.py             Hub de eventos WebSocket
│   │   ├── db.py                   Engine, sessão, pragmas do SQLite
│   │   ├── seed.py · seed_data.py  Geração dos dados de demonstração
│   │   ├── core/                   Configuração (pydantic-settings) e logging
│   │   ├── api/
│   │   │   ├── conversations.py    Inbox: listar, detalhar, responder, assumir, encerrar, copiloto
│   │   │   ├── channels.py         Entrada de mensagens e webhook do WhatsApp
│   │   │   ├── knowledge.py        CRUD da base e playground de busca
│   │   │   └── workspace.py        Analytics, fluxos, configurações, equipe, demo
│   │   └── services/
│   │       ├── agent.py            Orquestrador: o caminho completo de uma mensagem
│   │       ├── nlu.py              Intenção, sentimento e entidades em PT-BR
│   │       ├── retrieval.py        Índice BM25 da base de conhecimento
│   │       ├── tools.py            Ferramentas do agente (schema único para todos os motores)
│   │       ├── flows.py            Motor de automações
│   │       ├── copilot.py          Resumo e sugestão de resposta
│   │       ├── analytics.py        Indicadores do dashboard
│   │       ├── channels.py         Envio de mensagens (WhatsApp Graph API)
│   │       ├── settings_store.py   Configurações do agente
│   │       └── ai/
│   │           ├── base.py         Interface LLMProvider
│   │           ├── prompts.py      Prompt de sistema (parte fixa e cacheável + contexto)
│   │           ├── anthropic_provider.py
│   │           ├── openai_provider.py
│   │           ├── offline.py      Motor local
│   │           └── factory.py      Seleção do motor
│   ├── tests/                      pytest: NLU, busca e API ponta a ponta
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 Layout, menu lateral e rotas (páginas com carregamento sob demanda)
│   │   ├── pages/                  Dashboard, Inbox, Simulator, Knowledge, Flows, Settings
│   │   ├── components/             AiTrace (raciocínio), MessageBubble, componentes de UI
│   │   └── lib/                    Cliente da API tipado, tipos, tempo real, formatação
│   ├── Dockerfile · nginx.conf     Build estático servido por Nginx
│   └── vite.config.ts              Proxy de /api, /webhooks e /ws para o backend
├── compose.yaml
├── Makefile
└── start.sh
```

### Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, pydantic-settings, httpx, Uvicorn |
| IA | SDK `anthropic`, SDK `openai`, NLU e BM25 próprios |
| Banco | SQLite em modo WAL. Troca para PostgreSQL via `DATABASE_URL` |
| Frontend | React 18, TypeScript, Vite 6, Tailwind CSS 4, React Router 6, Recharts, lucide-react |
| Tempo real | WebSocket nativo com reconexão automática |
| Qualidade | pytest, ruff, `tsc` em modo estrito |
| Infra | Docker (multi-stage), Nginx, Docker Compose |

---

## Como uma mensagem é processada

Todo canal chega ao mesmo ponto, `handle_inbound`, em `services/agent.py`:

1. **Identificação.** O contato é encontrado pelo telefone, @ do Instagram ou e-mail, ou criado. A conversa aberta do canal é retomada ou uma nova é criada.
2. **Entendimento (NLU).** O sistema detecta a intenção (13 categorias: rastreio, troca, cancelamento, pagamento, frete, produto, cupom, reclamação, pedido de atendente…), mede o sentimento de −1 a +1 e extrai entidades como código de pedido, e-mail e CEP.
3. **Guardrails.** Regras fixas, que não dependem do modelo, decidem se a conversa precisa ir direto para humano. Veja [abaixo](#regras-de-segurança-guardrails).
4. **Motor de IA.** O modelo recebe o prompt de sistema, o contexto do cliente (pedidos recentes, canal, horário) e o histórico, e decide se responde direto ou chama ferramentas. Pode fazer até 5 rodadas de ferramentas.
5. **Confiança.** Respostas com baixa confiança somam um contador. Ao atingir o limite configurado, a conversa é transferida.
6. **Automações.** Os fluxos ativos ajustam o resultado: saudação na primeira mensagem, aviso fora do horário, transbordo e escalonamento.
7. **Registro.** A mensagem é salva com o **raciocínio completo** (`meta`): intenção, sentimento, regras, ferramentas com entrada e saída, fontes, motor, latência, tokens e eventual erro de fallback.
8. **Publicação.** Os eventos `message.created` e `conversation.updated` vão para todos os painéis abertos via WebSocket.
9. **Encerramento.** Se o cliente agradece e o assunto está resolvido, a conversa é encerrada e a pesquisa de satisfação é enviada. Uma nota de 1 a 5 nas 24 horas seguintes é registrada como CSAT.

### Adaptação por canal

| Canal | Estilo da resposta |
|---|---|
| WhatsApp | Curta, com *negrito* e quebras de linha |
| Instagram | Curta e informal |
| Chat do site | Direta, sem formatação de WhatsApp |
| E-mail | Saudação, parágrafos completos e assinatura |

---

## Ferramentas do agente (function calling)

As ferramentas são definidas **uma vez**, num schema JSON único, e convertidas automaticamente para o formato de cada provedor (`anthropic_tools()` e `openai_tools()` em `services/tools.py`). O motor local usa as mesmas funções.

| Ferramenta | O que faz | Segurança |
|---|---|---|
| `buscar_base_conhecimento` | Busca trechos relevantes nos artigos ativos | Só conteúdo oficial; a IA é instruída a não inventar política |
| `consultar_pedido` | Status, itens, transportadora, rastreio e previsão de entrega | **Só pedidos do próprio cliente da conversa** |
| `consultar_produto` | Busca no catálogo: preço, estoque, indicação | Somente leitura |
| `abrir_solicitacao` | Abre protocolo de troca, devolução, reembolso etc. | Gera número `OF-AAMM-####` e vincula à conversa |
| `transferir_para_humano` | Passa a conversa para a fila com motivo e resumo | Muda o status e notifica a equipe |

---

## Regras de segurança (guardrails)

Algumas decisões não podem depender do humor do modelo. Estas regras rodam **antes** da IA:

| Regra | Gatilho | Resultado |
|---|---|---|
| **Risco de reputação** | Termos como *Procon*, *Reclame Aqui*, *advogado*, *processar*, *chargeback* | Fila com prioridade **urgente** e tag `risco-reputacao` |
| **Pedido de atendente** | *"quero falar com uma pessoa"*, *"atendente"* | Transferência imediata |
| **Insatisfação** | Sentimento abaixo do limite configurado (padrão −0,55) | Transferência com prioridade alta (depende do fluxo *Transbordo inteligente*) |
| **Baixa confiança** | N respostas seguidas sem confiança (padrão 2) | Transferência |

Toda transferência leva um **resumo automático** para o atendente não precisar ler a conversa inteira.

---

## Automações

| Fluxo | Gatilho | O que faz |
|---|---|---|
| **Boas-vindas personalizada** | Primeira mensagem | Cumprimenta pelo nome, no tom configurado |
| **Transbordo inteligente** | Sentimento negativo ou baixa confiança | Transfere para humano com resumo |
| **Escalonamento de risco de reputação** | Termo crítico | Prioridade urgente e tag de risco |
| **Rastreio automático de pedidos** | Pergunta sobre entrega | Consulta o pedido e responde com status e rastreio |
| **Aviso fora do horário** | Transferência fora do expediente | Informa quando a equipe volta |
| **Pesquisa de satisfação (CSAT)** | Conversa encerrada | Pede uma nota de 1 a 5 e registra |

Cada fluxo é guardado com nós e conexões (`nodes`/`edges` com coordenadas) e desenhado em SVG na tela de Automações.

---

## Base de conhecimento e busca (RAG)

A busca é feita em `services/retrieval.py`, sem dependências externas:

- Cada artigo é dividido em **trechos por parágrafo**. Título e tags entram no índice de cada trecho.
- Ranking **BM25** com normalização para português: remoção de acentos e stopwords, sinônimos (*"chegar"* ~ *"entrega"*, *"correios"* ~ *"transportadora"*), famílias de palavras (*parcela*, *parcelar*, *parcelamento*) e radicalização leve.
- A pontuação final combina a **cobertura** dos termos da pergunta com o BM25 normalizado, numa escala de 0 a 1.
- O motor local só usa trechos acima de **38%**. Abaixo disso, oferece um especialista em vez de arriscar.
- O índice é **reconstruído** sempre que um artigo é criado, editado ou excluído.

Com Claude ou OpenAI, a mesma busca é exposta como a ferramenta `buscar_base_conhecimento`, e as fontes usadas aparecem no raciocínio da mensagem.

---

## Integração com WhatsApp Cloud API

O webhook já segue o formato oficial da Meta.

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/webhooks/whatsapp` | Verificação (`hub.mode`, `hub.verify_token`, `hub.challenge`) |
| `POST` | `/webhooks/whatsapp` | Recebimento de mensagens |

Para ligar a um número real:

1. Crie um app no Meta for Developers com o produto WhatsApp.
2. Preencha no `backend/.env`: `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.
3. Exponha a API publicamente (por exemplo, com um túnel) e cadastre `https://SEU-DOMINIO/webhooks/whatsapp` como URL do webhook.

As mensagens recebidas aparecem na Inbox com a tag `whatsapp-cloud`. As respostas, da IA ou de um atendente, saem pela Graph API.

---

## API

Documentação interativa completa em **http://localhost:8000/docs**.

### Conversas — `/api/conversations`

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/conversations` | Lista com filtros `status` (`bot`, `waiting`, `human`, `resolved`, `open`), `channel`, `q` e `assigned_to`. Inclui contadores por aba |
| `GET` | `/api/conversations/{id}` | Conversa com mensagens, contato, pedidos e protocolos |
| `POST` | `/api/conversations/{id}/messages` | Atendente envia mensagem |
| `POST` | `/api/conversations/{id}/assign` | Atribui a um atendente |
| `POST` | `/api/conversations/{id}/resolve` | Encerra |
| `POST` | `/api/conversations/{id}/return-to-bot` | Devolve para a IA |
| `POST` | `/api/conversations/{id}/read` | Marca como lida |
| `POST` | `/api/conversations/{id}/copilot/suggest` | Sugestão de resposta |
| `POST` | `/api/conversations/{id}/copilot/summarize` | Resumo da conversa |

### Canais

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/channels/{channel}/inbound` | Mensagem de cliente em `whatsapp`, `instagram`, `webchat` ou `email` |
| `GET`/`POST` | `/webhooks/whatsapp` | Webhook da WhatsApp Cloud API |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/channels/whatsapp/inbound \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5511988887777", "name": "Cliente Teste", "text": "qual o prazo de entrega para Curitiba?"}'
```

A resposta traz a mensagem do cliente, a resposta do agente com o raciocínio completo e o estado atualizado da conversa.

### Base de conhecimento — `/api/knowledge`

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/knowledge` | Lista artigos |
| `POST` | `/api/knowledge` | Cria (e reindexa) |
| `PUT` | `/api/knowledge/{id}` | Atualiza (e reindexa) |
| `DELETE` | `/api/knowledge/{id}` | Exclui (e reindexa) |
| `POST` | `/api/knowledge/search` | Playground: testa a busca usada pela IA |

### Workspace — `/api`

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/analytics/overview?days=30` | Todos os indicadores do dashboard |
| `GET` | `/api/flows` | Automações |
| `PATCH` | `/api/flows/{id}` | Liga ou desliga uma automação |
| `GET` | `/api/settings` | Configurações do agente e motor de IA ativo |
| `PATCH` | `/api/settings` | Atualiza configurações |
| `GET` | `/api/agents` | Equipe |
| `GET` | `/api/contacts` | Contatos |
| `GET` | `/api/tickets` | Protocolos |
| `GET` | `/api/demo/personas` | Personas do simulador |
| `POST` | `/api/demo/reset` | Restaura os dados de demonstração |
| `GET` | `/api/health` | Status da API e do motor de IA |

---

## Tempo real (WebSocket)

Conecte em `ws://localhost:8000/ws`. Cada evento é um JSON `{"event": "...", "data": {...}}`.

| Evento | Quando |
|---|---|
| `message.created` | Nova mensagem de cliente, IA ou atendente |
| `conversation.updated` | Mudança de status, prioridade, atribuição, sentimento ou resumo |
| `typing` | Indicador de "digitando" |
| `demo.reset` | Dados de demonstração restaurados (os painéis recarregam) |

No frontend, o `RealtimeProvider` mantém uma única conexão, reconecta sozinho e distribui os eventos pelo hook `useEvent`.

---

## Modelo de dados

| Entidade | Principais campos |
|---|---|
| **Agent** | Atendente: nome, e-mail, papel (supervisor/agente), equipe, status |
| **Contact** | Cliente: nome, telefone, e-mail, @ do Instagram, cidade, tags (ex.: `vip`), valor gasto na loja |
| **Conversation** | Canal, status (`bot`, `waiting`, `human`, `resolved`), prioridade, intenção, sentimento, resumo, motivo de transferência, falhas da IA, quem resolveu, CSAT, tempo da 1ª resposta |
| **Message** | Autor (cliente, IA, atendente, sistema), texto e `meta` com o raciocínio completo da IA |
| **Ticket** | Protocolo: tipo, status, descrição, vínculo com a conversa |
| **KnowledgeArticle** | Título, categoria, conteúdo, tags, ativo, contagem de uso |
| **Flow** | Automação: gatilho, nós e conexões, ativo, execuções |
| **Product** · **Order** | Catálogo e pedidos usados pelas ferramentas |
| **Setting** | Configurações do agente em chave e valor |

### Dados de demonstração

- **60 dias** de histórico com volume crescente e taxa de resolução da IA subindo de cerca de 60% para 76%.
- **5 atendentes**, **17 produtos**, **14 artigos** e **6 automações**.
- Mais de **90 clientes** com pedidos em vários estados (pago, enviado, atrasado, entregue).
- Conversas ao vivo geradas pelo **próprio orquestrador**, não escritas à mão, então o raciocínio de cada mensagem é real.

---

## Configuração

Variáveis em `backend/.env`. O modelo está em `backend/.env.example`.

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./omniflow.db` | Banco de dados |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Origens liberadas |
| `AI_PROVIDER` | `auto` | `auto`, `anthropic`, `openai` ou `offline` |
| `ANTHROPIC_API_KEY` | vazio | Chave da Anthropic |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Modelo Claude |
| `OPENAI_API_KEY` | vazio | Chave da OpenAI |
| `OPENAI_MODEL` | `gpt-5-mini` | Modelo OpenAI |
| `WHATSAPP_VERIFY_TOKEN` | `omniflow-verify` | Token de verificação do webhook |
| `WHATSAPP_TOKEN` | vazio | Token de acesso da Graph API |
| `WHATSAPP_PHONE_NUMBER_ID` | vazio | ID do número no WhatsApp Business |

No frontend, `VITE_API_URL` muda o destino do proxy de desenvolvimento (padrão: `http://localhost:8000`).

---

## Qualidade e testes

```bash
make test        # 34 testes
make lint        # ruff
make typecheck   # tsc
```

Os testes rodam com banco temporário e motor local, então não precisam de rede nem de chave. Eles cobrem:

- **NLU:** intenção, sentimento (incluindo negação e emojis) e extração de entidades;
- **Busca:** relevância dos trechos para perguntas reais de cliente;
- **API ponta a ponta:**
  - rastreio de pedido atrasado;
  - proteção de dados (o cliente não consulta pedido de outra pessoa);
  - resposta com fonte da base;
  - abertura de protocolo de troca;
  - cancelamento no formato de e-mail;
  - transferência com resumo;
  - escalonamento urgente por termo crítico;
  - agradecimento → encerramento → CSAT;
  - atendente assumindo, usando o copiloto e encerrando;
  - CRUD da base de conhecimento;
  - formato do analytics;
  - liga/desliga de fluxo;
  - webhook do WhatsApp.

---

## Deploy com Docker

```bash
docker compose up --build
```

Abra **http://localhost:8080**.

- **api:** imagem Python 3.12 slim com Uvicorn. O banco fica no volume `omniflow-data`.
- **web:** build do frontend em Node, servido por Nginx, que também faz proxy de `/api`, `/webhooks` e `/ws` para a API.

As variáveis são lidas de `backend/.env`, se existir.

---

## Decisões técnicas

- **IA independente de fornecedor.** Uma interface, três motores e um schema único de ferramentas. Trocar de modelo é mudar uma variável de ambiente.
- **Funciona sem chave.** O motor local garante que a demo, os testes e o produto continuem funcionando se a API externa cair.
- **Guardrails fora do modelo.** Prioridade, risco jurídico e pedido de humano são decididos por regra, de forma previsível e auditável.
- **Raciocínio auditável.** Cada resposta guarda o porquê: o que foi entendido, o que foi consultado e qual fonte foi usada. Isso dá confiança para a equipe e facilita ajustar a base.
- **Prompt em duas partes.** A parte fixa do prompt de sistema é cacheável, e o contexto que muda (cliente, pedidos, horário) vai separado. Isso reduz custo e latência com Claude.
- **Dados de demo gerados pelo sistema real.** As conversas ao vivo passam pelo orquestrador de verdade, então o que aparece na demo é o comportamento real do produto.
- **Banco simples, fácil de trocar.** SQLite em WAL para a demo, com SQLAlchemy 2.0 tipado, pronto para PostgreSQL.

---

## Próximos passos

Caminhos naturais para um produto em produção:

- Autenticação e múltiplas empresas (multi-tenant).
- Instagram Graph API e caixa de e-mail (IMAP/SMTP) como canais reais.
- PostgreSQL com busca vetorial (pgvector) somada ao BM25.
- Fila de mensagens (Redis) para processar alto volume.
- Respostas em streaming no chat do site.
- Widget de chat embutível com uma linha de `<script>`.
- Integração com plataformas de e-commerce (Shopify, Nuvemshop, VTEX).

---

<sub>Projeto fictício desenvolvido para portfólio. A Aurora Cosméticos, os clientes e os pedidos são inventados.</sub>
