from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.memory.productClassFactory import productClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida, UnidadeConjunto
from br.com.pdv.src.financeiro.Real import MoedaReal
from br.com.pdv.src.registro.registroGenerico import RegistroGenerico
from datetime import date


class InventoryFlowManager:
    """
    Classe estática central que gerencia TODO o fluxo de estoque do PDV.
    Faz parceria com productClassFactory para gerar produtos (moldes e com valores).
    Intermedia compras, vendas, devoluções, perdas e compensações.
    Ao vender, usa o CUSTO MAIS CARO entre os fornecedores.
    """

    # ========== CADASTROS ==========

    @staticmethod
    def criar_produto(nome: str, diasDuraveis: int = 365, unidadeMedida: int = 1,
                      receita: bool = False, varejo: float = 0, atacado: float = 0,
                      promocao: float = 0) -> int:
        """Cadastra um novo produto no banco de dados. Retorna o ID."""
        return DB.INSERT.PRODUTO.executar(nome, diasDuraveis, unidadeMedida,
                                           1 if receita else 0, varejo, atacado, promocao)

    @staticmethod
    def criar_pessoa(nome: str, sexo: int = 3) -> int:
        """Cadastra uma nova pessoa. Retorna o ID."""
        return DB.INSERT.PESSOA.executar(nome, sexo)

    @staticmethod
    def criar_empresa(nome: str) -> int:
        """Cadastra uma nova empresa. Retorna o ID."""
        return DB.INSERT.EMPRESA.executar(nome)

    @staticmethod
    def criar_entidade(id_pessoa: int = None, id_empresa: int = None,
                       fornecedor: bool = False, cliente: bool = False,
                       funcionario: bool = False) -> int:
        """Cadastra uma nova entidade. Retorna o ID."""
        return DB.INSERT.ENTIDADE.executar(
            id_pessoa, id_empresa,
            1 if fornecedor else 0,
            1 if cliente else 0,
            1 if funcionario else 0
        )

    @staticmethod
    def atribuir_cargo(id_entidade: int, id_cargo: int) -> int:
        """Atribui um cargo a uma entidade (pessoa vinculada a empresa)."""
        return DB.INSERT.ENTIDADE_CARGO.executar(id_entidade, id_cargo)

    @staticmethod
    def adicionar_registro(id_entidade: int, tipo_registro: int, valor: str) -> int:
        """Adiciona um registro (contato) a uma entidade."""
        return DB.INSERT.REGISTRO.executar(tipo_registro, id_entidade, valor)

    # ========== PRODUTO MOLDE (sem valores) ==========

    @staticmethod
    def obter_produto_molde(id_produto: int) -> dict:
        """Retorna o molde de um produto (sem valores de estoque/preço)."""
        resultado = DB.SELECT.PRODUTO_MOLDE.buscar_um(id_produto)
        if not resultado:
            return None
        return resultado

    @staticmethod
    def obter_todos_moldes() -> list:
        """Retorna todos os moldes de produtos."""
        return DB.SELECT.PRODUTO_MOLDES_TODOS.buscar()

    @staticmethod
    def fabricar_produto_molde(id_produto: int) -> Produto:
        """Fabrica uma instância de Produto a partir do molde do banco (sem valores)."""
        molde = InventoryFlowManager.obter_produto_molde(id_produto)
        if not molde:
            raise ValueError(f"Produto com ID {id_produto} não encontrado.")

        instrucoes = {
            "id": molde["id"],
            "nome": molde["nome"],
            "diasDuraveis": molde["diasDuraveis"],
            "unidadeMedida": molde["unidade_descricao"],
            "fatorConjunto": molde["fatorConjunto"]
        }

        return productClassFactory.testar_e_fabricar(instrucoes)

    # ========== PRODUTO COM VALORES ==========

    @staticmethod
    def obter_produto_completo(id_produto: int) -> dict:
        """Retorna o produto completo com unidade de medida."""
        return DB.SELECT.VW_PRODUTO_COMPLETO_POR_ID.buscar_um(id_produto)

    @staticmethod
    def obter_todos_produtos() -> list:
        """Retorna todos os produtos."""
        return DB.SELECT.VW_PRODUTO_COMPLETO_TODOS.buscar()

    # ========== NOTAS DE FLUXO ==========

    @staticmethod
    def registrar_compra(id_representante: int, produtos: list,
                         id_nota_origem: int = None,
                         data_vencimento: str = None) -> dict:
        """
        Registra uma compra completa.
        produtos: lista de dicts com {id_produto, quantidade, valorUnidario}
        Retorna: {id_nota, itens_registrados}
        """
        id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
            1, id_representante, id_nota_origem, data_vencimento
        )

        itens = []
        for p in produtos:
            id_item = DB.INSERT.FLUXO_ESTOQUE.executar(
                1, id_nota, p["id_produto"], p["quantidade"],
                p["valorUnidario"], 0, str(date.today())
            )
            itens.append({"id_item": id_item, **p})

        return {"id_nota": id_nota, "tipo": "COMPRA", "itens": itens}

    @staticmethod
    def registrar_venda(id_representante: int, produtos: list,
                        id_nota_origem: int = None,
                        data_vencimento: str = None) -> dict:
        """
        Registra uma venda completa.
        produtos: lista de dicts com {id_produto, quantidade, valorUnidario, lucroTotal}
        O sistema usa o custo mais caro entre os fornecedores para calcular o lucro.
        """
        id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
            2, id_representante, id_nota_origem, data_vencimento
        )

        itens = []
        for p in produtos:
            # Calcula lucro baseado no custo mais caro
            custo_mais_caro = InventoryFlowManager._obter_custo_mais_caro(p["id_produto"])
            lucro = (p["valorUnidario"] - custo_mais_caro) * p["quantidade"] if custo_mais_caro else p.get("lucroTotal", 0)

            id_item = DB.INSERT.FLUXO_ESTOQUE.executar(
                2, id_nota, p["id_produto"], p["quantidade"],
                p["valorUnidario"], lucro, str(date.today())
            )
            itens.append({"id_item": id_item, "lucroCalculado": lucro, **p})

        return {"id_nota": id_nota, "tipo": "VENDA", "itens": itens}

    @staticmethod
    def registrar_devolucao(id_representante: int, id_nota_venda: int,
                            produtos: list) -> dict:
        """
        Registra uma devolução citando a nota de venda de origem.
        produtos: lista de dicts com {id_produto, quantidade, valorUnidario}
        """
        id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
            3, id_representante, id_nota_venda, None
        )

        itens = []
        for p in produtos:
            id_item = DB.INSERT.FLUXO_ESTOQUE.executar(
                3, id_nota, p["id_produto"], p["quantidade"],
                p["valorUnidario"], 0, str(date.today())
            )
            itens.append({"id_item": id_item, **p})

        return {"id_nota": id_nota, "tipo": "DEVOLUÇÃO", "itens": itens}

    @staticmethod
    def registrar_perda(id_representante: int, id_nota_origem: int,
                        tipo_origem: str, produtos: list) -> dict:
        """
        Registra uma perda.
        tipo_origem: 'DEVOLUCAO' (perda após venda) ou 'ESTOQUE' (perda do estoque)
        """
        id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
            4, id_representante, id_nota_origem, None
        )

        itens = []
        for p in produtos:
            id_item = DB.INSERT.FLUXO_ESTOQUE.executar(
                4, id_nota, p["id_produto"], p["quantidade"],
                p["valorUnidario"], 0, str(date.today())
            )
            itens.append({"id_item": id_item, **p})

        return {"id_nota": id_nota, "tipo": "PERDA", "tipoOrigem": tipo_origem, "itens": itens}

    @staticmethod
    def registrar_compensacao(id_representante: int, id_nota_perda: int,
                              produtos: list) -> dict:
        """
        Registra uma compensação citando a nota de perda.
        """
        id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
            5, id_representante, id_nota_perda, None
        )

        itens = []
        for p in produtos:
            id_item = DB.INSERT.FLUXO_ESTOQUE.executar(
                5, id_nota, p["id_produto"], p["quantidade"],
                p["valorUnidario"], 0, str(date.today())
            )
            itens.append({"id_item": id_item, **p})

        return {"id_nota": id_nota, "tipo": "COMPENSAÇÃO", "itens": itens}

    # ========== PAGAMENTOS ==========

    @staticmethod
    def registrar_pagamento(id_fluxo_nota: int, id_forma_pagamento: int,
                            valor: float, data_pagamento: str = None) -> int:
        """Registra um pagamento para uma nota."""
        if data_pagamento is None:
            data_pagamento = str(date.today())
        return DB.INSERT.FLUXO_PAGAMENTO_NOTA.executar(
            id_fluxo_nota, id_forma_pagamento, valor, data_pagamento
        )

    # ========== CONSULTAS DE ESTOQUE ==========

    @staticmethod
    def consultar_estoque(id_produto: int = None) -> list:
        """Consulta o estoque atual. Se id_produto for None, retorna todos."""
        if id_produto:
            return DB.SELECT.ESTOQUE_POR_PRODUTO.buscar(id_produto)
        return DB.SELECT.ESTOQUE_TODOS.buscar()

    @staticmethod
    def consultar_fluxo_nota(id_nota: int) -> dict:
        """Retorna o fluxo completo de uma nota (itens + pagamentos)."""
        nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_nota)
        if not nota:
            return None

        itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
        pagamentos = DB.SELECT.VW_PAGAMENTOS_NOTA.buscar(id_nota)

        return {
            "nota": dict(nota),
            "itens": itens,
            "pagamentos": pagamentos
        }

    @staticmethod
    def consultar_resumo_vendas(id_produto: int = None) -> list:
        """Resumo de vendas por produto."""
        if id_produto:
            return DB.SELECT.VW_RESUMO_VENDAS_POR_PRODUTO.buscar(id_produto)
        return DB.SELECT.VW_RESUMO_VENDAS.buscar()

    # ========== CONSULTAS DE ENTIDADES ==========

    @staticmethod
    def consultar_fornecedores() -> list:
        return DB.SELECT.FORNECEDORES_TODOS.buscar()

    @staticmethod
    def consultar_clientes() -> list:
        return DB.SELECT.CLIENTES_TODOS.buscar()

    @staticmethod
    def consultar_entidade(id_entidade: int) -> dict:
        entidade = DB.SELECT.VW_ENTIDADE_COMPLETA_POR_ID.buscar_um(id_entidade)
        if not entidade:
            return None
        registros = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(id_entidade)
        cargos = DB.SELECT.CARGO_POR_ENTIDADE.buscar(id_entidade)
        return {
            "entidade": dict(entidade),
            "registros": registros,
            "cargos": cargos
        }

    # ========== SNAPSHOT SAZONAL ==========

    @staticmethod
    def registrar_snapshot_sazonal(id_fluxo_nota: int, dados_clima: dict = None,
                                    dados_rios: dict = None, qtd_eventos: int = 0) -> int:
        """
        Registra um snapshot sazonal vinculado a uma nota de fluxo.
        Salva apenas indicadores numéricos simples (não nomes de eventos).
        """
        temp_atual = None
        temp_min = None
        temp_max = None
        precip = None
        precip_prev = None
        indicador_clima = None
        nivel_rio = None
        nivel_rio_prev = None
        indicador_rio = None
        indicador_chuva = None

        # Processar dados de clima
        if dados_clima:
            atual = dados_clima.get("atual", {})
            previsao = dados_clima.get("previsao7dias", [])

            temp_atual = atual.get("temperatura")
            if previsao:
                temps_min = [d.get("temperaturaMinima", 0) for d in previsao if d.get("temperaturaMinima") is not None]
                temps_max = [d.get("temperaturaMaxima", 0) for d in previsao if d.get("temperaturaMaxima") is not None]
                precips = [d.get("precipitacao_mm", 0) for d in previsao if d.get("precipitacao_mm") is not None]

                temp_min = min(temps_min) if temps_min else None
                temp_max = max(temps_max) if temps_max else None
                precip = atual.get("precipitacao_mm", 0)
                precip_prev = sum(precips) if precips else None

            # Determinar indicadores
            if temp_atual is not None:
                if temp_atual < 22:
                    indicador_clima = "FRIO"
                elif temp_atual > 32:
                    indicador_clima = "QUENTE"
                else:
                    indicador_clima = "AMENO"

            if precip is not None:
                total_chuva = (precip or 0) + (precip_prev or 0)
                if total_chuva < 10:
                    indicador_chuva = "SECO"
                elif total_chuva < 50:
                    indicador_chuva = "MODERADO"
                else:
                    indicador_chuva = "CHUVOSO"

        # Processar dados de rios
        if dados_rios:
            rios = dados_rios.get("rios", {})
            for nome_rio, dados_rio in rios.items():
                if "erro" in dados_rio:
                    continue
                previsoes = dados_rio.get("previsao7dias", [])
                if previsoes:
                    vazoes = [p.get("vazao_m3s", 0) for p in previsoes if p.get("vazao_m3s") is not None]
                    if vazoes:
                        nivel_rio = vazoes[0]
                        nivel_rio_prev = sum(vazoes) / len(vazoes)

                        # Determinar indicador baseado na média de vazão
                        media_vazao = nivel_rio_prev
                        if media_vazao < 5000:
                            indicador_rio = "SECA"
                        elif media_vazao < 50000:
                            indicador_rio = "NORMAL"
                        else:
                            indicador_rio = "CHEIA"
                        break  # Usa o primeiro rio disponível

        return DB.INSERT.SNAPSHOT_SAZONAL.executar(
            id_fluxo_nota, str(date.today()),
            temp_atual, temp_min, temp_max,
            precip, precip_prev, indicador_clima,
            nivel_rio, nivel_rio_prev, indicador_rio,
            indicador_chuva, qtd_eventos
        )

    @staticmethod
    def consultar_analise_sazonal(id_produto: int = None) -> list:
        """Consulta a análise sazonal. Se id_produto for None, retorna todos."""
        if id_produto:
            return DB.SELECT.VW_ANALISE_SAZONAL_POR_PRODUTO.buscar(id_produto)
        return DB.SELECT.VW_ANALISE_SAZONAL.buscar()

    # ========== UTILITÁRIOS INTERNOS ==========

    @staticmethod
    def _obter_custo_mais_caro(id_produto: int) -> float:
        """
        Retorna o custo unitário mais caro entre todas as notas de compra
        para um determinado produto.
        """
        fluxos = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_produto)
        if not fluxos:
            # Fallback: busca diretamente
            try:
                from br.com.pdv.src.BDD.bancodb import BancoDB
                with BancoDB.obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT MAX(valorUnidario) as custo_max
                        FROM fluxoEstoque
                        WHERE id_produto = ? AND id_tipoNota = 1
                    """, (id_produto,))
                    row = cursor.fetchone()
                    if row and row["custo_max"]:
                        return row["custo_max"]
            except Exception:
                pass
            return 0

        custos = [f.get("valorUnidario", 0) for f in fluxos]
        return max(custos) if custos else 0

    # ========== CONSULTAS AUXILIARES ==========

    @staticmethod
    def listar_formas_pagamento() -> list:
        return DB.SELECT.FORMA_PAGAMENTO_TODOS.buscar()

    @staticmethod
    def listar_tipos_nota() -> list:
        return DB.SELECT.TIPO_NOTA_TODOS.buscar()

    @staticmethod
    def listar_cargos() -> list:
        return DB.SELECT.CARGO_TODOS.buscar()

    @staticmethod
    def listar_tipos_registro() -> list:
        return DB.SELECT.TIPO_REGISTRO_TODOS.buscar()

    @staticmethod
    def listar_sexos() -> list:
        return DB.SELECT.SEXO_TODOS.buscar()
