"""Conteúdo de demonstração: Aurora Cosméticos (e-commerce fictício)."""

AGENTS = [
    ("Ana Ribeiro", "ana.ribeiro@aurora.com.br", "supervisor", "Supervisão", "online", "#7c3aed"),
    ("Bruno Tavares", "bruno.tavares@aurora.com.br", "agent", "Pós-venda", "online", "#0ea5e9"),
    ("Carla Mendes", "carla.mendes@aurora.com.br", "agent", "Pós-venda", "online", "#f59e0b"),
    ("Diego Souza", "diego.souza@aurora.com.br", "agent", "Financeiro", "away", "#10b981"),
    ("Elisa Nakamura", "elisa.nakamura@aurora.com.br", "agent", "Consultoria de produtos", "offline", "#ec4899"),
]

PRODUCTS = [
    ("AUR-SR01", "Sérum Vitamina C 10%", "Skincare", 89.90, 142,
     "Antioxidante para uniformizar o tom e dar viço. Indicado para todos os tipos de pele."),
    ("AUR-SR02", "Sérum Niacinamida 5% + Zinco", "Skincare", 79.90, 96,
     "Controla oleosidade e minimiza poros. Ideal para pele oleosa e com tendência à acne."),
    ("AUR-SR03", "Sérum Ácido Hialurônico", "Skincare", 84.90, 0,
     "Hidratação profunda e efeito preenchedor. Para pele seca ou desidratada."),
    ("AUR-HD01", "Hidratante Facial Oil-Free", "Skincare", 69.90, 210,
     "Textura gel leve, toque seco. Hidrata sem pesar — perfeito para pele oleosa e mista."),
    ("AUR-HD02", "Creme Hidratante Manteiga de Karité", "Skincare", 74.90, 88,
     "Nutrição intensa para pele seca, com manteiga de karité e óleo de amêndoas."),
    ("AUR-PS01", "Protetor Solar Facial FPS 50 Toque Seco", "Proteção solar", 64.90, 320,
     "Alta proteção UVA/UVB, sem cor, não deixa a pele branca. Pode ser usado como base de maquiagem."),
    ("AUR-PS02", "Protetor Solar com Cor FPS 60", "Proteção solar", 72.90, 75,
     "Proteção e cobertura leve em 6 tons. Resistente à água e ao suor."),
    ("AUR-LP01", "Gel de Limpeza Facial Purificante", "Skincare", 49.90, 180,
     "Limpeza suave com extrato de chá verde. Remove o excesso de oleosidade sem ressecar."),
    ("AUR-CB01", "Shampoo Sólido Hidratação", "Cabelos", 39.90, 140,
     "Sem sulfatos, rende até 80 lavagens. Para cabelos secos e com frizz."),
    ("AUR-CB02", "Máscara Capilar Reconstrução", "Cabelos", 59.90, 64,
     "Reconstrução com queratina vegetal para cabelos danificados por química."),
    ("AUR-CB03", "Óleo Capilar Finalizador", "Cabelos", 54.90, 120,
     "Brilho e controle do frizz com óleo de argan e pracaxi."),
    ("AUR-CP01", "Óleo Corporal Relaxante Lavanda", "Corpo", 59.90, 90,
     "Hidratação e aroma relaxante. Absorção rápida, não deixa a pele grudenta."),
    ("AUR-CP02", "Esfoliante Corporal Café & Coco", "Corpo", 44.90, 0,
     "Esfoliação natural com café e óleo de coco para uma pele macia."),
    ("AUR-MK01", "Batom Líquido Matte Nude Rosé", "Maquiagem", 42.90, 150,
     "Longa duração, não transfere e não resseca os lábios."),
    ("AUR-MK02", "Máscara de Cílios Volume Vegano", "Maquiagem", 49.90, 98,
     "Volume e alongamento com cera de carnaúba. Fórmula vegana."),
    ("AUR-KT01", "Kit Rotina Pele Oleosa", "Kits", 179.90, 40,
     "Gel de limpeza + Sérum Niacinamida + Hidratante Oil-Free + Protetor FPS 50. Economia de 22%."),
    ("AUR-KT02", "Kit Glow Vitamina C", "Kits", 199.90, 25,
     "Sérum Vitamina C + Creme Karité + Protetor com Cor. Ideal para presente."),
]

KNOWLEDGE = [
    ("Política de trocas e devoluções", "Pós-venda", ["troca", "devolução", "prazo"],
     """Você pode solicitar a troca ou devolução de qualquer produto em até 30 dias corridos após o recebimento, desde que o produto esteja lacrado e sem sinais de uso.

Para iniciar, basta informar o código do pedido e o motivo. Enviamos por e-mail uma etiqueta de postagem reversa gratuita — é só levar o pacote a uma agência dos Correios.

Após recebermos o produto no nosso centro de distribuição, a troca é despachada em até 2 dias úteis. Na devolução, o reembolso é feito na mesma forma de pagamento da compra."""),
    ("Direito de arrependimento", "Pós-venda", ["arrependimento", "devolução", "7 dias", "cdc"],
     """Pelo Código de Defesa do Consumidor, compras online podem ser devolvidas em até 7 dias após o recebimento, sem necessidade de justificativa, mesmo que o produto tenha sido aberto.

Nesse caso o reembolso é integral, incluindo o valor do frete pago na compra."""),
    ("Produtos com defeito, avaria ou envio errado", "Pós-venda", ["defeito", "quebrado", "vazou", "errado", "avaria"],
     """Se o produto chegou com defeito, avariado, vazando ou diferente do que você comprou, a troca é garantida e sem nenhum custo de frete.

Pedimos apenas uma foto do produto e da embalagem para agilizar a análise. O novo envio sai com prioridade em até 1 dia útil após a aprovação."""),
    ("Prazos e regiões de entrega", "Entrega", ["prazo", "entrega", "regiões", "capitais"],
     """Entregamos em todo o Brasil. O prazo começa a contar após a aprovação do pagamento e varia conforme a região: Sudeste de 2 a 5 dias úteis; Sul e Centro-Oeste de 3 a 7 dias úteis; Nordeste de 4 a 9 dias úteis; Norte de 6 a 12 dias úteis.

Para capitais como Recife, Salvador e Fortaleza o prazo médio é de 5 dias úteis. O prazo exato para o seu CEP aparece no carrinho antes de finalizar a compra."""),
    ("Frete grátis", "Entrega", ["frete grátis", "frete", "gratuito"],
     """O frete é grátis para compras acima de R$ 199 para todo o Brasil. Para membros do Aurora Club o frete grátis vale a partir de R$ 149.

Abaixo desse valor, o frete é calculado no carrinho conforme o CEP e o peso do pedido."""),
    ("Rastreamento de pedidos", "Entrega", ["rastreio", "rastreamento", "código", "transportadora"],
     """Assim que o pedido é despachado, você recebe o código de rastreio por e-mail e WhatsApp. Também é possível acompanhar pelo menu Meus Pedidos no site.

Trabalhamos com Correios, Jadlog e Loggi. As atualizações podem levar até 24 horas para aparecer no site da transportadora após a postagem.

Se a entrega passar do prazo previsto, você pode solicitar reenvio ou reembolso integral após 2 dias úteis de atraso."""),
    ("Formas de pagamento e parcelamento", "Pagamento", ["pix", "cartão", "boleto", "parcelamento"],
     """Aceitamos Pix, cartão de crédito (Visa, Mastercard, Elo, Amex e Hipercard) e boleto bancário.

Pagamentos via Pix têm 5% de desconto e aprovação imediata. No cartão, parcelamos em até 6x sem juros para compras acima de R$ 120. O boleto vence em 2 dias úteis e a aprovação leva até 1 dia útil após o pagamento."""),
    ("Estornos e reembolsos", "Pagamento", ["estorno", "reembolso", "dinheiro de volta"],
     """O reembolso é feito na mesma forma de pagamento da compra. No Pix, o valor é devolvido em até 24 horas após a aprovação da solicitação.

No cartão de crédito, o estorno é solicitado à operadora em até 2 dias úteis e pode aparecer em até 2 faturas, dependendo da data de fechamento do cartão. No boleto, o reembolso é feito por transferência bancária em até 5 dias úteis."""),
    ("Cancelamento de pedidos", "Pedidos", ["cancelamento", "cancelar"],
     """Pedidos podem ser cancelados sem custo enquanto estiverem com status Pagamento aprovado ou Em separação. O estorno segue os prazos da forma de pagamento utilizada.

Se o pedido já foi enviado, não é possível cancelar pelo sistema: você pode recusar a entrega ou solicitar a devolução gratuita pelo direito de arrependimento em até 7 dias após o recebimento."""),
    ("Cupons e Aurora Club", "Promoções", ["cupom", "desconto", "fidelidade", "aurora club", "primeira compra"],
     """Na primeira compra, use o cupom BEMVINDA10 para ganhar 10% de desconto em todo o site. Cupons não são cumulativos entre si, mas são válidos junto com o desconto do Pix.

No Aurora Club, nosso programa de fidelidade gratuito, cada R$ 1 vira 1 ponto, e 100 pontos valem R$ 10 em compras. Membros também têm frete grátis a partir de R$ 149 e acesso antecipado a lançamentos."""),
    ("Produtos veganos e cruelty-free", "Produtos", ["vegano", "cruelty-free", "crueldade", "testes em animais", "ingredientes"],
     """Todos os produtos Aurora são 100% veganos e cruelty-free: não usamos ingredientes de origem animal e não realizamos nem encomendamos testes em animais. Somos certificados pelo selo Leaping Bunny.

Nossas fórmulas são livres de parabenos, sulfatos agressivos, petrolatos e corantes artificiais."""),
    ("Como montar uma rotina de skincare", "Produtos", ["skincare", "rotina", "pele oleosa", "pele seca", "acne"],
     """Uma rotina básica tem quatro passos: limpeza, tratamento (sérum), hidratação e protetor solar pela manhã.

Para pele oleosa ou com acne, indicamos o Gel de Limpeza Purificante, o Sérum Niacinamida e o Hidratante Oil-Free. Para pele seca, o Sérum de Ácido Hialurônico e o Creme de Karité. O Sérum Vitamina C é indicado para todos os tipos de pele, preferencialmente pela manhã."""),
    ("Alergias e reações", "Produtos", ["alergia", "reação", "irritação", "sensível"],
     """Todos os produtos são dermatologicamente testados. Mesmo assim, recomendamos fazer um teste de toque no antebraço 24 horas antes do primeiro uso.

Em caso de vermelhidão, coceira ou ardência, suspenda o uso e lave a região com água em abundância. Produtos que causaram reação podem ser devolvidos em até 30 dias, mesmo abertos, com reembolso integral."""),
    ("Horário de atendimento e canais", "Institucional", ["horário", "atendimento", "canais", "contato"],
     """Nossa assistente virtual atende 24 horas por dia, todos os dias, pelo WhatsApp, Instagram, chat do site e e-mail.

A equipe de especialistas atende de segunda a sábado, das 8h às 20h (horário de Brasília). Fora desse horário, os casos transferidos ficam na fila com prioridade para o próximo período."""),
]

FIRST_NAMES = ["Juliana", "Rafael", "Fernanda", "Marcos", "Patrícia", "Lucas", "Camila", "Beatriz", "Thiago", "Larissa", "Gabriel", "Mariana", "Pedro", "Aline", "Felipe", "Bruna", "Gustavo", "Letícia", "Rodrigo", "Natália", "Vinícius", "Isabela", "André", "Carolina", "Leonardo", "Amanda", "Ricardo", "Vanessa", "Eduardo", "Priscila", "Daniel", "Renata", "Matheus", "Tatiane", "Bruno", "Jéssica", "Henrique", "Luana", "Caio", "Débora", "Igor", "Sabrina", "Fábio", "Paula", "Diego", "Raquel", "Murilo", "Simone", "Otávio", "Helena", "Samuel", "Yasmin", "Alexandre", "Cíntia", "Júlio", "Elaine", "Wagner", "Lorena", "Hugo", "Michele"]
LAST_NAMES = ["Martins", "Costa", "Lima", "Oliveira", "Souza", "Almeida", "Ferreira", "Rodrigues", "Gomes", "Ribeiro", "Carvalho", "Pereira", "Barbosa", "Rocha", "Dias", "Teixeira", "Moreira", "Cardoso", "Nunes", "Araújo", "Freitas", "Mendes", "Castro", "Pinto", "Vieira", "Monteiro"]
CITIES = ["São Paulo/SP", "Rio de Janeiro/RJ", "Belo Horizonte/MG", "Curitiba/PR", "Porto Alegre/RS",
          "Recife/PE", "Salvador/BA", "Fortaleza/CE", "Brasília/DF", "Goiânia/GO", "Campinas/SP",
          "Florianópolis/SC", "Manaus/AM", "Belém/PA", "Vitória/ES", "Natal/RN"]

# Conversas históricas: (intenção, desfecho, turnos). c = cliente, b = IA, a = atendente.
# Desfecho "ai" = resolvida pela IA; "human" = transbordo e resolução humana.
HISTORY_TEMPLATES = [
    ("rastreio", "ai", [
        ("c", "Oi! Queria saber onde está meu pedido {pedido}"),
        ("b", "Encontrei seu pedido *{pedido}* 📦\n• Status: *Enviado*\n• Correios — rastreio: {rastreio}\n"
              "• Previsão de entrega: {eta}"),
        ("c", "Ah que ótimo, obrigada!"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."),
    ]),
    ("rastreio", "ai", [
        ("c", "cade meu pedido? comprei semana passada"),
        ("b", "Encontrei seu pedido *{pedido}* 📦\n• Status: *Em separação no estoque*\n\nAssim que for despachado "
              "você recebe o código de rastreio por e-mail e aqui."),
        ("c", "blz, valeu"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."),
    ]),
    ("troca_devolucao", "ai", [
        ("c", "Comprei um protetor e veio a cor errada, quero trocar. Pedido {pedido}"),
        ("b", "Pronto, {nome}! Abri sua solicitação de troca ✅\n• Protocolo: *{protocolo}*\n• Retorno da equipe: "
              "até 2 dias úteis\n\nVocê vai receber por e-mail a etiqueta de postagem gratuita."),
        ("c", "Perfeito, obrigada!"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."),
    ]),
    ("frete_prazo", "ai", [
        ("c", "Qual o valor mínimo para frete grátis?"),
        ("b", "O frete é grátis para compras acima de R$ 199 para todo o Brasil. Para membros do Aurora Club o "
              "frete grátis vale a partir de R$ 149."),
        ("c", "Show, obrigado"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."),
    ]),
    ("pagamento", "ai", [
        ("c", "Vocês parcelam no cartão?"),
        ("b", "Parcelamos em até 6x sem juros para compras acima de R$ 120. E no Pix você ganha 5% de desconto "
              "com aprovação imediata 😉"),
        ("c", "Vou fazer no pix então, valeu!"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜 Se precisar de algo mais, é só chamar."),
    ]),
    ("produto", "ai", [
        ("c", "Tenho pele oleosa, qual sérum vocês recomendam?"),
        ("b", "Separei estas opções pra você:\n\n• *Sérum Niacinamida 5% + Zinco* — R$ 79,90 (em estoque)\n"
              "• *Kit Rotina Pele Oleosa* — R$ 179,90 (em estoque)"),
        ("c", "Amei, vou levar o kit!"),
        ("b", "Ótima escolha! ✨ Qualquer dúvida no uso, é só me chamar."),
    ]),
    ("promocao", "ai", [
        ("c", "Tem cupom de primeira compra?"),
        ("b", "Tem sim! Use o cupom *BEMVINDA10* para ganhar 10% de desconto em todo o site. Ele vale junto com "
              "o desconto do Pix 💜"),
        ("c", "Obrigada!!"),
        ("b", "Imagina, {nome}! Boas compras ✨"),
    ]),
    ("produto", "ai", [
        ("c", "Os produtos de vocês são testados em animais?"),
        ("b", "Não! Todos os produtos Aurora são 100% veganos e cruelty-free, com certificação Leaping Bunny 🐰"),
        ("c", "Que bom, valeu"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜"),
    ]),
    ("cancelamento", "ai", [
        ("c", "Quero cancelar o pedido {pedido}"),
        ("b", "Feito! Solicitei o cancelamento do pedido *{pedido}* ✅\n• Protocolo: *{protocolo}*\n"
              "• Estorno na mesma forma de pagamento. Pix é estornado em até 24h."),
        ("c", "Obrigado pela agilidade"),
        ("b", "Imagina, {nome}! Fico feliz em ajudar 💜"),
    ]),
    ("rastreio", "human", [
        ("c", "Meu pedido {pedido} está atrasado faz uma semana, isso é um absurdo"),
        ("b", "Encontrei seu pedido *{pedido}* 📦\n• Status: *Enviado*\n\nPeço desculpas: a entrega passou do "
              "prazo previsto 😔"),
        ("c", "Quero falar com um atendente agora"),
        ("b", "Claro! Já estou chamando um especialista da equipe. Em instantes alguém continua com você 🙂"),
        ("s", "Conversa transferida para a fila humana · Cliente pediu atendente"),
        ("a", "Oi, {nome}! Aqui é {atendente}, da equipe Aurora. Já acionei a transportadora e vou reenviar seu "
              "pedido hoje com frete expresso, sem custo. Te mando o novo rastreio em instantes."),
        ("c", "Ok, obrigada pela atenção"),
    ]),
    ("troca_devolucao", "human", [
        ("c", "O sérum chegou vazando, a caixa toda melada. Pedido {pedido}"),
        ("b", "Sinto muito pelo transtorno! 😔 Produtos com defeito ou avaria têm troca garantida, sem custo de "
              "frete. Abri a solicitação com o protocolo *{protocolo}*."),
        ("c", "mas eu preciso dele pra sexta, tem como mandar antes?"),
        ("b", "Hmm, não encontrei essa informação com segurança na nossa base 🤔 Para não te deixar sem resposta, "
              "já chamei um especialista da equipe 🙋‍♀️"),
        ("s", "Conversa transferida para a fila humana · IA não encontrou resposta confiável"),
        ("a", "Oi, {nome}! Consegui liberar o envio expresso: chega até quinta-feira. Não precisa devolver o "
              "produto avariado 😉"),
        ("c", "Nossa, perfeito! Muito obrigada"),
    ]),
    ("reclamacao", "human", [
        ("c", "Péssimo atendimento, ninguém resolve meu problema. Vou reclamar no Procon"),
        ("b", "Entendo a seriedade da situação e peço desculpas pelo transtorno. Estou encaminhando seu caso com "
              "prioridade máxima para um especialista."),
        ("s", "Conversa transferida para a fila humana · Risco de reputação (Procon/Reclame Aqui/jurídico)"),
        ("a", "Olá, {nome}. Sou {atendente}, supervisora do atendimento. Analisei seu histórico e já aprovei o "
              "reembolso integral, além de um cupom de R$ 50 pelo transtorno."),
        ("c", "Ok. Pelo menos agora resolveram"),
    ]),
    ("pagamento", "human", [
        ("c", "Fui cobrada duas vezes no cartão pelo mesmo pedido"),
        ("b", "Sinto muito por isso! Vou chamar um especialista do financeiro para verificar a cobrança."),
        ("s", "Conversa transferida para a fila humana · Cobrança em duplicidade"),
        ("a", "Oi, {nome}! Verifiquei aqui: a segunda cobrança foi uma pré-autorização e já foi cancelada. "
              "Ela some da fatura em até 5 dias úteis."),
        ("c", "Ufa, obrigada pela explicação"),
    ]),
    ("outro", "human", [
        ("c", "Vocês vendem para revenda? Tenho uma loja em Goiânia"),
        ("b", "Hmm, não encontrei essa informação com segurança na nossa base 🤔 Para não te deixar sem resposta, "
              "já chamei um especialista da equipe 🙋‍♀️"),
        ("s", "Conversa transferida para a fila humana · IA não encontrou resposta confiável"),
        ("a", "Oi, {nome}! Temos sim um programa para lojistas. Te enviei por e-mail a tabela e as condições 😊"),
        ("c", "Recebi, obrigado!"),
    ]),
]

# Conversas "ao vivo" geradas pelo motor real no seed (traces autênticos).
LIVE_SCRIPTS = [
    # (persona, canal, mensagens do cliente, minutos atrás, atendente que assume)
    ("juliana", "whatsapp", ["oi, meu pedido ainda não chegou 😕"], 6, None),
    ("rafael", "instagram", ["Vocês têm sérum para pele oleosa?"], 11, None),
    ("beatriz", "email", ["Bom dia. Qual o prazo de entrega para Recife?"], 19, None),
    ("patricia", "whatsapp", ["Já é a terceira vez que entro em contato e ninguém resolve. "
                              "Vou abrir reclamação no Reclame Aqui"], 3, None),
    ("lucas", "webchat", ["quero falar com um atendente"], 9, None),
    ("camila", "whatsapp", ["Oi, o hidratante que chegou me deu alergia", "Pedido AUR-10458"], 27, 2),
    ("thiago", "whatsapp", ["vcs aceitam pix? da desconto?"], 34, None),
]

FLOWS = [
    {
        "key": "boas_vindas",
        "name": "Boas-vindas personalizada",
        "description": "Cumprimenta o cliente pelo nome no primeiro contato e já responde à dúvida, sem menus.",
        "trigger": {"type": "first_message", "label": "Primeira mensagem da conversa"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Nova conversa", "detail": "Qualquer canal", "x": 40, "y": 140},
            {"id": "c", "type": "condition", "label": "É só uma saudação?", "detail": "NLU: intenção", "x": 300,
             "y": 140},
            {"id": "m1", "type": "message", "label": "Apresentação", "detail": "Saudação + menu de ajuda", "x": 580,
             "y": 50},
            {"id": "m2", "type": "ai", "label": "Saudação + resposta da IA", "detail": "“Oi, {nome}! …”", "x": 580,
             "y": 230},
            {"id": "e", "type": "end", "label": "Segue com a IA", "detail": "", "x": 860, "y": 140},
        ],
        "edges": [{"from": "t", "to": "c"}, {"from": "c", "to": "m1", "label": "sim"},
                  {"from": "c", "to": "m2", "label": "não"}, {"from": "m1", "to": "e"}, {"from": "m2", "to": "e"}],
    },
    {
        "key": "transbordo_inteligente",
        "name": "Transbordo inteligente",
        "description": "Transfere para humano quando o sentimento cai abaixo do limite ou a IA falha em responder "
                       "com confiança repetidas vezes. O atendente recebe um resumo do caso.",
        "trigger": {"type": "every_message", "label": "Cada mensagem do cliente"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Mensagem recebida", "detail": "", "x": 40, "y": 140},
            {"id": "c1", "type": "condition", "label": "Sentimento ≤ limite?", "detail": "Média móvel", "x": 300,
             "y": 50},
            {"id": "c2", "type": "condition", "label": "Falhas da IA ≥ N?", "detail": "Confiança < 35%", "x": 300,
             "y": 230},
            {"id": "a", "type": "ai", "label": "Resumo para o atendente", "detail": "Copiloto", "x": 580, "y": 140},
            {"id": "h", "type": "handoff", "label": "Fila humana", "detail": "Prioridade alta", "x": 860, "y": 140},
        ],
        "edges": [{"from": "t", "to": "c1"}, {"from": "t", "to": "c2"}, {"from": "c1", "to": "a", "label": "sim"},
                  {"from": "c2", "to": "a", "label": "sim"}, {"from": "a", "to": "h"}],
    },
    {
        "key": "escalonamento_critico",
        "name": "Escalonamento de risco de reputação",
        "description": "Menções a Procon, Reclame Aqui, advogado ou processo vão direto para a fila com prioridade "
                       "urgente, sem passar pela IA.",
        "trigger": {"type": "keyword", "label": "Termos críticos detectados"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Termo crítico", "detail": "Procon · Reclame Aqui · jurídico",
             "x": 40, "y": 140},
            {"id": "m", "type": "message", "label": "Mensagem de acolhimento", "detail": "Sem IA generativa",
             "x": 300, "y": 140},
            {"id": "a", "type": "action", "label": "Tag risco-reputação", "detail": "Prioridade urgente", "x": 580,
             "y": 140},
            {"id": "h", "type": "handoff", "label": "Supervisão", "detail": "Notifica supervisora", "x": 860,
             "y": 140},
        ],
        "edges": [{"from": "t", "to": "m"}, {"from": "m", "to": "a"}, {"from": "a", "to": "h"}],
    },
    {
        "key": "rastreio_inteligente",
        "name": "Rastreio automático de pedidos",
        "description": "Identifica o pedido (pelo código ou pelo histórico do cliente), consulta o status e "
                       "trata atrasos proativamente.",
        "trigger": {"type": "intent", "label": "Intenção: rastreio"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Intenção: rastreio", "detail": "NLU", "x": 40, "y": 140},
            {"id": "a", "type": "action", "label": "consultar_pedido", "detail": "Ferramenta da IA", "x": 300,
             "y": 140},
            {"id": "c", "type": "condition", "label": "Entrega atrasada?", "detail": "Previsão < hoje", "x": 580,
             "y": 140},
            {"id": "m1", "type": "message", "label": "Status + rastreio", "detail": "", "x": 860, "y": 50},
            {"id": "m2", "type": "ai", "label": "Desculpas + reenvio/reembolso", "detail": "", "x": 860, "y": 230},
        ],
        "edges": [{"from": "t", "to": "a"}, {"from": "a", "to": "c"}, {"from": "c", "to": "m1", "label": "não"},
                  {"from": "c", "to": "m2", "label": "sim"}],
    },
    {
        "key": "fora_horario",
        "name": "Aviso fora do horário",
        "description": "Quando há transbordo fora do horário comercial, informa o horário da equipe e mantém o "
                       "caso na fila com prioridade.",
        "trigger": {"type": "handoff", "label": "Transbordo fora do expediente"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Transbordo", "detail": "", "x": 40, "y": 140},
            {"id": "c", "type": "condition", "label": "Fora do horário?", "detail": "Seg–Sáb · 8h–20h", "x": 300,
             "y": 140},
            {"id": "m", "type": "message", "label": "Informa horário", "detail": "", "x": 580, "y": 140},
            {"id": "h", "type": "handoff", "label": "Fila prioritária", "detail": "", "x": 860, "y": 140},
        ],
        "edges": [{"from": "t", "to": "c"}, {"from": "c", "to": "m", "label": "sim"}, {"from": "m", "to": "h"}],
    },
    {
        "key": "pesquisa_csat",
        "name": "Pesquisa de satisfação (CSAT)",
        "description": "Ao encerrar o atendimento, pede uma nota de 1 a 5 e registra a resposta na conversa.",
        "trigger": {"type": "resolved", "label": "Conversa encerrada"},
        "nodes": [
            {"id": "t", "type": "trigger", "label": "Conversa encerrada", "detail": "IA ou humano", "x": 40,
             "y": 140},
            {"id": "m", "type": "message", "label": "Pergunta a nota", "detail": "1 a 5", "x": 300, "y": 140},
            {"id": "a", "type": "action", "label": "Registra CSAT", "detail": "Resposta em até 24h", "x": 580,
             "y": 140},
            {"id": "e", "type": "end", "label": "Agradece", "detail": "", "x": 860, "y": 140},
        ],
        "edges": [{"from": "t", "to": "m"}, {"from": "m", "to": "a"}, {"from": "a", "to": "e"}],
    },
]

# Personas do simulador: cada uma demonstra uma capacidade diferente do agente.
DEMO_PERSONAS = [
    {"key": "juliana", "channel": "whatsapp", "headline": "Cliente VIP com entrega atrasada",
     "skills": ["Ferramenta de pedidos", "Atraso proativo"],
     "suggestions": ["meu pedido ainda não chegou", "quero o reembolso então", "obrigada!"]},
    {"key": "fernanda", "channel": "whatsapp", "headline": "Produto chegou vazando",
     "skills": ["Abertura de protocolo", "Contexto multi-turno"],
     "suggestions": ["O sérum chegou vazando, quero trocar", "é o pedido AUR-10511", "obrigada!"]},
    {"key": "marcos", "channel": "email", "headline": "Quer cancelar um pedido recém-pago",
     "skills": ["Cancelamento + estorno", "Formato de e-mail"],
     "suggestions": ["Quero cancelar o pedido AUR-10533", "Em quanto tempo o estorno cai no cartão?"]},
    {"key": "rafael", "channel": "instagram", "headline": "Dúvidas sobre produtos",
     "skills": ["Catálogo em tempo real", "RAG"],
     "suggestions": ["Vocês têm sérum para pele oleosa?", "Os produtos são veganos?", "tem cupom de primeira compra?"]},
    {"key": "visitante", "channel": "webchat", "headline": "Visitante anônimo do site",
     "skills": ["Transbordo inteligente", "Guardrails"],
     "suggestions": ["Qual o prazo de entrega para Manaus?", "vocês vendem cartão presente?",
                     "quero falar com um atendente", "vou reclamar no Procon"]},
]
