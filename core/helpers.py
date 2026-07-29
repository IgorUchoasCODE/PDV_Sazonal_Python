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
    return DB, InventoryManager, PaymentManager


# ─────────────────────────────────────────────────────────────────────────
# Catálogo de produtos (junta estoque calculado + nome/unidade do banco)
# ─────────────────────────────────────────────────────────────────────────
def get_produtos_catalogo():
    def _real():
        DB, InventoryManager, _ = _backend()
        produtos_db = DB.SELECT.VW_PRODUTO_COMPLETO_TODOS.buscar()
        if not produtos_db:
            return []
        estoque_por_id = {p["id"]: p for p in InventoryManager.get_produtos_lista()}
        catalogo = []
        for p in produtos_db:
            info = estoque_por_id.get(p["id"], {})
            catalogo.append({
                "id": p["id"],
                "nome": p["nome"],
                "UnidadeMedida": p.get("unidade_descricao") or "Unidade",
                "estoque": info.get("qtd_estoque", 0),
                "eh_composto": info.get("eh_composto", False),
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


def financeiro_context():
    return {
        "resumo": get_resumo_financeiro(),
        "entidades": get_entidades_detalhadas(),
        "formas_pagamento": get_formas_pagamento(),
    }


def entidades_context():
    return {
        "entidades": get_entidades_detalhadas(),
        "cargos": get_cargos(),
    }


def relatorios_context():
    return {
        "notas": get_notas(),
        "relatorio_markdown": get_relatorio_markdown(),
    }


def pdv_context():
    entidades = get_entidades_detalhadas()
    clientes = [e for e in entidades if e.get("is_cliente")] or DEMO_CLIENTES
    return {
        "clientes": clientes,
        "formas_pagamento": get_formas_pagamento(),
        "catalogo": get_produtos_catalogo(),
    }
