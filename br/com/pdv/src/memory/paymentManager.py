import sqlite3
from datetime import date, datetime
from typing import Optional, Union, Dict, List, Any

from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.Real import MoedaReal
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.registro.registroGenerico import RegistroGenerico
from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
from br.com.pdv.src.memory.enterpriseClassFactory import EnterpriseClassFactory
from br.com.pdv.src.memory.clientClassFactory import ClientClassFactory
from br.com.pdv.src.memory.supplierClassFactory import SupplierClassFactory
from br.com.pdv.src.memory.inventoryManager import InventoryManager


# ─────────────────────────────────────────────────────────────────────────────
# Classes Auxiliares: Processamento, Estruturação e Formatação
# ─────────────────────────────────────────────────────────────────────────────

class ExtratoFinanceiro:
    """
    Representa a posição financeira consolidada de uma Entidade, Empresa ou Pessoa.
    Centraliza saldos, totais de vendas, compras, devoluções, perdas, lucros
    e histórico de pagamentos.
    """
    def __init__(self, id_dono: int, tipo_dono: str, nome_dono: str):
        self.id_dono: int = id_dono
        self.tipo_dono: str = tipo_dono  # 'EMPRESA', 'PESSOA', 'ENTIDADE'
        self.nome_dono: str = nome_dono

        self.total_vendas: float = 0.0
        self.total_compras: float = 0.0
        self.total_devolucoes: float = 0.0
        self.total_perdas: float = 0.0
        self.lucro_bruto_estimado: float = 0.0

        self.pagamentos_recebidos: float = 0.0
        self.pagamentos_efetuados: float = 0.0

        self.contas_a_receber: float = 0.0  # Vendas - Recebidos
        self.contas_a_pagar: float = 0.0    # Compras - Efetuados
        self.saldo_liquido_caixa: float = 0.0  # Recebidos - Efetuados

        self.historico_notas: List[Dict[str, Any]] = []
        self.historico_pagamentos: List[Dict[str, Any]] = []

    def calcular_saldos(self):
        """Atualiza os saldos derivados com base nas movimentações acumuladas."""
        self.contas_a_receber = round(max(0.0, self.total_vendas - self.pagamentos_recebidos), 2)
        self.contas_a_pagar = round(max(0.0, self.total_compras - self.pagamentos_efetuados), 2)
        self.saldo_liquido_caixa = round(self.pagamentos_recebidos - self.pagamentos_efetuados, 2)
        
        # Adiantamentos: Pagamentos além das dívidas
        self.adiantamento_cliente = round(max(0.0, self.pagamentos_recebidos - self.total_vendas), 2)
        self.adiantamento_fornecedor = round(max(0.0, self.pagamentos_efetuados - self.total_compras), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Exporta os dados formatados em dicionário para consumo por interfaces ou APIs."""
        self.calcular_saldos()
        return {
            "id_dono": self.id_dono,
            "tipo_dono": self.tipo_dono,
            "nome_dono": self.nome_dono,
            "resumo": {
                "total_vendas": round(self.total_vendas, 2),
                "total_compras": round(self.total_compras, 2),
                "total_devolucoes": round(self.total_devolucoes, 2),
                "total_perdas": round(self.total_perdas, 2),
                "lucro_bruto_estimado": round(self.lucro_bruto_estimado, 2),
                "pagamentos_recebidos": round(self.pagamentos_recebidos, 2),
                "pagamentos_efetuados": round(self.pagamentos_efetuados, 2),
                "contas_a_receber": self.contas_a_receber,
                "contas_a_pagar": self.contas_a_pagar,
                "saldo_liquido_caixa": self.saldo_liquido_caixa,
                "adiantamento_cliente": getattr(self, 'adiantamento_cliente', 0.0),
                "adiantamento_fornecedor": getattr(self, 'adiantamento_fornecedor', 0.0),
            },
            "historico_notas": sorted(self.historico_notas, key=lambda x: x["id_fluxo_nota"], reverse=True),
            "historico_pagamentos": sorted(self.historico_pagamentos, key=lambda x: x["id_pagamento"], reverse=True)
        }


class RelatorioFinanceiroHelper:
    """
    Classe utilitária para formatação e processamento de dados para exibição em relatórios.
    """
    @staticmethod
    def formatar_moeda(valor: float) -> str:
        """Formata um valor numérico para o padrão de moeda brasileiro R$ X.XXX,XX."""
        if valor is None:
            valor = 0.0
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def gerar_markdown_extrato(extrato: ExtratoFinanceiro) -> str:
        """Gera um relatório formatado em GitHub Markdown a partir de um ExtratoFinanceiro."""
        res = extrato.to_dict()["resumo"]
        fmt = RelatorioFinanceiroHelper.formatar_moeda

        md = []
        md.append(f"# Extrato Financeiro — {extrato.nome_dono}")
        md.append(f"**Tipo de Titular:** `{extrato.tipo_dono}` | **ID:** `{extrato.id_dono}`\n")
        md.append("## Resumo Financeiro\n")
        md.append("| Métrica | Valor |")
        md.append("|---|---|")
        md.append(f"| **Vendas Brutas** | {fmt(res['total_vendas'])} |")
        md.append(f"| **Compras / Aquisições** | {fmt(res['total_compras'])} |")
        md.append(f"| **Devoluções** | {fmt(res['total_devolucoes'])} |")
        md.append(f"| **Perdas Abatidas** | {fmt(res['total_perdas'])} |")
        md.append(f"| **Lucro Bruto Estimado** | {fmt(res['lucro_bruto_estimado'])} |")
        md.append(f"| **Pagamentos Recebidos** | {fmt(res['pagamentos_recebidos'])} |")
        md.append(f"| **Pagamentos Efetuados** | {fmt(res['pagamentos_efetuados'])} |")
        md.append(f"| **Contas a Receber (Pendente)** | {fmt(res['contas_a_receber'])} |")
        md.append(f"| **Contas a Pagar (Pendente)** | {fmt(res['contas_a_pagar'])} |")
        md.append(f"| **Saldo Líquido em Caixa** | **{fmt(res['saldo_liquido_caixa'])}** |\n")

        if extrato.historico_pagamentos:
            md.append("### Histórico de Pagamentos\n")
            md.append("| ID Nota | Tipo Nota | Forma Pagamento | Valor | Data |")
            md.append("|---|---|---|---|---|")
            for pag in extrato.historico_pagamentos:
                md.append(f"| {pag.get('id_fluxo_nota')} | {pag.get('tipo_nota', 'N/A')} | {pag.get('forma_pagamento', 'N/A')} | {fmt(pag.get('valor'))} | {pag.get('data_pagamento')} |")

        return "\n".join(md)

    @staticmethod
    def gerar_markdown_global(resumo_global: Dict[str, Any]) -> str:
        """Gera um relatório financeiro consolidado global em Markdown."""
        fmt = RelatorioFinanceiroHelper.formatar_moeda
        md = []
        md.append("# Relatório Financeiro Consolidado Global\n")
        md.append("## Visão Geral das Operações\n")
        md.append("| Indicador | Valor Consolidado |")
        md.append("|---|---|")
        md.append(f"| Total Faturamento (Vendas) | {fmt(resumo_global.get('total_vendas'))} |")
        md.append(f"| Total Compras / Insumos | {fmt(resumo_global.get('total_compras'))} |")
        md.append(f"| Total Devoluções | {fmt(resumo_global.get('total_devolucoes'))} |")
        md.append(f"| Total Perdas | {fmt(resumo_global.get('total_perdas'))} |")
        md.append(f"| Lucro Bruto Geral | {fmt(resumo_global.get('lucro_bruto_estimado'))} |")
        md.append(f"| Total Recebido | {fmt(resumo_global.get('pagamentos_recebidos'))} |")
        md.append(f"| Total Pago | {fmt(resumo_global.get('pagamentos_efetuados'))} |")
        md.append(f"| Contas a Receber Global | {fmt(resumo_global.get('contas_a_receber'))} |")
        md.append(f"| Contas a Pagar Global | {fmt(resumo_global.get('contas_a_pagar'))} |")
        md.append(f"| **Saldo em Caixa Geral** | **{fmt(resumo_global.get('saldo_liquido_caixa'))}** |\n")
        return "\n".join(md)


# ─────────────────────────────────────────────────────────────────────────────
# Classe Principal: PaymentManager
# ─────────────────────────────────────────────────────────────────────────────

class PaymentManager:
    """
    Gerenciador Central de Pagamentos e Cadastro Financeiro de Entidades.
    
    Responsável por:
      1. Receber requisições via dicionário (UI/APIs) para cadastrar Pessoas, Empresas
         e vincular Entidades (Cliente, Fornecedor, Funcionário).
      2. Registrar fluxo de pagamentos (`fluxoPagamentoNotas`).
      3. Calcular custos, lucros, pagamentos e saldos vinculados a cada Entidade.
      4. Aplicar a regra de titularidade: para qualquer entidade vinculada a uma Empresa,
         TODOS os valores, custos, lucros e saldos pertencem e consolidam na EMPRESA.
      5. Comunicar-se de forma eficiente com o `InventoryManager` via dicionários
         e instâncias sem exigir alterações na estrutura existente.
      6. Fornecer extratos e relatórios financeiros em dicionário ou Markdown.
    """

    # ─────────────────────────────────────────────────────────────────
    # 1. CADASTRO DE PESSOAS, EMPRESAS E VÍNCULO DE ENTIDADES (VIA DICT)
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _obter_registro_generico(cls, tipo: str) -> RegistroGenerico:
        """Converte uma string de tipo de contato em RegistroGenerico com fallback seguro."""
        try:
            return RegistroGenerico.por_nome(tipo)
        except Exception:
            return RegistroGenerico.OUTRO

    @classmethod
    def cadastrar_pessoa(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cadastra uma nova Pessoa física no sistema a partir de um dicionário.
        
        Formato esperado de 'dados':
        {
            "nome": str,
            "sexo": str ("MASCULINO", "FEMININO", "OUTRO") ou int (1, 2, 3),
            "is_cliente": bool (opcional, padrão False),
            "is_fornecedor": bool (opcional, padrão False),
            "is_funcionario": bool (opcional, padrão False),
            "contatos": {"TELEFONE": "...", "EMAIL": "...", "CPF": "..."} (opcional)
        }
        """
        try:
            nome = dados.get("nome")
            if not nome:
                return {"sucesso": False, "mensagem": "O campo 'nome' é obrigatório."}

            sexo_input = dados.get("sexo", "OUTROS")
            sexo_enum = None
            if isinstance(sexo_input, int):
                for g in Sexo:
                    if g.codigo == sexo_input:
                        sexo_enum = g
                        break
            elif isinstance(sexo_input, str):
                for g in Sexo:
                    if g.descricao.upper() == sexo_input.upper() or g.name.upper() == sexo_input.upper():
                        sexo_enum = g
                        break
            if not sexo_enum:
                sexo_enum = Sexo.OUTROS

            pessoa_obj = Pessoa(0, nome, sexo_enum)
            contatos = dados.get("contatos", {})
            for tipo, val in contatos.items():
                rgt_enum = cls._obter_registro_generico(tipo)
                from br.com.pdv.src.registro.registro import Registro
                if isinstance(val, list):
                    for v in val:
                        pessoa_obj.adicionarRegistro(Registro(rgt_enum, str(v)))
                else:
                    pessoa_obj.adicionarRegistro(Registro(rgt_enum, str(val)))

            # Persiste a pessoa
            id_pessoa = PeopleClassFactory.salvar(pessoa_obj)
            if id_pessoa <= 0:
                return {"sucesso": False, "mensagem": "Falha ao salvar pessoa no banco."}

            # Obtém a entidade gerada automaticamente pelo PeopleClassFactory
            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            id_entidade = None
            for ent in entidades:
                if ent["id_pessoa"] == id_pessoa and ent["id_empresa"] is None:
                    id_entidade = ent["id"]
                    break

            # Atualiza flags de papel (Cliente, Fornecedor, Funcionário) se solicitado
            is_cli = 1 if dados.get("is_cliente") else 0
            is_forn = 1 if dados.get("is_fornecedor") else 0
            is_func = 1 if dados.get("is_funcionario") else 0

            if is_cli or is_forn or is_func:
                with BancoDB.obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE entidades SET cliente = ?, fornecedor = ?, funcionario = ? WHERE id = ?",
                        (is_cli, is_forn, is_func, id_entidade)
                    )
                    conn.commit()

            return {
                "sucesso": True,
                "mensagem": f"Pessoa '{nome}' cadastrada com sucesso.",
                "id_pessoa": id_pessoa,
                "id_entidade": id_entidade
            }

        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao cadastrar pessoa: {e}"}

    @classmethod
    def cadastrar_empresa(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cadastra uma nova Empresa no sistema a partir de um dicionário.
        
        Formato esperado de 'dados':
        {
            "nome": str,
            "is_cliente": bool (opcional),
            "is_fornecedor": bool (opcional),
            "is_funcionario": bool (opcional),
            "contatos": {"CNPJ": "...", "TELEFONE": "..."} (opcional),
            "representantes": [{"id_pessoa": int, "cargo": int|str, "is_cliente": bool, "is_fornecedor": bool, "is_funcionario": bool}] (opcional)
        }
        """
        try:
            nome = dados.get("nome")
            if not nome:
                return {"sucesso": False, "mensagem": "O campo 'nome' é obrigatório."}

            empresa_obj = Empresa(0, nome)
            contatos = dados.get("contatos", {})
            for tipo, val in contatos.items():
                rgt_enum = cls._obter_registro_generico(tipo)
                from br.com.pdv.src.registro.registro import Registro
                if isinstance(val, list):
                    for v in val:
                        empresa_obj.adicionarRegistro(Registro(rgt_enum, str(v)))
                else:
                    empresa_obj.adicionarRegistro(Registro(rgt_enum, str(val)))

            id_empresa = EnterpriseClassFactory.salvar(empresa_obj)
            if id_empresa <= 0:
                return {"sucesso": False, "mensagem": "Falha ao salvar empresa no banco."}

            # Obtém a entidade gerada automaticamente para a empresa pura (sem pessoa)
            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            id_entidade_empresa = None
            for ent in entidades:
                if ent["id_empresa"] == id_empresa and ent["id_pessoa"] is None:
                    id_entidade_empresa = ent["id"]
                    break

            is_cli = 1 if dados.get("is_cliente") else 0
            is_forn = 1 if dados.get("is_fornecedor") else 0
            is_func = 1 if dados.get("is_funcionario") else 0

            if (is_cli or is_forn or is_func) and id_entidade_empresa:
                with BancoDB.obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE entidades SET cliente = ?, fornecedor = ?, funcionario = ? WHERE id = ?",
                        (is_cli, is_forn, is_func, id_entidade_empresa)
                    )
                    conn.commit()

            # Representantes internos da empresa (cria a 3ª entidade de VÍNCULO Pessoa+Empresa+Cargo)
            reps = dados.get("representantes", [])
            vinculos_criados = []
            for rep in reps:
                id_p = rep.get("id_pessoa")
                if id_p:
                    res_vinc = cls.vincular_pessoa_empresa({
                        "id_pessoa": id_p,
                        "id_empresa": id_empresa,
                        "cargo": rep.get("cargo", "SOCIO"),
                        "is_cliente": rep.get("is_cliente", False),
                        "is_fornecedor": rep.get("is_fornecedor", False),
                        "is_funcionario": rep.get("is_funcionario", True)
                    })
                    if res_vinc.get("sucesso"):
                        vinculos_criados.append(res_vinc.get("id_entidade"))

            return {
                "sucesso": True,
                "mensagem": f"Empresa '{nome}' cadastrada com sucesso.",
                "id_empresa": id_empresa,
                "id_entidade": id_entidade_empresa,
                "id_entidade_empresa": id_entidade_empresa,
                "entidades_vinculos": vinculos_criados
            }

        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao cadastrar empresa: {e}"}

    @classmethod
    def vincular_pessoa_empresa(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria ou atualiza uma ENTIDADE DE VÍNCULO entre uma Pessoa Física e uma Empresa (Pessoa Jurídica),
        cadastrando o CARGO dessa pessoa na empresa na tabela 'entidades_cargos'.
        
        Permite que a entidade possua as 3 opções simultaneamente (cliente=1, fornecedor=1, funcionario=1).
        
        Formato esperado de 'dados':
        {
            "id_pessoa": int,
            "id_empresa": int,
            "cargo": int | str (ex: 2 ou "SOCIO", "GERENTE", "COMPRADOR"),
            "is_cliente": bool (opcional),
            "is_fornecedor": bool (opcional),
            "is_funcionario": bool (opcional, padrão True)
        }
        """
        try:
            id_p = dados.get("id_pessoa")
            id_e = dados.get("id_empresa")
            if not id_p or not id_e:
                return {"sucesso": False, "mensagem": "'id_pessoa' e 'id_empresa' são obrigatórios."}

            pes_db = DB.SELECT.PESSOA_POR_ID.buscar_um(id_p)
            if not pes_db:
                return {"sucesso": False, "mensagem": f"Pessoa ID {id_p} não encontrada."}

            emp_db = DB.SELECT.EMPRESA_POR_ID.buscar_um(id_e)
            if not emp_db:
                return {"sucesso": False, "mensagem": f"Empresa ID {id_e} não encontrada."}

            is_cli = 1 if dados.get("is_cliente") else 0
            is_forn = 1 if dados.get("is_fornecedor") else 0
            is_func = 1 if dados.get("is_funcionario", True) else 0

            # Procura se já existe a entidade de VÍNCULO (id_pessoa = X AND id_empresa = Y)
            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            ent_vinculo = None
            for ent in entidades:
                if ent["id_pessoa"] == id_p and ent["id_empresa"] == id_e:
                    ent_vinculo = ent
                    break

            if ent_vinculo:
                id_entidade = ent_vinculo["id"]
                with BancoDB.obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE entidades SET cliente = ?, fornecedor = ?, funcionario = ? WHERE id = ?",
                        (is_cli, is_forn, is_func, id_entidade)
                    )
                    conn.commit()
            else:
                id_entidade = DB.INSERT.ENTIDADE.executar(id_p, id_e, is_forn, is_cli, is_func)

            # Resolve o Cargo (Enum Cargo)
            cargo_input = dados.get("cargo", 21)  # 21 = "não definido" / OUTROS
            from br.com.pdv.src.pessoa.cargos import Cargo
            cargo_enum = None
            if isinstance(cargo_input, int):
                for c in Cargo:
                    if c.codigo == cargo_input:
                        cargo_enum = c; break
            elif isinstance(cargo_input, str):
                for c in Cargo:
                    if c.descricao.upper() == cargo_input.upper() or c.name.upper() == cargo_input.upper():
                        cargo_enum = c; break
            if not cargo_enum:
                cargo_enum = Cargo.OUTROS

            # Remove cargos prévios da entidade de vínculo e insere o novo cargo
            with BancoDB.obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM entidades_cargos WHERE id_entidade = ?", (id_entidade,))
                cursor.execute("INSERT INTO entidades_cargos (id_entidade, id_cargo) VALUES (?, ?)", (id_entidade, cargo_enum.codigo))
                conn.commit()

            return {
                "sucesso": True,
                "mensagem": f"Vínculo registrado com sucesso! Pessoa '{pes_db['nome']}' na Empresa '{emp_db['nome']}' com o cargo '{cargo_enum.descricao}'.",
                "id_entidade": id_entidade,
                "id_pessoa": id_p,
                "id_empresa": id_e,
                "id_cargo": cargo_enum.codigo,
                "cargo_nome": cargo_enum.descricao,
                "papeis": {
                    "cliente": bool(is_cli),
                    "fornecedor": bool(is_forn),
                    "funcionario": bool(is_func)
                }
            }

        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao vincular pessoa e empresa: {e}"}

    @classmethod
    def vincular_entidade(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria ou atualiza os papéis de uma Entidade.
        Se informados 'id_pessoa' E 'id_empresa' (ou se houver 'cargo'), delega para 'vincular_pessoa_empresa'.
        """
        id_p = dados.get("id_pessoa")
        id_e = dados.get("id_empresa")
        if id_p and id_e:
            return cls.vincular_pessoa_empresa(dados)

        try:
            if not id_p and not id_e:
                return {"sucesso": False, "mensagem": "Deve informar 'id_pessoa' ou 'id_empresa'."}

            is_cli = 1 if dados.get("is_cliente") else 0
            is_forn = 1 if dados.get("is_fornecedor") else 0
            is_func = 1 if dados.get("is_funcionario") else 0

            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            ent_existente = None
            for ent in entidades:
                if id_e and ent["id_empresa"] == id_e and ent["id_pessoa"] is None:
                    ent_existente = ent; break
                if id_p and ent["id_pessoa"] == id_p and ent["id_empresa"] is None:
                    ent_existente = ent; break

            if ent_existente:
                id_ent = ent_existente["id"]
                with BancoDB.obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE entidades SET cliente = ?, fornecedor = ?, funcionario = ? WHERE id = ?",
                        (is_cli, is_forn, is_func, id_ent)
                    )
                    conn.commit()
                msg = f"Vínculos da entidade ID {id_ent} atualizados."
            else:
                id_ent = DB.INSERT.ENTIDADE.executar(id_p, id_e, is_forn, is_cli, is_func)
                msg = f"Nova entidade registrada com ID {id_ent}."

            return {
                "sucesso": True,
                "mensagem": msg,
                "id_entidade": id_ent
            }

        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao vincular entidade: {e}"}

    @classmethod
    def obter_entidades_detalhadas(cls) -> List[Dict[str, Any]]:
        """
        Retorna todas as entidades do banco detalhando o seu tipo:
          - 'PESSOA_PURA' (entidade de pessoa física sem empresa)
          - 'EMPRESA_PURA' (entidade de empresa sem pessoa)
          - 'VINCULO_PESSOA_EMPRESA' (entidade de vínculo com pessoa + empresa + cargo)
        com suporte às 3 opções ativas simultaneamente (cliente, fornecedor, funcionario).
        """
        entidades = DB.SELECT.VW_ENTIDADE_COMPLETA_TODOS.buscar()
        resultado = []

        for ent in entidades:
            id_ent = ent["id"]
            id_p = ent.get("pessoa_id")
            id_e = ent.get("empresa_id")

            if id_p is not None and id_e is not None:
                tipo_entidade = "VINCULO_PESSOA_EMPRESA"
            elif id_e is not None:
                tipo_entidade = "EMPRESA_PURA"
            else:
                tipo_entidade = "PESSOA_PURA"

            cargos_rows = DB.SELECT.CARGO_POR_ENTIDADE.buscar(id_ent)
            cargos_list = []
            if cargos_rows:
                from br.com.pdv.src.pessoa.cargos import Cargo
                for cr in cargos_rows:
                    id_c = cr.get("id_cargo")
                    for cg in Cargo:
                        if cg.codigo == id_c:
                            cargos_list.append({"id_cargo": id_c, "descricao": cg.descricao})

            # Registros de contato vinculados a ESTA entidade específica
            registros_rows = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(id_ent)
            registros_list = []
            if registros_rows:
                for r in registros_rows:
                    id_tipo = r.get("id_tipos_registros")
                    reg_val = r.get("registro")
                    try:
                        tipo_obj = RegistroGenerico.por_codigo(id_tipo)
                        tipo_nome = tipo_obj.getNome()
                    except Exception:
                        tipo_nome = f"Tipo {id_tipo}"
                    registros_list.append({"tipo": tipo_nome, "valor": reg_val})

            try:
                extrato = cls.get_extrato_entidade(id_ent)
                saldo_devedor = extrato.get("resumo", {}).get("contas_a_receber", 0.0)
                saldo_fornecedor = extrato.get("resumo", {}).get("contas_a_pagar", 0.0)
                adiantamento_c = extrato.get("resumo", {}).get("adiantamento_cliente", 0.0)
                adiantamento_f = extrato.get("resumo", {}).get("adiantamento_fornecedor", 0.0)
            except Exception:
                saldo_devedor = 0.0
                saldo_fornecedor = 0.0
                adiantamento_c = 0.0
                adiantamento_f = 0.0

            resultado.append({
                "id_entidade": id_ent,
                "tipo_entidade": tipo_entidade,
                "id_pessoa": id_p,
                "pessoa_nome": ent.get("pessoa_nome"),
                "id_empresa": id_e,
                "empresa_nome": ent.get("empresa_nome"),
                "is_cliente": bool(ent.get("cliente")),
                "is_fornecedor": bool(ent.get("fornecedor")),
                "is_funcionario": bool(ent.get("funcionario")),
                "cargos": cargos_list,
                "contatos": registros_list,
                "saldo_devedor_cliente": saldo_devedor,
                "saldo_devedor_fornecedor": saldo_fornecedor,
                "adiantamento_cliente": adiantamento_c,
                "adiantamento_fornecedor": adiantamento_f
            })

        return resultado

    @classmethod
    def cadastrar_entidade_completa(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método unificado que recebe uma requisição completa via dicionário
        e decide se cria Pessoa, Empresa ou um Vínculo completo.
        """
        tipo = dados.get("tipo", "PESSOA").upper()
        if tipo == "EMPRESA":
            return cls.cadastrar_empresa(dados)
        elif tipo == "PESSOA":
            return cls.cadastrar_pessoa(dados)
        elif tipo == "VINCULO":
            return cls.cadastrar_vinculo_completo(dados)
        else:
            return {"sucesso": False, "mensagem": f"Tipo de cadastro '{tipo}' inválido."}

    @classmethod
    def cadastrar_vinculo_completo(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma Pessoa e uma Empresa simultaneamente (se não informadas)
        e já estabelece o Vínculo entre elas.
        """
        id_pessoa = dados.get("id_pessoa_existente")
        if not id_pessoa:
            pessoa_dados = dados.get("pessoa", {})
            pessoa_dados["is_cliente"] = False
            pessoa_dados["is_fornecedor"] = False
            pessoa_dados["is_funcionario"] = False
            res_p = cls.cadastrar_pessoa(pessoa_dados)
            if not res_p.get("sucesso"):
                return res_p
            id_pessoa = res_p.get("id_pessoa")

        id_empresa = dados.get("id_empresa_existente")
        if not id_empresa:
            empresa_dados = dados.get("empresa", {})
            empresa_dados["is_cliente"] = False
            empresa_dados["is_fornecedor"] = False
            empresa_dados["is_funcionario"] = False
            res_e = cls.cadastrar_empresa(empresa_dados)
            if not res_e.get("sucesso"):
                return res_e
            id_empresa = res_e.get("id_empresa")

        res_vinc = cls.vincular_pessoa_empresa({
            "id_pessoa": id_pessoa,
            "id_empresa": id_empresa,
            "cargo": dados.get("cargo", 21),
            "is_cliente": dados.get("is_cliente", False),
            "is_fornecedor": dados.get("is_fornecedor", False),
            "is_funcionario": dados.get("is_funcionario", False)
        })
        
        return res_vinc

    @classmethod
    def apagar_entidade(cls, id_entidade: int) -> Dict[str, Any]:
        """
        Apaga uma entidade e todos os seus ramificados.
        Bloqueia a exclusão se houver alguma nota vinculada a ela ou aos seus ramificados.
        """
        try:
            from br.com.pdv.src.BDD.bancodb import BancoDB
            banco = BancoDB()
            with banco.obter_conexao() as conn:
                cursor = conn.cursor()
                
                # 1. Buscar a entidade base
                cursor.execute("SELECT id_pessoa, id_empresa FROM entidades WHERE id = ?", (id_entidade,))
                row = cursor.fetchone()
                if not row:
                    return {"sucesso": False, "mensagem": "Entidade não encontrada."}
                
                id_pessoa = row[0]
                id_empresa = row[1]
                
                # 2. Descobrir todos os IDs de entidades afetados (ramificações)
                ids_afetados = set()
                ids_afetados.add(id_entidade)
                
                if id_pessoa is not None and id_empresa is None:
                    # É pessoa pura, afeta qualquer vínculo com esse id_pessoa
                    cursor.execute("SELECT id FROM entidades WHERE id_pessoa = ?", (id_pessoa,))
                    for r in cursor.fetchall(): ids_afetados.add(r[0])
                elif id_empresa is not None and id_pessoa is None:
                    # É empresa pura, afeta qualquer vínculo com esse id_empresa
                    cursor.execute("SELECT id FROM entidades WHERE id_empresa = ?", (id_empresa,))
                    for r in cursor.fetchall(): ids_afetados.add(r[0])
                    
                # 3. Verificar notas financeiras vinculadas a qualquer um dos ids afetados
                placeholders = ",".join(["?"] * len(ids_afetados))
                cursor.execute(f"SELECT id FROM fluxosNotasEstoque WHERE id_representante IN ({placeholders}) LIMIT 1", tuple(ids_afetados))
                if cursor.fetchone():
                    return {"sucesso": False, "mensagem": "Exclusão bloqueada: Esta entidade (ou seus vínculos) possui histórico de notas cadastrado."}
                
                # 4. Apagar em cascata
                for eid in ids_afetados:
                    cursor.execute("DELETE FROM registro WHERE id_entidade = ?", (eid,))
                    cursor.execute("DELETE FROM entidades_cargos WHERE id_entidade = ?", (eid,))
                    cursor.execute("DELETE FROM entidades WHERE id = ?", (eid,))
                    
                # Se era pura, apagar da tabela raiz
                if id_pessoa is not None and id_empresa is None:
                    cursor.execute("DELETE FROM pessoas WHERE id = ?", (id_pessoa,))
                elif id_empresa is not None and id_pessoa is None:
                    cursor.execute("DELETE FROM empresas WHERE id = ?", (id_empresa,))
                    
                conn.commit()
                return {"sucesso": True, "mensagem": "Entidade apagada com sucesso."}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"sucesso": False, "mensagem": f"Erro interno ao apagar entidade: {e}"}

    @classmethod
    def editar_entidade(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza o nome, papéis, cargo e contatos da entidade.
        """
        try:
            id_entidade = dados.get("id_entidade")
            if not id_entidade:
                return {"sucesso": False, "mensagem": "ID da entidade não fornecido."}
                
            from br.com.pdv.src.BDD.bancodb import BancoDB
            banco = BancoDB()
            with banco.obter_conexao() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id_pessoa, id_empresa FROM entidades WHERE id = ?", (id_entidade,))
                row = cursor.fetchone()
                if not row:
                    return {"sucesso": False, "mensagem": "Entidade não encontrada."}
                
                id_pessoa = row[0]
                id_empresa = row[1]
                
                # Atualiza nome se fornecido
                novo_nome = dados.get("nome")
                if novo_nome:
                    if id_pessoa is not None and id_empresa is None:
                        cursor.execute("UPDATE pessoas SET nome = ? WHERE id = ?", (novo_nome, id_pessoa))
                    elif id_empresa is not None and id_pessoa is None:
                        cursor.execute("UPDATE empresas SET nome = ? WHERE id = ?", (novo_nome, id_empresa))
                        
                # Atualiza flags de papel (is_cliente, is_fornecedor, is_funcionario)
                is_cliente = 1 if dados.get("is_cliente") else 0
                is_fornecedor = 1 if dados.get("is_fornecedor") else 0
                is_funcionario = 1 if dados.get("is_funcionario") else 0
                cursor.execute(
                    "UPDATE entidades SET cliente = ?, fornecedor = ?, funcionario = ? WHERE id = ?",
                    (is_cliente, is_fornecedor, is_funcionario, id_entidade)
                )
                
                # Atualiza cargo (apenas se fornecido)
                novo_cargo = dados.get("cargo")
                if novo_cargo:
                    cursor.execute("DELETE FROM entidades_cargos WHERE id_entidade = ?", (id_entidade,))
                    cursor.execute("INSERT INTO entidades_cargos (id_entidade, id_cargo) VALUES (?, ?)", (id_entidade, novo_cargo))
                    
                # Atualiza Contatos (se vieram)
                contatos = dados.get("contatos")
                if contatos is not None and isinstance(contatos, dict):
                    cursor.execute("DELETE FROM registro WHERE id_entidade = ?", (id_entidade,))
                    for k, v in contatos.items():
                        if v:
                            reg_tipo = cls._obter_registro_generico(k)
                            cursor.execute("INSERT INTO registro (id_tipos_registros, id_entidade, registro) VALUES (?, ?, ?)", (reg_tipo.codigo, id_entidade, v))
                            
                conn.commit()
                return {"sucesso": True, "mensagem": "Entidade atualizada com sucesso."}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"sucesso": False, "mensagem": f"Erro interno ao editar entidade: {e}"}

    # ─────────────────────────────────────────────────────────────────
    # 2. FLUXO DE PAGAMENTO DE NOTAS
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def registrar_pagamento(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra uma parcela ou pagamento total referente a uma nota.
        
        Formato de 'dados':
        {
            "id_fluxo_nota": int,
            "id_forma_pagamento": int (1=Dinheiro, 2=Cartão Crédito, 3=Débito, 4=Pix, etc.),
            "valor": float,
            "data": "YYYY-MM-DD" (opcional)
        }
        """
        try:
            id_nota = dados.get("id_fluxo_nota")
            id_forma = dados.get("id_forma_pagamento", 1)
            valor = dados.get("valor")
            if not id_nota or valor is None or valor <= 0:
                return {"sucesso": False, "mensagem": "'id_fluxo_nota' e 'valor' válido são obrigatórios."}

            nota_hdr = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_nota)
            if not nota_hdr:
                return {"sucesso": False, "mensagem": f"Nota ID {id_nota} não encontrada no banco."}

            if nota_hdr["id_tipoNota"] == 1:
                saldo_atual = cls.get_resumo_financeiro_global().get("saldo_liquido_caixa", 0.0)
                if valor > saldo_atual:
                    return {"sucesso": False, "mensagem": f"Saldo insuficiente em caixa (Saldo atual: R$ {saldo_atual:.2f})."}

            data_pag = dados.get("data") or str(date.today())

            id_pag = DB.INSERT.FLUXO_PAGAMENTO_NOTA.executar(
                id_nota, id_forma, valor, data_pag
            )

            if id_pag and id_pag > 0:
                return {
                    "sucesso": True,
                    "mensagem": f"Pagamento de R$ {valor:.2f} registrado para a nota ID {id_nota}.",
                    "id_pagamento": id_pag,
                    "id_fluxo_nota": id_nota,
                    "valor": valor
                }
            else:
                return {"sucesso": False, "mensagem": "Falha ao gravar pagamento no banco."}

        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao registrar pagamento: {e}"}

    @classmethod
    def registrar_pagamento_por_entidade(cls, id_entidade: int, valor_total: float, id_forma_pagamento: int = 1) -> Dict[str, Any]:
        """
        Liquida notas em aberto da entidade, da mais antiga para a mais recente (FIFO).
        Se houver sobra, fica como adiantamento.
        """
        try:
            if valor_total <= 0:
                return {"sucesso": False, "mensagem": "O valor precisa ser maior que zero."}
                
            extrato = cls.get_extrato_entidade(id_entidade)
            notas = extrato.get("historico_notas", [])
            
            notas_validas = [n for n in notas if n["id_tipoNota"] in (1, 2)]
            notas_validas.sort(key=lambda x: x["id_fluxo_nota"])
            
            pagamentos_realizados = []
            valor_restante = valor_total
            
            for n in notas_validas:
                if valor_restante <= 0:
                    break
                    
                id_nota = n["id_fluxo_nota"]
                v_total_nota = n["total_nota"]
                
                pags_nota = sum(p["valor"] for p in extrato.get("historico_pagamentos", []) if p["id_fluxo_nota"] == id_nota)
                saldo_devedor_nota = max(0.0, v_total_nota - pags_nota)
                
                if saldo_devedor_nota > 0:
                    valor_a_pagar = min(valor_restante, saldo_devedor_nota)
                    dados_pag = {
                        "id_fluxo_nota": id_nota,
                        "id_forma_pagamento": id_forma_pagamento,
                        "valor": valor_a_pagar,
                        "data": str(date.today())
                    }
                    
                    resp = cls.registrar_pagamento(dados_pag)
                    if resp.get("sucesso"):
                        valor_restante -= valor_a_pagar
                        pagamentos_realizados.append({"id_fluxo_nota": id_nota, "valor_pago": valor_a_pagar})
                    else:
                        return {"sucesso": False, "mensagem": resp.get("mensagem")}
                        
            msg_sobra = f" (Sobrou R$ {valor_restante:.2f} como adiantamento)" if valor_restante > 0 else ""
            return {
                "sucesso": True,
                "mensagem": f"Pagamento distribuído em {len(pagamentos_realizados)} notas" + msg_sobra,
                "pagamentos": pagamentos_realizados,
                "sobra": valor_restante
            }
            
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro na liquidação por entidade: {e}"}

    @classmethod
    def obter_pagamentos_nota(cls, id_fluxo_nota: int) -> List[Dict[str, Any]]:
        """Retorna todos os pagamentos efetuados/recebidos para uma nota específica."""
        try:
            pags = DB.SELECT.FLUXO_PAGAMENTO_POR_NOTA.buscar(id_fluxo_nota)
            return pags or []
        except Exception as e:
            print(f"[PaymentManager] Erro ao buscar pagamentos da nota {id_fluxo_nota}: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────
    # 3. CÁLCULOS FINANCEIROS E REGRAS DE TITULARIDADE DA EMPRESA
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _obter_mapa_entidade_titular(cls) -> Dict[int, Dict[str, Any]]:
        """
        Retorna um dicionário mapeando cada `id_entidade` para a sua estrutura de Titular
        (Empresa ou Pessoa), aplicando a regra de negócio:
        
        REGRA: Se a entidade estiver vinculada a uma Empresa (id_empresa != None),
        TODOS os valores e saldos pertencem à EMPRESA, mesmo que haja pessoa vinculada.
        """
        entidades = DB.SELECT.VW_ENTIDADE_COMPLETA_TODOS.buscar()
        mapa = {}

        for ent in entidades:
            id_ent = ent["id"]
            id_emp = ent.get("empresa_id")
            id_pes = ent.get("pessoa_id")

            if id_emp is not None:
                dono_id = id_emp
                tipo_dono = "EMPRESA"
                nome_dono = ent.get("empresa_nome") or f"Empresa ID {id_emp}"
            elif id_pes is not None:
                dono_id = id_pes
                tipo_dono = "PESSOA"
                nome_dono = ent.get("pessoa_nome") or f"Pessoa ID {id_pes}"
            else:
                dono_id = id_ent
                tipo_dono = "ENTIDADE"
                nome_dono = f"Entidade ID {id_ent}"

            mapa[id_ent] = {
                "id_entidade": id_ent,
                "dono_id": dono_id,
                "tipo_dono": tipo_dono,
                "nome_dono": nome_dono,
                "id_empresa": id_emp,
                "id_pessoa": id_pes,
            }
        return mapa

    @classmethod
    def get_extrato_empresa(cls, id_empresa: int) -> Dict[str, Any]:
        """
        Calcula a posição financeira consolidada de uma Empresa.
        Agrupa TODAS as entidades pertencentes a essa Empresa.
        """
        nome_empresa = f"Empresa ID {id_empresa}"
        emp_db = DB.SELECT.EMPRESA_POR_ID.buscar_um(id_empresa)
        if emp_db:
            nome_empresa = emp_db.get("nome", nome_empresa)

        extrato = ExtratoFinanceiro(id_empresa, "EMPRESA", nome_empresa)

        mapa_titulares = cls._obter_mapa_entidade_titular()
        entidades_empresa = [id_ent for id_ent, info in mapa_titulares.items() if info["id_empresa"] == id_empresa]

        if not entidades_empresa:
            return extrato.to_dict()

        cls._consolidar_movimentacoes_para_entidades(entidades_empresa, extrato)
        return extrato.to_dict()

    @classmethod
    def get_extrato_pessoa(cls, id_pessoa: int) -> Dict[str, Any]:
        """
        Calcula a posição financeira de uma Pessoa física que NÃO esteja sob o CNPJ de uma Empresa.
        """
        nome_pessoa = f"Pessoa ID {id_pessoa}"
        pes_db = DB.SELECT.PESSOA_POR_ID.buscar_um(id_pessoa)
        if pes_db:
            nome_pessoa = pes_db.get("nome", nome_pessoa)

        extrato = ExtratoFinanceiro(id_pessoa, "PESSOA", nome_pessoa)

        mapa_titulares = cls._obter_mapa_entidade_titular()
        # Seleciona apenas entidades dessa pessoa sem empresa
        entidades_pessoa = [id_ent for id_ent, info in mapa_titulares.items() if info["id_pessoa"] == id_pessoa and info["id_empresa"] is None]

        if not entidades_pessoa:
            return extrato.to_dict()

        cls._consolidar_movimentacoes_para_entidades(entidades_pessoa, extrato)
        return extrato.to_dict()

    @classmethod
    def get_extrato_entidade(cls, id_entidade: int) -> Dict[str, Any]:
        """
        Calcula a posição financeira individual de uma Entidade (Cliente ou Fornecedor).
        Se a entidade for vinculada a uma Empresa, redireciona a consolidação para o CNPJ da Empresa.
        """
        mapa_titulares = cls._obter_mapa_entidade_titular()
        info = mapa_titulares.get(id_entidade)

        if not info:
            extrato = ExtratoFinanceiro(id_entidade, "ENTIDADE", f"Entidade ID {id_entidade}")
            return extrato.to_dict()

        if info["id_empresa"] is not None:
            # Regra: Entidade da Empresa ➔ os valores são da Empresa
            return cls.get_extrato_empresa(info["id_empresa"])

        extrato = ExtratoFinanceiro(id_entidade, info["tipo_dono"], info["nome_dono"])
        cls._consolidar_movimentacoes_para_entidades([id_entidade], extrato)
        return extrato.to_dict()

    @staticmethod
    def _normalizar_reais(val: float) -> float:
        """Converte o valor para float (assumindo que o BD já armazena em reais)."""
        if val is None:
            return 0.0
        return float(val)

    @classmethod
    def _consolidar_movimentacoes_para_entidades(cls, lista_id_entidades: List[int], extrato: ExtratoFinanceiro):
        """
        Percorre o banco/InventoryManager e consolida notas de fluxo e pagamentos para as entidades especificadas.
        """
        if not lista_id_entidades:
            return

        placeholders = ",".join("?" for _ in lista_id_entidades)

        # 1. Consulta notas onde as entidades são representantes
        sql_notas = f"SELECT * FROM fluxosNotasEstoque WHERE id_representante IN ({placeholders})"
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_notas, tuple(lista_id_entidades))
            notas = [dict(row) for row in cursor.fetchall()]

        mapa_tipos = {1: "COMPRA", 2: "VENDA", 3: "DEVOLUCAO", 4: "PERDA", 5: "COMPENSACAO"}

        for nota in notas:
            id_nota = nota["id"]
            tipo_id = nota["id_tipoNota"]
            tipo_nome = mapa_tipos.get(tipo_id, "OUTRO")

            # Busca itens no fluxoEstoque
            itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            total_nota = sum((i["quantidade"] * cls._normalizar_reais(i["valorUnidario"])) for i in itens) if itens else 0.0
            lucro_nota = sum(cls._normalizar_reais(i.get("lucroTotal", 0) or 0) for i in itens) if itens else 0.0

            if tipo_id == 1:
                extrato.total_compras += total_nota
            elif tipo_id == 2:
                extrato.total_vendas += total_nota
                extrato.lucro_bruto_estimado += lucro_nota
            elif tipo_id == 3:
                extrato.total_devolucoes += total_nota
            elif tipo_id == 4:
                extrato.total_perdas += total_nota

            extrato.historico_notas.append({
                "id_fluxo_nota": id_nota,
                "id_tipoNota": tipo_id,
                "tipo_nota": tipo_nome,
                "total_nota": round(total_nota, 2),
                "lucro_nota": round(lucro_nota, 2),
                "data_vencimento": nota.get("data_vencimento")
            })

            # Busca pagamentos associados a esta nota
            pags = DB.SELECT.FLUXO_PAGAMENTO_POR_NOTA.buscar(id_nota)
            for p in (pags or []):
                val_pag = p.get("valor", 0.0)
                if tipo_id == 2:
                    extrato.pagamentos_recebidos += val_pag
                elif tipo_id == 1:
                    extrato.pagamentos_efetuados += val_pag

                extrato.historico_pagamentos.append({
                    "id_pagamento": p.get("id"),
                    "id_fluxo_nota": id_nota,
                    "tipo_nota": tipo_nome,
                    "valor": round(val_pag, 2),
                    "forma_pagamento": p.get("id_forma_pagamento"),
                    "data_pagamento": p.get("data_pagamento")
                })

        extrato.calcular_saldos()

    @classmethod
    def get_historico_movimentacoes_global(cls) -> List[Dict[str, Any]]:
        """Retorna o histórico completo de movimentações (notas) com status de pagamento."""
        mapa_entidades = cls._obter_mapa_entidade_titular()
        
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    fne.id as id_nota,
                    fne.id_tipoNota as tipo_nota,
                    fne.id_representante as id_entidade,
                    MIN(fe.data) as data_nota,
                    SUM(ABS(fe.quantidade) * fe.valorUnidario) as valor_total,
                    (SELECT SUM(fpn.valor) FROM fluxoPagamentoNotas fpn WHERE fpn.id_fluxo_nota = fne.id) as valor_pago
                FROM fluxosNotasEstoque fne
                JOIN fluxoEstoque fe ON fne.id = fe.id_fluxo_nota
                GROUP BY fne.id, fne.id_tipoNota, fne.id_representante
                ORDER BY data_nota DESC, fne.id DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            historico = []
            tipos = {1: "COMPRA", 2: "VENDA", 3: "DEVOLUÇÃO", 4: "PERDA", 5: "REPOSIÇÃO/COMPENSAÇÃO"}
            
            for row in rows:
                id_entidade = row['id_entidade']
                entidade_info = mapa_entidades.get(id_entidade, {})
                nome_entidade = entidade_info.get("nome_dono", entidade_info.get("nome", f"Desconhecido #{id_entidade}"))
                
                v_total = cls._normalizar_reais(row['valor_total'] or 0.0)
                v_pago = cls._normalizar_reais(row['valor_pago'] or 0.0)
                
                # Para Perda (4) e Reposição (5) e Devolução (3), consideramos LIQUIDADO/SEM CUSTO?
                # O usuário reclamou que reposição e perda não deveriam ter saldo pendente
                if row['tipo_nota'] in (3, 4, 5):
                    status = "CONCLUÍDO"
                elif v_total <= 0:
                    status = "PAGO"
                elif v_pago >= v_total:
                    status = "PAGO"
                elif v_pago > 0:
                    status = "PARCIAL"
                else:
                    status = "ABERTO"
                    
                historico.append({
                    "id_nota": row['id_nota'],
                    "tipo_nota_id": row['tipo_nota'],
                    "tipo_nota_str": tipos.get(row['tipo_nota'], "OUTRO"),
                    "id_entidade": id_entidade,
                    "entidade_nome": nome_entidade,
                    "data": row['data_nota'],
                    "valor_total": round(v_total, 2),
                    "valor_pago": round(v_pago, 2),
                    "status_pagamento": status
                })
                
            return historico

    @classmethod
    def get_resumo_financeiro_global(cls) -> Dict[str, Any]:
        """Calcula o resumo financeiro consolidado de TODAS as operações da empresa/sistema."""
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()

            # Vendas, compras, lucros item a item
            cursor.execute("SELECT id_tipoNota, quantidade, valorUnidario, lucroTotal FROM fluxoEstoque")
            rows = [dict(row) for row in cursor.fetchall()]

            # Pagamentos
            cursor.execute("""
                SELECT fn.id_tipoNota, SUM(fp.valor) as total_pago
                FROM fluxoPagamentoNotas fp
                JOIN fluxosNotasEstoque fn ON fp.id_fluxo_nota = fn.id
                GROUP BY fn.id_tipoNota
            """)
            totais_pags = {row["id_tipoNota"]: row["total_pago"] for row in cursor.fetchall()}

        vendas = sum(r["quantidade"] * cls._normalizar_reais(r["valorUnidario"]) for r in rows if r["id_tipoNota"] == 2)
        compras = sum(r["quantidade"] * cls._normalizar_reais(r["valorUnidario"]) for r in rows if r["id_tipoNota"] == 1)
        devolucoes = sum(r["quantidade"] * cls._normalizar_reais(r["valorUnidario"]) for r in rows if r["id_tipoNota"] == 3)
        perdas = sum(r["quantidade"] * cls._normalizar_reais(r["valorUnidario"]) for r in rows if r["id_tipoNota"] == 4)
        lucro = sum(cls._normalizar_reais(r.get("lucroTotal", 0) or 0) for r in rows if r["id_tipoNota"] == 2)

        pags_recebidos = totais_pags.get(2, 0.0) or 0.0
        pags_efetuados = totais_pags.get(1, 0.0) or 0.0

        contas_a_receber = max(0.0, vendas - pags_recebidos)
        contas_a_pagar = max(0.0, compras - pags_efetuados)
        saldo_caixa = pags_recebidos - pags_efetuados

        return {
            "total_vendas": round(vendas, 2),
            "total_compras": round(compras, 2),
            "total_devolucoes": round(devolucoes, 2),
            "total_perdas": round(perdas, 2),
            "lucro_bruto_estimado": round(lucro, 2),
            "pagamentos_recebidos": round(pags_recebidos, 2),
            "pagamentos_efetuados": round(pags_efetuados, 2),
            "contas_a_receber": round(contas_a_receber, 2),
            "contas_a_pagar": round(contas_a_pagar, 2),
            "saldo_liquido_caixa": round(saldo_caixa, 2)
        }

    @classmethod
    def registrar_pagamentos_lote(cls, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra múltiplos pagamentos para uma nota e entidade específicas,
        tipicamente vindo de uma tela de "Fechamento" que divide os valores 
        em PIX, Débito, Crédito e Dinheiro.
        """
        try:
            id_entidade = dados.get("id_entidade")
            id_nota = dados.get("id_nota")
            pagamentos = dados.get("pagamentos", [])
            
            if not id_entidade or not id_nota:
                return {"sucesso": False, "mensagem": "id_entidade e id_nota são obrigatórios."}
                
            if not pagamentos:
                return {"sucesso": False, "mensagem": "Nenhum pagamento fornecido."}
                
            mensagens = []
            
            from br.com.pdv.src.BDD.bancodb import BancoDB
            with BancoDB.obter_conexao() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id_tipoNota FROM fluxosNotasEstoque WHERE id = ?", (id_nota,))
                row = cursor.fetchone()
                if not row:
                    return {"sucesso": False, "mensagem": f"Nota de ID {id_nota} não encontrada."}
                    
                tipo_nota = int(row[0])
                
                # Definir id_tipo_registro baseado na nota
                if tipo_nota == 1: id_tipo_registro = 1
                elif tipo_nota == 2: id_tipo_registro = 2
                elif tipo_nota == 3: id_tipo_registro = 3
                elif tipo_nota == 4: id_tipo_registro = 4
                else: id_tipo_registro = 5

                from datetime import date
                hoje_str = str(date.today())

                for p in pagamentos:
                    id_forma = int(p.get("id_forma_pagamento", 1))
                    valor = float(p.get("valor", 0))
                    if valor > 0:
                        cursor.execute("""
                            INSERT INTO fluxoPagamentoNotas (
                                id_fluxo_nota, 
                                id_forma_pagamento, 
                                valor, 
                                data_pagamento
                            ) VALUES (?, ?, ?, ?)
                        """, (id_nota, id_forma, valor, hoje_str))
                        mensagens.append(f"Pago R$ {valor:.2f} via Forma {id_forma}.")
                        
                conn.commit()

            return {"sucesso": True, "mensagem": "Pagamentos registrados. " + " ".join(mensagens)}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"sucesso": False, "mensagem": f"Erro ao registrar pagamentos em lote: {e}"}

    # ─────────────────────────────────────────────────────────────────
    # 4. GERAÇÃO DE RELATÓRIOS EM MARKDOWN
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def gerar_relatorio_markdown_empresa(cls, id_empresa: int) -> str:
        """Retorna a string Markdown com o relatório completo de uma Empresa."""
        extrato_dict = cls.get_extrato_empresa(id_empresa)
        extrato = ExtratoFinanceiro(
            extrato_dict["id_dono"], extrato_dict["tipo_dono"], extrato_dict["nome_dono"]
        )
        res = extrato_dict["resumo"]
        extrato.total_vendas = res["total_vendas"]
        extrato.total_compras = res["total_compras"]
        extrato.total_devolucoes = res["total_devolucoes"]
        extrato.total_perdas = res["total_perdas"]
        extrato.lucro_bruto_estimado = res["lucro_bruto_estimado"]
        extrato.pagamentos_recebidos = res["pagamentos_recebidos"]
        extrato.pagamentos_efetuados = res["pagamentos_efetuados"]
        extrato.historico_pagamentos = extrato_dict.get("historico_pagamentos", [])
        extrato.historico_notas = extrato_dict.get("historico_notas", [])

        return RelatorioFinanceiroHelper.gerar_markdown_extrato(extrato)

    @classmethod
    def gerar_relatorio_markdown_global(cls) -> str:
        """Retorna a string Markdown do consolidado financeiro global."""
        resumo = cls.get_resumo_financeiro_global()
        return RelatorioFinanceiroHelper.gerar_markdown_global(resumo)
