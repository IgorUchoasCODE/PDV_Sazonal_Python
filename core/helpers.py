# -*- coding: utf-8 -*-
"""
core/helpers.py
────────────────
Camada de tradução entre o backend puro (InventoryManager / PaymentManager,
dentro de br/com/pdv/src) e os templates Django já existentes.

Estratégia "melhor esforço": cada função tenta primeiro buscar os dados
REAIS do backend/banco (databaseSazonalizei.db). Se o backend ainda não
tiver dados cadastrados, ou qualquer exceção ocorrer, a função devolve um
conjunto de dados de DEMONSTRAÇÃO (mesma estrutura/campos) para que a
interface nunca quebre e sempre tenha algo bonito para mostrar.
"""


# ─────────────────────────────────────────────────────────────────────────
# Utilitário genérico de fallback seguro
# ─────────────────────────────────────────────────────────────────────────
def _safe(fn, fallback):
    try:
        resultado = fn()
        if resultado in (None, [], {}):
            return fallback
        return resultado
    except Exception as exc:  # backend/banco indisponível, tabela vazia, etc.
        import traceback
        traceback.print_exc()
        print(f"[core.helpers] usando dados de demonstração: {exc}")
        return fallback


# ─────────────────────────────────────────────────────────────────────────
# Dados de demonstração (usados apenas como reserva)
# ─────────────────────────────────────────────────────────────────────────
DEMO_RESUMO = {
    "total_vendas": 24590.00,
    "total_compras": 17050.00,
    "total_devolucoes": 420.00,
    "total_perdas": 180.00,
    "lucro_bruto_estimado": 8820.00,
    "pagamentos_recebidos": 21390.00,
    "pagamentos_efetuados": 15200.00,
    "contas_a_receber": 3200.00,
    "contas_a_pagar": 1850.00,
    "saldo_liquido_caixa": 6190.00,
}

DEMO_CATALOGO = [
    {"id": 1, "nome": "Notebook Dell Inspiron", "estoque": 12, "UnidadeMedida": "Unidade"},
    {"id": 2, "nome": "Smartphone Samsung Galaxy", "estoque": 22, "UnidadeMedida": "Unidade"},
    {"id": 3, "nome": "Monitor LG 24\"", "estoque": 8, "UnidadeMedida": "Unidade"},
    {"id": 4, "nome": "Teclado Mecânico RGB", "estoque": 30, "UnidadeMedida": "Unidade"},
    {"id": 5, "nome": "Mouse Gamer Logitech", "estoque": 41, "UnidadeMedida": "Unidade"},
    {"id": 6, "nome": "Teclado Gamer Redragon", "estoque": 3, "UnidadeMedida": "Unidade"},
    {"id": 7, "nome": "Cabo HDMI 2.0", "estoque": 0, "UnidadeMedida": "Unidade"},
    {"id": 8, "nome": "Arroz Tipo 1", "estoque": 55, "UnidadeMedida": "Kilograma"},
]

DEMO_UNIDADES = [
    {"id": 1, "descricao": "Unidade"},
    {"id": 2, "descricao": "Kilograma"},
    {"id": 3, "descricao": "Litros"},
    {"id": 4, "descricao": "Metros"},
    {"id": 5, "descricao": "Conjunto/Pacote"},
]

DEMO_CARGOS = [
    {"id": 1, "descricao": "Dono"},
    {"id": 2, "descricao": "Sócio"},
    {"id": 3, "descricao": "Diretor"},
    {"id": 4, "descricao": "Gerente"},
]

DEMO_FORMAS_PAGAMENTO = [
    {"id": 1, "descricao": "DINHEIRO"},
    {"id": 2, "descricao": "PIX"},
    {"id": 3, "descricao": "CARTÃO DE DÉBITO"},
    {"id": 4, "descricao": "CARTÃO DE CRÉDITO"},
]

DEMO_CLIENTES = [
    {"id_entidade": 101, "pessoa_nome": "João Silva", "extrato": {"resumo": {
        "total_vendas": 2450.00, "pagamentos_recebidos": 2450.00, "contas_a_receber": 0.00}}},
    {"id_entidade": 102, "pessoa_nome": "Maria Oliveira", "extrato": {"resumo": {
        "total_vendas": 1899.00, "pagamentos_recebidos": 1200.00, "contas_a_receber": 699.00}}},
    {"id_entidade": 103, "pessoa_nome": "Carlos Souza", "extrato": {"resumo": {
        "total_vendas": 890.00, "pagamentos_recebidos": 890.00, "contas_a_receber": 0.00}}},
]

DEMO_FORNECEDORES = [
    {"id_entidade": 201, "pessoa_nome": None, "empresa_nome": "Distribuidora Rio Norte Ltda",
     "tipo_entidade": "EMPRESA_PURA", "extrato": {"resumo": {
         "total_compras": 12500.00, "pagamentos_efetuados": 10000.00, "contas_a_pagar": 2500.00}}},
    {"id_entidade": 202, "pessoa_nome": "Ana Pereira", "empresa_nome": None,
     "tipo_entidade": "PESSOA_PURA", "extrato": {"resumo": {
         "total_compras": 4550.00, "pagamentos_efetuados": 3900.00, "contas_a_pagar": 650.00}}},
]

DEMO_ENTIDADES = [
    {"id_entidade": 101, "pessoa_nome": "João Silva", "empresa_nome": None,
     "tipo_entidade": "PESSOA_PURA", "cargos": []},
    {"id_entidade": 102, "pessoa_nome": "Maria Oliveira", "empresa_nome": None,
     "tipo_entidade": "PESSOA_PURA", "cargos": []},
    {"id_entidade": 201, "pessoa_nome": None, "empresa_nome": "Distribuidora Rio Norte Ltda",
     "tipo_entidade": "EMPRESA_PURA", "cargos": []},
    {"id_entidade": 301, "pessoa_nome": "Pedro Costa", "empresa_nome": "Sazonalizei Comércio Ltda",
     "tipo_entidade": "VINCULO_PESSOA_EMPRESA", "cargos": [{"id": 4, "descricao": "Gerente"}]},
]

DEMO_NOTAS = [
    {"id": 1001, "data_vencimento": "2026-08-05", "id_representante": 101},
    {"id": 1002, "data_vencimento": "2026-08-10", "id_representante": 201},
    {"id": 1003, "data_vencimento": "2026-08-18", "id_representante": 102},
]

DEMO_RELATORIO_MD = """# Relatório Financeiro Consolidado Global (Demonstração)

| Indicador | Valor Consolidado |
|---|---|
| Total Faturamento (Vendas) | R$ 24.590,00 |
| Total Compras / Insumos | R$ 17.050,00 |
| Lucro Bruto Geral | R$ 8.820,00 |
| Contas a Receber Global | R$ 3.200,00 |
| Contas a Pagar Global | R$ 1.850,00 |
| **Saldo em Caixa Geral** | **R$ 6.190,00** |

_Cadastre produtos, clientes e notas reais para que este relatório passe a refletir o seu banco de dados._
"""


# ─────────────────────────────────────────────────────────────────────────
# Backend real (importado dentro das funções para nunca derrubar o site
# caso o pacote br.com.pdv não esteja disponível/compatível)
# ─────────────────────────────────────────────────────────────────────────
def _backend():
    from br.com.pdv.src.BDD.queryEnum import DB
    from br.com.pdv.src.memory.inventoryManager import InventoryManager
    from br.com.pdv.src.memory.paymentManager import PaymentManager
    from br.com.pdv.src.financeiro.Real import MoedaReal
    return DB, InventoryManager, PaymentManager


# ─────────────────────────────────────────────────────────────────────────
# Catálogo de produtos (junta estoque calculado + nome/unidade do banco)
# Para produtos compostos, o estoque é calculado a partir dos ingredientes.
# ─────────────────────────────────────────────────────────────────────────
def _calcular_estoque_liquido_db(conn):
    """Retorna dict {id_produto: estoque_liquido} calculado diretamente do banco."""
    cur = conn.cursor()
    cur.execute('''
        SELECT id_produto,
               SUM(CASE WHEN id_tipoNota IN (1,5) THEN quantidade
                        WHEN id_tipoNota IN (2,4) THEN -quantidade
                        WHEN id_tipoNota = 3      THEN  quantidade
                        ELSE 0 END) AS estoque_liquido
        FROM fluxoEstoque
        GROUP BY id_produto
    ''')
    return {r['id_produto']: max(float(r['estoque_liquido'] or 0), 0) for r in cur.fetchall()}


def _calcular_estoque_composto(id_produto, receita_dict, estoque_liquido_map):
    """
    Calcula quantas unidades do produto composto podem ser fabricadas
    com base no estoque liquido de cada ingrediente.
    receita_dict: {str(id_ingr): qntdd_por_unidade_composta}
    Retorna float com o numero de unidades possíveis (floor do mínimo).
    """
    import math
    minimo = float('inf')
    for id_ingr_str, qtd_por_un in receita_dict.items():
        try:
            id_ingr = int(id_ingr_str)
            qtd_por_un = float(qtd_por_un)
        except (ValueError, TypeError):
            continue
        if qtd_por_un <= 0:
            continue
        estoque_ingr = estoque_liquido_map.get(id_ingr, 0)
        possivel = estoque_ingr / qtd_por_un
        if possivel < minimo:
            minimo = possivel
    if minimo == float('inf') or minimo < 0:
        return 0
    return math.floor(minimo)


def get_produtos_catalogo():
    def _real():
        DB, InventoryManager, _ = _backend()
        produtos_db = DB.SELECT.VW_PRODUTO_COMPLETO_TODOS.buscar()
        if not produtos_db:
            return []

        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()

            # Médias de venda por produto (para preencher preço quando varejo=0)
            cur.execute('''
                SELECT fe.id_produto, AVG(fe.valorUnidario) as media_venda
                FROM fluxoEstoque fe
                WHERE fe.id_tipoNota = 2
                GROUP BY fe.id_produto
            ''')
            medias = {row['id_produto']: row['media_venda'] for row in cur.fetchall()}

            # Estoque líquido calculado diretamente (mais preciso que InventoryManager em memória)
            estoque_liquido_map = _calcular_estoque_liquido_db(conn)

            # Receitas: {id_produto: {id_ingrediente: qntdd}}
            cur.execute('SELECT id_produto, id_ingrediente, qntdd FROM receita')
            receitas_rows = cur.fetchall()

        receitas_map = {}  # {id_produto: {str(id_ingr): float(qntdd)}}
        for r in receitas_rows:
            pid = r['id_produto']
            if pid not in receitas_map:
                receitas_map[pid] = {}
            receitas_map[pid][str(r['id_ingrediente'])] = float(r['qntdd'])

        catalogo = []
        for p in produtos_db:
            pid = p["id"]
            valor_venda = float(p.get("varejo") or 0.0)
            if valor_venda <= 0:
                valor_venda = float(medias.get(pid, 0.0) or 0.0)

            eh_composto = pid in receitas_map

            if eh_composto:
                # Estoque do composto = mínimo de (estoque_ingr / qntdd) entre todos ingredientes
                estoque = _calcular_estoque_composto(pid, receitas_map[pid], estoque_liquido_map)
            else:
                estoque = max(float(estoque_liquido_map.get(pid, 0)), 0)

            catalogo.append({
                "id": pid,
                "nome": p["nome"],
                "UnidadeMedida": p.get("unidade_descricao") or "Unidade",
                "estoque": estoque,
                "eh_composto": eh_composto,
                "receita": receitas_map.get(pid, {}),  # exposto para JS se necessário
                "valor_venda": valor_venda,
            })
        catalogo.sort(key=lambda x: x["id"])
        return catalogo
    return _safe(_real, DEMO_CATALOGO)


def get_unidades():
    def _real():
        DB, _, _ = _backend()
        return DB.SELECT.UNIDADE_MEDIDA_TODOS.buscar()
    return _safe(_real, DEMO_UNIDADES)


def get_cargos():
    def _real():
        DB, _, _ = _backend()
        return DB.SELECT.CARGO_TODOS.buscar()
    return _safe(_real, DEMO_CARGOS)


def get_formas_pagamento():
    def _real():
        DB, _, _ = _backend()
        return DB.SELECT.FORMA_PAGAMENTO_TODOS.buscar()
    return _safe(_real, DEMO_FORMAS_PAGAMENTO)


# ─────────────────────────────────────────────────────────────────────────
# Entidades (clientes / fornecedores / cadastro completo)
# ─────────────────────────────────────────────────────────────────────────
def get_entidades_detalhadas():
    def _real():
        _, _, PaymentManager = _backend()
        return PaymentManager.obter_entidades_detalhadas()
    return _safe(_real, DEMO_ENTIDADES)


def _com_extrato(entidade):
    """Anexa o extrato financeiro (resumo) de uma entidade — melhor esforço."""
    def _real():
        _, _, PaymentManager = _backend()
        return PaymentManager.get_extrato_entidade(entidade["id_entidade"])
    extrato = _safe(_real, entidade.get("extrato", {"resumo": {
        "total_vendas": 0, "total_compras": 0, "pagamentos_recebidos": 0,
        "pagamentos_efetuados": 0, "contas_a_receber": 0, "contas_a_pagar": 0}}))
    entidade["extrato"] = extrato
    return entidade


def get_clientes():
    entidades = get_entidades_detalhadas()
    clientes = [e for e in entidades if e.get("is_cliente")]
    if not clientes:
        return DEMO_CLIENTES
    return [_com_extrato(dict(c)) for c in clientes]


def get_fornecedores():
    entidades = get_entidades_detalhadas()
    fornecedores = [e for e in entidades if e.get("is_fornecedor")]
    if not fornecedores:
        return DEMO_FORNECEDORES
    return [_com_extrato(dict(f)) for f in fornecedores]


# ─────────────────────────────────────────────────────────────────────────
# Resumo financeiro global (dashboard / financeiro)
# ─────────────────────────────────────────────────────────────────────────
def get_resumo_financeiro():
    def _real():
        _, _, PaymentManager = _backend()
        return PaymentManager.get_resumo_financeiro_global()
    return _safe(_real, DEMO_RESUMO)


def get_status_estoque():
    def _real():
        _, InventoryManager, _ = _backend()
        return InventoryManager.get_status()
    fallback = {"total_produtos_distintos": len(DEMO_CATALOGO), "total_lotes_ativos": 0}
    return _safe(_real, fallback)


# ─────────────────────────────────────────────────────────────────────────
# Lotes FIFO (página de estoque)
# ─────────────────────────────────────────────────────────────────────────
def get_lotes_fifo():
    def _real():
        DB, InventoryManager, _ = _backend()
        
        # Obter dicionário de diasDuraveis dos produtos
        produtos = DB.SELECT.PRODUTO_TODOS.buscar()
        dias_duraveis_map = {p["id"]: p.get("diasDuraveis", 30) for p in produtos}
        
        from datetime import datetime, timedelta
        
        lotes = []
        for idx, lote in InventoryManager._mapaEstoque.items():
            if lote.get("consumido"):
                continue
                
            id_produto = lote.get("id_produto")
            data_entrada_str = lote.get("data_entrada", "")
            dias = dias_duraveis_map.get(id_produto, 30)
            
            validade_str = "N/A"
            status_validade = "N/A"
            is_vencido = False
            
            if data_entrada_str:
                try:
                    data_entrada = datetime.strptime(data_entrada_str[:10], "%Y-%m-%d")
                    data_validade = data_entrada + timedelta(days=dias)
                    validade_str = data_validade.strftime("%d/%m/%Y")
                    
                    hoje = datetime.now()
                    dias_restantes = (data_validade - hoje).days
                    
                    if dias_restantes < 0:
                        status_validade = "VENCIDO"
                        is_vencido = True
                    elif dias_restantes <= 3:
                        status_validade = f"{dias_restantes} dias (CRÍTICO)"
                    elif dias_restantes <= 7:
                        status_validade = f"{dias_restantes} dias (ATENÇÃO)"
                    else:
                        status_validade = f"{dias_restantes} dias (OK)"
                except Exception:
                    pass

            lotes.append({
                "idx_lote": idx,
                "id_produto": id_produto,
                "id_nota": lote.get("id_nota"),
                "qtd_inicial": lote.get("qtd_inicial"),
                "qtd_disponivel": lote.get("qtd_disponivel"),
                "custo_unitario": lote.get("custo_unitario"),
                "data_entrada": data_entrada_str,
                "validade": validade_str,
                "status_validade": status_validade,
                "is_vencido": is_vencido
            })
        return lotes
    return _safe(_real, [])


def get_notas():
    def _real():
        DB, _, _ = _backend()
        return DB.SELECT.FLUXO_NOTA_ESTOQUE_TODOS.buscar()
    return _safe(_real, DEMO_NOTAS)


def get_relatorio_markdown():
    def _real():
        _, _, PaymentManager = _backend()
        return PaymentManager.gerar_relatorio_markdown_global()
    return _safe(_real, DEMO_RELATORIO_MD)


# ─────────────────────────────────────────────────────────────────────────
# Agregadores por página (o que cada view precisa)
# ─────────────────────────────────────────────────────────────────────────
def dashboard_context():
    catalogo = get_produtos_catalogo()
    status = get_status_estoque()
    entidades = get_entidades_detalhadas()
    total_clientes = len([e for e in entidades if e.get("is_cliente")]) or 120
    return {
        "resumo": get_resumo_financeiro(),
        "total_produtos": status.get("total_produtos_distintos", len(catalogo)),
        "total_clientes": total_clientes,
        "catalogo": catalogo,
    }


def produtos_context():
    return {
        "catalogo": get_produtos_catalogo(),
        "fornecedores": get_fornecedores(),
        "unidades": get_unidades(),
    }


def estoque_context():
    catalogo = get_produtos_catalogo()
    simples = [p for p in catalogo if not p.get("eh_composto")]
    compostos = [p for p in catalogo if p.get("eh_composto")]
    return {
        "catalogo": catalogo,
        "simples": simples,
        "compostos": compostos,
        "total_simples": len(simples),
        "total_compostos": len(compostos),
        "lotes_fifo": get_lotes_fifo(),
    }


def clientes_context():
    return {"clientes": get_clientes()}


def fornecedores_context():
    return {"fornecedores": get_fornecedores()}


def get_grafico_lucratividade():
    """Retorna dados diários agrupados de vendas, compras, lucro, perdas e devoluções para o gráfico."""
    def _real():
        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    DATE(fe.data) as dia,
                    SUM(CASE WHEN fe.id_tipoNota = 1 THEN ABS(fe.quantidade) * fe.valorUnidario ELSE 0 END) as compras,
                    SUM(CASE WHEN fe.id_tipoNota = 2 THEN ABS(fe.quantidade) * fe.valorUnidario ELSE 0 END) as vendas,
                    SUM(CASE WHEN fe.id_tipoNota = 2 THEN fe.lucroTotal ELSE 0 END) as lucro,
                    SUM(CASE WHEN fe.id_tipoNota = 3 THEN ABS(fe.quantidade) * fe.valorUnidario ELSE 0 END) as devolucoes,
                    SUM(CASE WHEN fe.id_tipoNota = 4 THEN ABS(fe.quantidade) * fe.valorUnidario ELSE 0 END) as perdas
                FROM fluxoEstoque fe
                GROUP BY DATE(fe.data)
                ORDER BY DATE(fe.data) ASC
            """)
            rows = [dict(r) for r in cur.fetchall()]
        result = []
        for r in rows:
            result.append({
                'dia': r['dia'] or '',
                'compras': round(r['compras'] or 0, 2),
                'vendas': round(r['vendas'] or 0, 2),
                'lucro': round(r['lucro'] or 0, 2),
                'devolucoes': round(r['devolucoes'] or 0, 2),
                'perdas': round(r['perdas'] or 0, 2),
            })
        return result
    return _safe(_real, [])


def get_relatorio_por_entidade():
    """Retorna lista de entidades (clientes/fornecedores) com totais financeiros consolidados."""
    def _real():
        _, _, PaymentManager = _backend()
        entidades = PaymentManager.obter_entidades_detalhadas()
        resultado = []
        for ent in entidades:
            if not ent.get('is_cliente') and not ent.get('is_fornecedor'):
                continue
            nome = ent.get('pessoa_nome') or ent.get('empresa_nome') or f"Entidade #{ent['id_entidade']}"
            resultado.append({
                'id_entidade': ent['id_entidade'],
                'nome': nome,
                'tipo_entidade': ent.get('tipo_entidade', ''),
                'is_cliente': ent.get('is_cliente', False),
                'is_fornecedor': ent.get('is_fornecedor', False),
                'saldo_devedor_cliente': ent.get('saldo_devedor_cliente', 0.0),
                'saldo_devedor_fornecedor': ent.get('saldo_devedor_fornecedor', 0.0),
                'adiantamento_cliente': ent.get('adiantamento_cliente', 0.0),
                'adiantamento_fornecedor': ent.get('adiantamento_fornecedor', 0.0),
            })
        return resultado
    return _safe(_real, [])


def financeiro_context():
    _, _, PaymentManager = _backend()
    import json
    grafico_dados = get_grafico_lucratividade()
    return {
        "resumo": get_resumo_financeiro(),
        "entidades": get_entidades_detalhadas(),
        "formas_pagamento": get_formas_pagamento(),
        "movimentacoes": _safe(PaymentManager.get_historico_movimentacoes_global, []),
        "relatorio_entidades": get_relatorio_por_entidade(),
        "grafico_json": json.dumps(grafico_dados),
    }


def entidades_context():
    entidades = get_entidades_detalhadas()
    pessoas_puras = [e for e in entidades if e.get('tipo_entidade') == 'PESSOA_PURA']
    empresas_puras = [e for e in entidades if e.get('tipo_entidade') == 'EMPRESA_PURA']
    return {
        "entidades": entidades,
        "pessoas_puras": pessoas_puras,
        "empresas_puras": empresas_puras,
        "cargos": get_cargos(),
    }


def relatorios_context():
    return {
        "notas": get_notas(),
        "relatorio_markdown": get_relatorio_markdown(),
    }


# ─────────────────────────────────────────────────────────────────────────
# Notas de Venda e Devolução para o PDV
# ─────────────────────────────────────────────────────────────────────────
def get_notas_venda():
    """Retorna lista de Notas de Venda (tipo 2) com nome do cliente."""
    def _real():
        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    fn.id,
                    fn.data_vencimento,
                    fn.id_representante,
                    COALESCE(pe.nome, em.nome, 'Consumidor ' || fn.id_representante) AS nome_cliente,
                    SUM(ABS(fe.quantidade) * fe.valorUnidario) AS valor_total
                FROM fluxosNotasEstoque fn
                LEFT JOIN entidades en ON en.id = fn.id_representante
                LEFT JOIN pessoas pe ON pe.id = en.id_pessoa
                LEFT JOIN empresas em ON em.id = en.id_empresa
                LEFT JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
                WHERE fn.id_tipoNota = 2
                GROUP BY fn.id
                ORDER BY fn.id DESC
                LIMIT 100
            ''')
            notas = []
            for r in cur.fetchall():
                notas.append({
                    'id': r['id'],
                    'data': str(r['data_vencimento']) if r['data_vencimento'] else '',
                    'id_cliente': r['id_representante'],
                    'nome_cliente': r['nome_cliente'] or '',
                    'valor_total': round(float(r['valor_total'] or 0), 2),
                })
        return notas
    return _safe(_real, [])


def get_notas_devolucao():
    """Retorna lista de Notas de Devolução (tipo 3) com referência à venda de origem."""
    def _real():
        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    fn.id,
                    fn.data_vencimento,
                    fn.id_representante,
                    COALESCE(pe.nome, em.nome, 'Entidade ' || fn.id_representante) AS nome_cliente,
                    SUM(ABS(fe.quantidade) * fe.valorUnidario) AS valor_total,
                    MIN(fe.id_notaOrigem) AS id_nota_venda_origem
                FROM fluxosNotasEstoque fn
                LEFT JOIN entidades en ON en.id = fn.id_representante
                LEFT JOIN pessoas pe ON pe.id = en.id_pessoa
                LEFT JOIN empresas em ON em.id = en.id_empresa
                LEFT JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
                WHERE fn.id_tipoNota = 3
                GROUP BY fn.id
                ORDER BY fn.id DESC
                LIMIT 100
            ''')
            notas = []
            for r in cur.fetchall():
                notas.append({
                    'id': r['id'],
                    'data': str(r['data_vencimento']) if r['data_vencimento'] else '',
                    'id_cliente': r['id_representante'],
                    'nome_cliente': r['nome_cliente'] or '',
                    'valor_total': round(float(r['valor_total'] or 0), 2),
                    'id_nota_venda_origem': r['id_nota_venda_origem'],
                })
        return notas
    return _safe(_real, [])


def get_itens_nota(id_nota):
    """Retorna os itens (produtos, quantidades, valores) de uma nota específica."""
    def _real():
        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    fe.id_produto,
                    p.nome AS nome_produto,
                    um.descricao AS unidade,
                    SUM(fe.quantidade) AS quantidade,
                    AVG(fe.valorUnidario) AS valor_unitario
                FROM fluxoEstoque fe
                JOIN produto p ON p.id = fe.id_produto
                LEFT JOIN unidadeMedida um ON um.id = p.unidadeMedida
                WHERE fe.id_fluxo_nota = ?
                GROUP BY fe.id_produto
            ''', (id_nota,))
            itens = []
            for r in cur.fetchall():
                itens.append({
                    'id': r['id_produto'],
                    'nome': r['nome_produto'],
                    'unidade': r['unidade'] or 'un',
                    'quantidade': abs(float(r['quantidade'] or 0)),
                    'valor_unitario': round(float(r['valor_unitario'] or 0), 4),
                })
        return itens
    return _safe(_real, [])


def pdv_context():
    entidades = get_entidades_detalhadas()
    clientes = [e for e in entidades if e.get("is_cliente")] or DEMO_CLIENTES
    return {
        "clientes": clientes,
        "formas_pagamento": get_formas_pagamento(),
        "catalogo": get_produtos_catalogo(),
        "notas_venda": get_notas_venda(),
        "notas_devolucao": get_notas_devolucao(),
    }
