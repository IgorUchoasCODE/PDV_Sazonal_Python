"""
Seed de Dados - PDV Sazonal
============================
Popula o banco com produtos e fluxos de estoque seguindo as proporcoes:
  - 10% simples (sem receita, unidade simples)
  - 10% conjunto (com unidade de conjunto)
  - 20% receita simples (1 ingrediente)
  - 60% receita complexa (4+ ingredientes)

Regra de venda de composto:
  - Produto composto: registrado com preco de venda e LUCRO
  - Ingredientes do composto: registrados como VENDA ao preco de CUSTO, LUCRO = 0
"""

import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "databaseSazonalizei.db"

# Proporcoes planejadas para ~30 novos produtos:
# 10% simples       => 4 produtos
# 10% conjunto      => 3 pares (caixa + avulso) = 6 produtos
# 20% receita simples (1 ingr) => 6 produtos
# 60% receita complexa (4+ ingr) => 12 produtos compostos

# -------------------------------------------------
# CATALOGO DE DADOS REALISTAS
# -------------------------------------------------

PRODUTOS_SIMPLES = [
    {"nome": "ARROZ BRANCO TIPO 1 (5KG)",   "unidade": 1, "custo": 22.50, "venda": 29.90},
    {"nome": "FEIJAO CARIOCA TIPO 1 (1KG)", "unidade": 1, "custo": 7.80,  "venda": 10.50},
    {"nome": "AZEITE EXTRA VIRGEM 500ML",    "unidade": 3, "custo": 18.00, "venda": 25.90},
    {"nome": "SAL REFINADO 1KG",             "unidade": 2, "custo": 2.30,  "venda": 3.50},
]

PRODUTOS_CONJUNTO = [
    {
        "caixa":  {"nome": "CAIXA DE ARROZ BRANCO (10 SACOS 5KG)",  "fator": 10, "custo": 210.00},
        "avulso": {"nome": "SACO DE ARROZ BRANCO 5KG (AVULSO)",     "unidade": 1, "custo": 22.50, "venda": 29.90},
    },
    {
        "caixa":  {"nome": "FARDO DE FEIJAO CARIOCA (12 SACOS 1KG)","fator": 12, "custo": 87.00},
        "avulso": {"nome": "SACO DE FEIJAO CARIOCA 1KG (AVULSO)",   "unidade": 1, "custo": 7.80,  "venda": 10.50},
    },
    {
        "caixa":  {"nome": "CAIXA DE AZEITE 500ML (6 UN.)",          "fator": 6,  "custo": 100.00},
        "avulso": {"nome": "GARRAFA DE AZEITE 500ML (AVULSA)",       "unidade": 1, "custo": 18.00, "venda": 25.90},
    },
]

PRODUTOS_RECEITA_SIMPLES = [
    {"nome": "OVO CAIPIRA AVULSO (UNIDADE)",   "ingrediente_nome": "CAIXA DE OVO  BRANCO TIPO A", "qntdd": 1, "custo": 0.45, "venda": 0.80, "unidade": 1},
    {"nome": "REFRIGERANTE 350ML AVULSO",       "ingrediente_nome": "FARDO DE COCA-COLA 350ML (12 UN.)", "qntdd": 1, "custo": 2.50, "venda": 4.00, "unidade": 1},
    {"nome": "AGUA MINERAL AVULSA 500ML",       "ingrediente_nome": "FARDO DE AGUA MINERAL 500ML (24 UN.)", "qntdd": 1, "custo": 0.75, "venda": 2.00, "unidade": 1},
    {"nome": "SABAO EM PO AVULSO 1KG",          "ingrediente_nome": "CAIXA DE SABAO EM PO 1KG (20 UN.)", "qntdd": 1, "custo": 5.50, "venda": 8.90, "unidade": 1},
    {"nome": "BISCOITO RECHEADO AVULSO",        "ingrediente_nome": "CAIXA DE BISCOITO RECHEADO (50 UN.)", "qntdd": 1, "custo": 1.40, "venda": 2.50, "unidade": 1},
    {"nome": "LEITE INTEGRAL AVULSO 1L",        "ingrediente_nome": None, "qntdd": 1, "custo": 4.20, "venda": 6.50, "unidade": 3},
]

PRODUTOS_RECEITA_COMPLEXA = [
    {
        "nome": "MARMITA FITNESS FRANGO GRELHADO", "venda": 22.00,
        "ingredientes": [
            {"nome": "FRANGO GRELHADO 150G",      "custo": 6.50, "qntdd": 1, "unidade": 2},
            {"nome": "ARROZ INTEGRAL 200G",        "custo": 2.00, "qntdd": 1, "unidade": 2},
            {"nome": "FEIJAO CARIOCA COZIDO 100G", "custo": 1.20, "qntdd": 1, "unidade": 2},
            {"nome": "SALADA VERDE MISTA 80G",     "custo": 1.50, "qntdd": 1, "unidade": 2},
            {"nome": "AZEITE DE OLIVA 5ML",        "custo": 0.50, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "PIZZA MARGHERITA MEDIA", "venda": 45.00,
        "ingredientes": [
            {"nome": "MASSA DE PIZZA MEDIA",     "custo": 4.00, "qntdd": 1, "unidade": 1},
            {"nome": "MOLHO DE TOMATE CASEIRO",  "custo": 2.50, "qntdd": 1, "unidade": 3},
            {"nome": "MUSSARELA FATIADA 150G",   "custo": 6.00, "qntdd": 1, "unidade": 2},
            {"nome": "TOMATE RODELA 100G",       "custo": 1.50, "qntdd": 2, "unidade": 1},
            {"nome": "OREGANO SECO 5G",          "custo": 0.30, "qntdd": 1, "unidade": 2},
            {"nome": "AZEITE EXTRA VIRGEM PIZZA","custo": 0.80, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "ACAI COMPLETO 500ML", "venda": 28.00,
        "ingredientes": [
            {"nome": "POLPA DE ACAI 300ML",    "custo": 8.00, "qntdd": 1, "unidade": 3},
            {"nome": "BANANA PRATA UNIDADE",   "custo": 0.60, "qntdd": 2, "unidade": 1},
            {"nome": "GRANOLA NATURAL 50G",    "custo": 1.20, "qntdd": 1, "unidade": 2},
            {"nome": "MEL PURO 15ML",          "custo": 1.50, "qntdd": 1, "unidade": 3},
            {"nome": "LEITE CONDENSADO 20ML",  "custo": 0.80, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "CACHORRO QUENTE COMPLETO", "venda": 12.00,
        "ingredientes": [
            {"nome": "PAO DE HOT DOG",       "custo": 0.80, "qntdd": 1, "unidade": 1},
            {"nome": "SALSICHA VIENENSE",    "custo": 2.50, "qntdd": 2, "unidade": 1},
            {"nome": "MILHO VERDE LATA 50G", "custo": 0.60, "qntdd": 1, "unidade": 2},
            {"nome": "ERVILHA LATA 30G",     "custo": 0.40, "qntdd": 1, "unidade": 2},
            {"nome": "BATATA PALHA 20G",     "custo": 0.50, "qntdd": 1, "unidade": 2},
            {"nome": "KETCHUP 20ML",         "custo": 0.40, "qntdd": 1, "unidade": 3},
            {"nome": "MOSTARDA 15ML",        "custo": 0.30, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "VITAMINA DE FRUTAS MISTA 400ML", "venda": 15.00,
        "ingredientes": [
            {"nome": "LEITE INTEGRAL 200ML", "custo": 0.90, "qntdd": 1, "unidade": 3},
            {"nome": "MAMAO FORMOSA 100G",   "custo": 1.20, "qntdd": 1, "unidade": 2},
            {"nome": "BANANA NANICA UNIDADE","custo": 0.55, "qntdd": 1, "unidade": 1},
            {"nome": "MACA FUJI 80G",        "custo": 1.00, "qntdd": 1, "unidade": 2},
            {"nome": "ACUCAR REFINADO 10G",  "custo": 0.10, "qntdd": 1, "unidade": 2},
        ],
    },
    {
        "nome": "TAPIOCA RECHEADA FRANGO", "venda": 18.00,
        "ingredientes": [
            {"nome": "GOMA DE TAPIOCA 80G",        "custo": 1.50, "qntdd": 1, "unidade": 2},
            {"nome": "FRANGO DESFIADO 100G",        "custo": 4.00, "qntdd": 1, "unidade": 2},
            {"nome": "QUEIJO COALHO FATIA",         "custo": 1.80, "qntdd": 1, "unidade": 1},
            {"nome": "CREME DE LEITE 30ML",         "custo": 0.70, "qntdd": 1, "unidade": 3},
            {"nome": "TEMPERO VERDE FRESCO 5G",     "custo": 0.30, "qntdd": 1, "unidade": 2},
        ],
    },
    {
        "nome": "PRATO FEITO COMPLETO ALMOCO", "venda": 25.00,
        "ingredientes": [
            {"nome": "CARNE BOVINA BIFAO 200G",  "custo": 12.00, "qntdd": 1, "unidade": 2},
            {"nome": "ARROZ BRANCO COZIDO 200G", "custo": 1.80,  "qntdd": 1, "unidade": 2},
            {"nome": "FEIJAO PRETO COZIDO 150G", "custo": 1.50,  "qntdd": 1, "unidade": 2},
            {"nome": "FAROFA DE MANTEIGA 30G",   "custo": 0.60,  "qntdd": 1, "unidade": 2},
            {"nome": "MACARRAO PARAFUSO 100G",   "custo": 1.20,  "qntdd": 1, "unidade": 2},
            {"nome": "VINAGRETE CASEIRO 50G",    "custo": 0.80,  "qntdd": 1, "unidade": 2},
        ],
    },
    {
        "nome": "COXINHA DE FRANGO GRANDE", "venda": 8.00,
        "ingredientes": [
            {"nome": "MASSA DE COXINHA 80G",       "custo": 1.20, "qntdd": 1, "unidade": 2},
            {"nome": "FRANGO COZIDO DESFIADO 50G", "custo": 2.50, "qntdd": 1, "unidade": 2},
            {"nome": "CATUPIRY CREME 20G",         "custo": 0.90, "qntdd": 1, "unidade": 2},
            {"nome": "FARINHA DE ROSCA 30G",       "custo": 0.40, "qntdd": 1, "unidade": 2},
            {"nome": "OLEO DE FRITURA 50ML",       "custo": 0.60, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "SMOOTHIE DETOX VERDE 350ML", "venda": 20.00,
        "ingredientes": [
            {"nome": "COUVE MANTEIGA FOLHA",  "custo": 0.80, "qntdd": 2, "unidade": 1},
            {"nome": "PEPINO JAPONES 100G",   "custo": 1.20, "qntdd": 1, "unidade": 2},
            {"nome": "GENGEMBRE RAIZ 10G",    "custo": 0.50, "qntdd": 1, "unidade": 2},
            {"nome": "LIMAO TAHITI 30ML",     "custo": 0.60, "qntdd": 1, "unidade": 3},
            {"nome": "AGUA DE COCO 100ML",    "custo": 2.50, "qntdd": 1, "unidade": 3},
            {"nome": "HORTELA FRESCA 5G",     "custo": 0.30, "qntdd": 1, "unidade": 2},
        ],
    },
    {
        "nome": "PASTEL DE CARNE FRITO", "venda": 10.00,
        "ingredientes": [
            {"nome": "MASSA DE PASTEL GRANDE",    "custo": 1.00, "qntdd": 1, "unidade": 1},
            {"nome": "CARNE MOIDA TEMPERADA 80G", "custo": 4.50, "qntdd": 1, "unidade": 2},
            {"nome": "AZEITONA VERDE 10G",        "custo": 0.60, "qntdd": 1, "unidade": 2},
            {"nome": "OVO COZIDO PICADO 20G",     "custo": 0.30, "qntdd": 1, "unidade": 2},
            {"nome": "OLEO FRITURA 80ML",         "custo": 0.70, "qntdd": 1, "unidade": 3},
        ],
    },
    {
        "nome": "ESCONDIDINHO DE CARNE SECA", "venda": 35.00,
        "ingredientes": [
            {"nome": "CARNE SECA DESSALGADA 200G", "custo": 15.00, "qntdd": 1, "unidade": 2},
            {"nome": "PURE DE MANDIOCA 250G",      "custo": 3.50,  "qntdd": 1, "unidade": 2},
            {"nome": "CEBOLA ROXA PICADA 50G",     "custo": 0.80,  "qntdd": 1, "unidade": 2},
            {"nome": "ALHO AMASSADO 5G",           "custo": 0.30,  "qntdd": 1, "unidade": 2},
            {"nome": "PIMENTA DO REINO 2G",        "custo": 0.20,  "qntdd": 1, "unidade": 2},
            {"nome": "MANTEIGA CULINARIA 20G",     "custo": 0.90,  "qntdd": 1, "unidade": 2},
            {"nome": "QUEIJO PARMESAO RALADO 30G", "custo": 2.50,  "qntdd": 1, "unidade": 2},
        ],
    },
    {
        "nome": "HAMBURGUER GOURMET DUPLO", "venda": 42.00,
        "ingredientes": [
            {"nome": "PAO BRIOCHE GOURMET",        "custo": 3.50,  "qntdd": 1, "unidade": 1},
            {"nome": "BLEND BOVINO 100G",           "custo": 7.00,  "qntdd": 2, "unidade": 1},
            {"nome": "QUEIJO GOUDA FATIA GROSSA",   "custo": 3.00,  "qntdd": 2, "unidade": 1},
            {"nome": "BACON DEFUMADO TIRA",         "custo": 1.30,  "qntdd": 3, "unidade": 1},
            {"nome": "ALFACE AMERICANA FOLHA",      "custo": 0.30,  "qntdd": 2, "unidade": 1},
            {"nome": "TOMATE ITALIANO RODELA",      "custo": 0.50,  "qntdd": 2, "unidade": 1},
            {"nome": "CEBOLA CARAMELIZADA 30G",     "custo": 1.20,  "qntdd": 1, "unidade": 2},
            {"nome": "MOLHO DA CASA 20ML",          "custo": 0.80,  "qntdd": 1, "unidade": 3},
        ],
    },
]


# -------------------------------------------------
# DATAS DO CENARIO
# -------------------------------------------------
BASE_DATE = date(2026, 7, 1)

def d(offset_days):
    return str(BASE_DATE + timedelta(days=offset_days))


# -------------------------------------------------
# FUNCOES AUXILIARES
# -------------------------------------------------

def get_id_by_nome(cur, nome):
    cur.execute("SELECT id FROM produto WHERE nome = ?", (nome.upper(),))
    row = cur.fetchone()
    return row["id"] if row else None

def get_or_create_unidade(cur, conn, descricao, fator):
    cur.execute("SELECT id FROM unidadeMedida WHERE descricao = ? AND fatorConjunto = ?", (descricao, fator))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO unidadeMedida (descricao, fatorConjunto) VALUES (?, ?)", (descricao, fator))
    conn.commit()
    return cur.lastrowid

def criar_produto(cur, conn, nome, unidade_id, tem_receita):
    cur.execute(
        "INSERT INTO produto (nome, diasDuraveis, unidadeMedida, receita, varejo, atacado, promocao) VALUES (?, 365, ?, ?, 0, 0, 0)",
        (nome.upper(), unidade_id, 1 if tem_receita else 0)
    )
    conn.commit()
    return cur.lastrowid

def registrar_compra(cur, conn, id_fornecedor, id_produto, qtd, custo, data_str):
    cur.execute(
        "INSERT INTO fluxosNotasEstoque (id_tipoNota, id_representante, id_notaOrigem, data_vencimento) VALUES (1, ?, NULL, ?)",
        (id_fornecedor, data_str)
    )
    conn.commit()
    id_nota = cur.lastrowid
    cur.execute(
        "INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data) VALUES (1, ?, ?, ?, ?, 0, ?)",
        (id_nota, id_produto, qtd, custo, data_str)
    )
    conn.commit()
    return id_nota

def registrar_venda_simples(cur, conn, id_cliente, id_produto, qtd, preco_venda, custo,
                             data_str, id_nota_origem=None, id_forma_pagamento=1):
    lucro = round((preco_venda - custo) * qtd, 2)
    cur.execute(
        "INSERT INTO fluxosNotasEstoque (id_tipoNota, id_representante, id_notaOrigem, data_vencimento) VALUES (2, ?, ?, ?)",
        (id_cliente, id_nota_origem, data_str)
    )
    conn.commit()
    id_nota = cur.lastrowid
    cur.execute(
        "INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data) VALUES (2, ?, ?, ?, ?, ?, ?)",
        (id_nota, id_produto, qtd, preco_venda, lucro, data_str)
    )
    conn.commit()
    # Pagamento da venda simples
    _registrar_pagamento(cur, conn, id_nota, id_forma_pagamento, round(qtd * preco_venda, 2), data_str)
    return id_nota

def _buscar_nota_compra(cur, id_produto):
    """Retorna o id da nota de compra mais recente do produto/ingrediente."""
    cur.execute("""
        SELECT fn.id
        FROM fluxosNotasEstoque fn
        JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
        WHERE fn.id_tipoNota = 1 AND fe.id_produto = ?
        ORDER BY fn.id DESC LIMIT 1
    """, (id_produto,))
    row = cur.fetchone()
    return row["id"] if row else None


def _registrar_pagamento(cur, conn, id_nota, id_forma, valor, data_str):
    """Insere pagamento em fluxoPagamentoNotas."""
    cur.execute(
        "INSERT INTO fluxoPagamentoNotas (id_fluxo_nota, id_forma_pagamento, valor, data_pagamento) VALUES (?, ?, ?, ?)",
        (id_nota, id_forma, valor, data_str)
    )
    conn.commit()


def registrar_venda_composto(cur, conn, id_cliente, id_produto, qtd, preco_venda,
                              custo_total, ingr_items, data_str,
                              id_nota_origem=None, id_forma_pagamento=1):
    """
    Estrutura correta de venda de produto composto:

    1. Nota do produto composto (fluxosNotasEstoque tipo=2):
       - id_notaOrigem: NULL se multiplos ingredientes, ou nota de compra se 1 ingrediente
       - fluxoEstoque: valorUnidario=preco_venda, lucroTotal=lucro real

    2. Uma nota separada por ingrediente (fluxosNotasEstoque tipo=2):
       - id_representante: MESMO cliente
       - id_notaOrigem: nota de COMPRA daquele ingrediente
       - fluxoEstoque: valorUnidario=custo, lucroTotal=0

    3. fluxoPagamentoNotas:
       - Nota do produto: valor = qtd * preco_venda (pagamento real do cliente)
       - Notas de ingredientes: valor = 0 (rastreabilidade da transacao)
       - Mesma forma de pagamento para todas
    """
    lucro = round((preco_venda - custo_total) * qtd, 2)
    total_pago = round(qtd * preco_venda, 2)

    # ── 1. Nota do produto composto ──
    cur.execute(
        "INSERT INTO fluxosNotasEstoque (id_tipoNota, id_representante, id_notaOrigem, data_vencimento) VALUES (2, ?, ?, ?)",
        (id_cliente, id_nota_origem, data_str)
    )
    conn.commit()
    id_nota_produto = cur.lastrowid

    cur.execute(
        "INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data) VALUES (2, ?, ?, ?, ?, ?, ?)",
        (id_nota_produto, id_produto, qtd, preco_venda, lucro, data_str)
    )
    conn.commit()

    # Pagamento da nota principal (valor real cobrado do cliente)
    _registrar_pagamento(cur, conn, id_nota_produto, id_forma_pagamento, total_pago, data_str)

    # ── 2. Uma nota separada por ingrediente ──
    for ingr in ingr_items:
        id_nota_compra_ingr = _buscar_nota_compra(cur, ingr["id_ingrediente"])

        cur.execute(
            "INSERT INTO fluxosNotasEstoque (id_tipoNota, id_representante, id_notaOrigem, data_vencimento) VALUES (2, ?, ?, ?)",
            (id_cliente, id_nota_compra_ingr, data_str)
        )
        conn.commit()
        id_nota_ingr = cur.lastrowid

        cur.execute(
            "INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data) VALUES (2, ?, ?, ?, ?, 0, ?)",
            (id_nota_ingr, ingr["id_ingrediente"], qtd * ingr["qntdd"], ingr["custo"], data_str)
        )
        conn.commit()

        # Pagamento da nota do ingrediente (valor=0, apenas rastreabilidade)
        _registrar_pagamento(cur, conn, id_nota_ingr, id_forma_pagamento, 0, data_str)

    return id_nota_produto


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Coleta de entidades
    cur.execute("SELECT id FROM entidades WHERE fornecedor = 1")
    fornecedores = [r["id"] for r in cur.fetchall()]
    cur.execute("SELECT id FROM entidades WHERE cliente = 1")
    clientes = [r["id"] for r in cur.fetchall()]

    if not fornecedores or not clientes:
        print("ERRO: Nenhum fornecedor ou cliente encontrado no banco.")
        return

    print(f"Fornecedores: {fornecedores}")
    print(f"Clientes:     {clientes}")

    # cache nome -> id para nao duplicar
    cache = {}

    def obter_ou_criar(nome, unidade_id, tem_receita):
        nome_upper = nome.upper()
        if nome_upper in cache:
            return cache[nome_upper]
        pid = get_id_by_nome(cur, nome_upper)
        if not pid:
            pid = criar_produto(cur, conn, nome_upper, unidade_id, tem_receita)
            print(f"    [NOVO] {nome_upper} (id={pid})")
        else:
            print(f"    [JA EXISTE] {nome_upper} (id={pid})")
        cache[nome_upper] = pid
        return pid

    # -------------------------------------------------------
    # BLOCO 1 — 10% SIMPLES
    # -------------------------------------------------------
    print("\n========== [1/4] PRODUTOS SIMPLES ==========")
    for p in PRODUTOS_SIMPLES:
        pid = obter_ou_criar(p["nome"], p["unidade"], False)
        forn = random.choice(fornecedores)
        # Captura id da nota de compra para referenciar na venda
        id_nota_compra = registrar_compra(cur, conn, forn, pid, random.randint(50, 200), p["custo"], d(random.randint(0, 10)))
        cli = random.choice(clientes)
        # Venda referencia a nota de compra como origem
        registrar_venda_simples(cur, conn, cli, pid, random.randint(5, 30), p["venda"], p["custo"], d(random.randint(11, 20)), id_nota_origem=id_nota_compra)

    # -------------------------------------------------------
    # BLOCO 2 — 10% CONJUNTO
    # -------------------------------------------------------
    print("\n========== [2/4] PRODUTOS CONJUNTO ==========")
    for conj in PRODUTOS_CONJUNTO:
        caixa  = conj["caixa"]
        avulso = conj["avulso"]

        desc_un = f"CAIXA/PACOTE ({caixa['fator']} UN.)"
        uid_caixa = get_or_create_unidade(cur, conn, desc_un, caixa["fator"])

        pid_caixa  = obter_ou_criar(caixa["nome"],  uid_caixa,       False)
        pid_avulso = obter_ou_criar(avulso["nome"], avulso["unidade"], True)

        # Receita do avulso: 1 unidade da caixa
        cur.execute("SELECT id_ingrediente FROM receita WHERE id_produto = ? AND id_ingrediente = ?", (pid_avulso, pid_caixa))
        if not cur.fetchone():
            cur.execute("INSERT INTO receita (id_produto, id_ingrediente, qntdd) VALUES (?, ?, 1)", (pid_avulso, pid_caixa))
            conn.commit()

        # Compra da caixa — 1 fornecedor, captura nota de origem
        forn = random.choice(fornecedores)
        id_nota_compra_caixa = registrar_compra(cur, conn, forn, pid_caixa, random.randint(5, 20), caixa["custo"], d(random.randint(0, 5)))

        # Venda do avulso (composto simples: 1 ingrediente => aponta pra nota de compra da caixa)
        ingr_items = [{"id_ingrediente": pid_caixa, "qntdd": 1, "custo": avulso["custo"]}]
        cli = random.choice(clientes)
        qtd = random.randint(5, 30)
        registrar_venda_composto(cur, conn, cli, pid_avulso, qtd, avulso["venda"], avulso["custo"], ingr_items, d(random.randint(6, 15)), id_nota_origem=id_nota_compra_caixa)

    # -------------------------------------------------------
    # BLOCO 3 — 20% RECEITA SIMPLES (1 ingrediente)
    # -------------------------------------------------------
    print("\n========== [3/4] RECEITA SIMPLES ==========")
    for p in PRODUTOS_RECEITA_SIMPLES:
        pid = obter_ou_criar(p["nome"], p["unidade"], True)

        # Buscar ingrediente existente ou criar novo
        id_ing = None
        if p.get("ingrediente_nome"):
            id_ing = get_id_by_nome(cur, p["ingrediente_nome"])
            if not id_ing:
                id_ing = cache.get(p["ingrediente_nome"].upper())

        if not id_ing:
            nome_ing = p["nome"] + " GRANEL"
            id_ing = obter_ou_criar(nome_ing, p["unidade"], False)
            forn = random.choice(fornecedores)
            registrar_compra(cur, conn, forn, id_ing, 100, round(p["custo"] * 0.8, 2), d(1))

        if p.get("ingrediente_nome"):
            cache[p["ingrediente_nome"].upper()] = id_ing

        # Vincula receita se nao existe
        cur.execute("SELECT id_ingrediente FROM receita WHERE id_produto = ? AND id_ingrediente = ?", (pid, id_ing))
        if not cur.fetchone():
            cur.execute("INSERT INTO receita (id_produto, id_ingrediente, qntdd) VALUES (?, ?, ?)", (pid, id_ing, p["qntdd"]))
            conn.commit()

        # Compra do ingrediente — 1 fornecedor, captura nota de origem
        forn = random.choice(fornecedores)
        id_nota_compra_ing = registrar_compra(cur, conn, forn, id_ing, random.randint(50, 300), p["custo"], d(random.randint(0, 5)))

        # Venda (composto 1 ingrediente => aponta pra nota de compra do ingrediente)
        ingr_items = [{"id_ingrediente": id_ing, "qntdd": p["qntdd"], "custo": p["custo"]}]
        cli = random.choice(clientes)
        qtd = random.randint(10, 50)
        registrar_venda_composto(cur, conn, cli, pid, qtd, p["venda"], p["custo"], ingr_items, d(random.randint(6, 20)), id_nota_origem=id_nota_compra_ing)

    # -------------------------------------------------------
    # BLOCO 4 — 60% RECEITA COMPLEXA (4+ ingredientes)
    # -------------------------------------------------------
    print("\n========== [4/4] RECEITA COMPLEXA ==========")
    for p in PRODUTOS_RECEITA_COMPLEXA:
        pid = obter_ou_criar(p["nome"], 1, True)

        ingr_items_venda = []
        for ingr in p["ingredientes"]:
            id_ing = obter_ou_criar(ingr["nome"], ingr["unidade"], False)

            # Compra do ingrediente de fornecedor aleatorio
            forn = random.choice(fornecedores)
            registrar_compra(cur, conn, forn, id_ing, random.randint(20, 100), ingr["custo"], d(random.randint(0, 10)))

            # Vincula na receita se nao existe
            cur.execute("SELECT id_ingrediente FROM receita WHERE id_produto = ? AND id_ingrediente = ?", (pid, id_ing))
            if not cur.fetchone():
                cur.execute("INSERT INTO receita (id_produto, id_ingrediente, qntdd) VALUES (?, ?, ?)", (pid, id_ing, ingr["qntdd"]))
                conn.commit()

            ingr_items_venda.append({"id_ingrediente": id_ing, "qntdd": ingr["qntdd"], "custo": ingr["custo"]})

        custo_total = sum(i["custo"] * i["qntdd"] for i in ingr_items_venda)

        # Venda do composto com multiplos ingredientes/fornecedores => id_notaOrigem = NULL
        # pois nao ha uma unica nota de compra de referencia
        cli = random.choice(clientes)
        qtd = random.randint(3, 15)
        registrar_venda_composto(cur, conn, cli, pid, qtd, p["venda"], custo_total, ingr_items_venda, d(random.randint(11, 25)), id_nota_origem=None)

    # -------------------------------------------------------
    # RELATORIO FINAL
    # -------------------------------------------------------
    cur.execute("SELECT COUNT(*) as c FROM produto"); total_prod = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM receita"); total_rec = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM fluxosNotasEstoque"); total_notas = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM fluxoEstoque"); total_itens = cur.fetchone()["c"]

    print(f"\n{'='*55}")
    print(f"  SEED CONCLUIDO!")
    print(f"  Produtos:              {total_prod}")
    print(f"  Linhas de Receita:     {total_rec}")
    print(f"  Notas de Fluxo:        {total_notas}")
    print(f"  Itens de Fluxo:        {total_itens}")
    print(f"{'='*55}")

    conn.close()


if __name__ == "__main__":
    main()
