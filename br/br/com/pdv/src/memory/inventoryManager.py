from ast import main
import sqlite3
from datetime import date, datetime
from typing import Optional

from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaCompensacao import NotaCompensacao
from br.com.pdv.src.financeiro.notaPerda import NotaPerda
from br.com.pdv.src.financeiro.notaDevolucao import NotaDevolucao
from br.com.pdv.src.financeiro.notaCompra import NotaCompra
from br.com.pdv.src.financeiro.notaVenda import NotaVenda
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory


class InventoryManager:
    """
    Hub central do sistema. Recebe TODAS as interações da interface (UI).
    
    Dois índices internos:
      _mapaEstoque  → índice rastreável por lote, no formato:
                       '{seq_lote}.{id_nota}.{id_tipo}.{id_produto}.{variacao}'
                       Exemplo: '1.405.1.265.0'
      _mapaProdutos → índice agregado por produto (acesso rápido)
                       Chave: str(id_produto)
                       Valor: dict com totais + lista de lotes FIFO

    Regras de snapshot sazonal:
      - Salvo SOMENTE em insert_venda e insert_perda (tipos 2 e 4/5).
    """

    # ─────────────────────────────────────────────────────────────────
    # Estado da classe (em memória)
    # ─────────────────────────────────────────────────────────────────
    _mapaProdutos: dict = {}   # {id_prod_str: {totais..., "lotes": [...]}}
    _mapaEstoque: dict = {}    # {idx_lote: {dados do lote}}

    _NotasCompras: set = set()
    _NotasVendas: set = set()
    _NotasDevolucoes: set = set()
    _NotasPerdas: set = set()
    _NotasCompensacao: set = set()

    # contador global de lotes para gerar o índice sequencial
    _contadorLote: int = 0

    # ─────────────────────────────────────────────────────────────────
    # Inicialização / Carregamento
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def carregarTudo(cls) -> bool:
        """Carrega todas as notas do banco e reconstrói os índices em memória."""
        ok = (
            cls.carregarNotasCompras()
            and cls.carregarNotasVendas()
            and cls.carregarNotasDevolucoes()
            and cls.carregarNotasPerdas()
            and cls.carregarNotasCompensacao()
        )
        if ok:
            cls.mapearProdutos()
        return ok

    @classmethod
    def carregarNotasCompras(cls) -> bool:
        try:
            notasID = DB.SELECT.TODAS_NOTAS_COMPRA_ID.buscar()
            if not notasID:
                return True
            for nota in notasID:
                obj = PurchaseNoteClassFactory.fabricar(nota["id_fluxo_nota"])
                if obj:
                    cls._NotasCompras.add(obj)
            return True
        except Exception as e:
            print(f"[InventoryManager] Erro ao carregar notas de compra: {e}")
            return False

    @classmethod
    def carregarNotasVendas(cls) -> bool:
        try:
            from br.com.pdv.src.memory.saleNoteClassFactory import SaleNoteClassFactory
            notasID = DB.SELECT.TODAS_NOTAS_VENDA_ID.buscar()
            if not notasID:
                return True
            for nota in notasID:
                obj = SaleNoteClassFactory.fabricar(nota["id_fluxo_nota"])
                if obj:
                    cls._NotasVendas.add(obj)
            return True
        except Exception as e:
            print(f"[InventoryManager] Erro ao carregar notas de venda: {e}")
            return False

    @classmethod
    def carregarNotasDevolucoes(cls) -> bool:
        try:
            from br.com.pdv.src.memory.returnNoteClassFactory import ReturnNoteClassFactory
            notasID = DB.SELECT.TODAS_NOTAS_DEVOLUCAO_ID.buscar()
            if not notasID:
                return True
            for nota in notasID:
                obj = ReturnNoteClassFactory.fabricar(nota["id_fluxo_nota"])
                if obj:
                    cls._NotasDevolucoes.add(obj)
            return True
        except Exception as e:
            print(f"[InventoryManager] Erro ao carregar notas de devolução: {e}")
            return False

    @classmethod
    def carregarNotasPerdas(cls) -> bool:
        try:
            from br.com.pdv.src.memory.lossNoteClassFactory import LossNoteClassFactory
            notasID = DB.SELECT.TODAS_NOTAS_PERDA_ID.buscar()
            if not notasID:
                return True
            for nota in notasID:
                obj = LossNoteClassFactory.fabricar(nota["id_fluxo_nota"])
                if obj:
                    cls._NotasPerdas.add(obj)
            return True
        except Exception as e:
            print(f"[InventoryManager] Erro ao carregar notas de perda: {e}")
            return False

    @classmethod
    def carregarNotasCompensacao(cls) -> bool:
        try:
            from br.com.pdv.src.memory.compensationNoteClassFactory import CompensationNoteClassFactory
            notasID = DB.SELECT.TODAS_NOTAS_COMPENSACAO_ID.buscar()
            if not notasID:
                return True
            for nota in notasID:
                obj = CompensationNoteClassFactory.fabricar(nota["id_fluxo_nota"])
                if obj:
                    cls._NotasCompensacao.add(obj)
            return True
        except Exception as e:
            print(f"[InventoryManager] Erro ao carregar notas de compensação: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────
    # Mapeamento Contábil (Processamento Cronológico)
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _ordenarTodasAsNotas(cls) -> list:
        """Junta e ordena cronologicamente todas as notas carregadas."""
        todas = []
        todas.extend(cls._NotasCompras)
        todas.extend(cls._NotasVendas)
        todas.extend(cls._NotasDevolucoes)
        todas.extend(cls._NotasPerdas)
        todas.extend(cls._NotasCompensacao)
        try:
            todas.sort(key=lambda n: n.getDados().get("dataEmissao") or n.getDados().get("data", date.min))
        except Exception as e:
            print(f"[InventoryManager] Aviso ao ordenar notas: {e}")
        return todas

    @classmethod
    def mapearProdutos(cls) -> None:
        """
        Reconstrói _mapaProdutos e _mapaEstoque a partir do fluxo cronológico de notas.
        
        Índice de lote: '{seq}.{id_nota}.{id_tipo}.{id_produto}.{variacao}'
        onde id_tipo:  1=compra, 2=venda, 3=devolução, 4=perda(dev), 5=compensação(reposição)
        """
        notas_ordenadas = cls._ordenarTodasAsNotas()
        cls._mapaProdutos.clear()
        cls._mapaEstoque.clear()
        cls._contadorLote = 0

        def _prod_base():
            return {
                "quantidadeTotal": 0.0,
                "valorTotalEstoque": 0.0,
                "custoMedio": 0.0,
                "totalCompras": 0.0,
                "totalVendas": 0.0,
                "totalPerdas": 0.0,
                "totalDevolucoes": 0.0,
                "composicao": None,
                "lotes": []           # índices FIFO (somente entradas/lotes disponíveis)
            }

        def _garantir_produto(id_str):
            if id_str not in cls._mapaProdutos:
                cls._mapaProdutos[id_str] = _prod_base()
            return cls._mapaProdutos[id_str]

        def _registrar_lote(id_nota, id_tipo, id_produto_str, variacao, qtd, custo_unitario, data_entrada):
            """Cria uma entrada no _mapaEstoque e retorna seu índice."""
            cls._contadorLote += 1
            idx = f"{cls._contadorLote}.{id_nota}.{id_tipo}.{id_produto_str}.{variacao}"
            cls._mapaEstoque[idx] = {
                "id_nota": id_nota,
                "id_tipo": id_tipo,
                "id_produto": int(id_produto_str),
                "variacao": variacao,
                "qtd_inicial": qtd,
                "qtd_disponivel": qtd,
                "custo_unitario": custo_unitario,
                "data_entrada": data_entrada,
                "consumido": False
            }
            return idx

        def _consumir_fifo(id_produto_str, qtd_necessaria) -> list:
            """
            Consome qtd_necessaria de estoque do produto no modo FIFO.
            Retorna lista de (idx_lote, qtd_consumida) para rastreabilidade.
            Atualiza qtd_disponivel em cada lote consumido.
            """
            mapa = cls._mapaProdutos.get(id_produto_str, {})
            lotes_fifo = mapa.get("lotes", [])
            rastro = []
            restante = qtd_necessaria
            for idx_lote in lotes_fifo[:]:
                if restante <= 0:
                    break
                lote = cls._mapaEstoque.get(idx_lote)
                if not lote or lote["qtd_disponivel"] <= 0:
                    continue
                consumivel = min(lote["qtd_disponivel"], restante)
                lote["qtd_disponivel"] -= consumivel
                if lote["qtd_disponivel"] <= 0:
                    lote["consumido"] = True
                    lotes_fifo.remove(idx_lote)
                restante -= consumivel
                rastro.append((idx_lote, consumivel))
            return rastro

        for nota in notas_ordenadas:
            dados = nota.getDados()
            id_nota = dados.get("id")
            data_nota = dados.get("dataEmissao") or dados.get("data", date.today())
            produtos_dict = dados.get("produtos", {})

            # ── Identifica tipo ──────────────────────────────────────
            if isinstance(nota, NotaCompra):
                id_tipo = 1
            elif isinstance(nota, NotaVenda):
                id_tipo = 2
            elif isinstance(nota, NotaDevolucao):
                id_tipo = 3
            elif isinstance(nota, NotaPerda):
                id_tipo = 4
            elif isinstance(nota, NotaCompensacao):
                id_tipo = 5
            else:
                continue

            for chave_nota, prod in produtos_dict.items():
                id_produto_str = str(prod["id"])
                receita = prod.get("Receita")
                # Extrai variação do chave composto da nota (ex: '265.1.0' → '0')
                partes_chave = str(chave_nota).split(".")
                variacao = int(partes_chave[-1]) if partes_chave else 0

                # Quantidade movimentada
                if id_tipo == 2:  # Venda
                    qtd_mov = prod.get("vendas", prod.get("quantidadeEntrada", 0.0))
                else:
                    qtd_mov = prod.get("quantidadeEntrada", 0.0)

                mapa = _garantir_produto(id_produto_str)
                if receita:
                    mapa["composicao"] = receita

                # ── COMPRA / COMPENSAÇÃO (Entrada → gera lote FIFO) ──
                if id_tipo in (1, 5):
                    custo = prod.get("ValorTotal", 0.0)
                    custo_unit = prod.get("valor") or prod.get("valorUnitario", 0.0)
                    if custo_unit == 0 and qtd_mov > 0:
                        custo_unit = custo / qtd_mov

                    mapa["quantidadeTotal"] += qtd_mov
                    mapa["valorTotalEstoque"] += custo
                    mapa["totalCompras"] += qtd_mov
                    if mapa["quantidadeTotal"] > 0:
                        mapa["custoMedio"] = mapa["valorTotalEstoque"] / mapa["quantidadeTotal"]

                    # Cria lote rastreável
                    idx = _registrar_lote(id_nota, id_tipo, id_produto_str, variacao, qtd_mov, custo_unit, data_nota)
                    mapa["lotes"].append(idx)

                # ── VENDA (Saída FIFO, desmonta compostos) ───────────
                elif id_tipo == 2:
                    if receita:
                        for id_ingr, qtd_ingr in receita.items():
                            id_ingr_str = str(id_ingr)
                            mapa_ingr = _garantir_produto(id_ingr_str)
                            qtd_consumida = qtd_mov * qtd_ingr
                            _consumir_fifo(id_ingr_str, qtd_consumida)
                            mapa_ingr["quantidadeTotal"] -= qtd_consumida
                            mapa_ingr["valorTotalEstoque"] -= qtd_consumida * mapa_ingr["custoMedio"]
                            mapa_ingr["totalVendas"] += qtd_consumida
                    else:
                        _consumir_fifo(id_produto_str, qtd_mov)
                        mapa["quantidadeTotal"] -= qtd_mov
                        mapa["valorTotalEstoque"] -= qtd_mov * mapa["custoMedio"]
                        mapa["totalVendas"] += qtd_mov

                # ── PERDA (Saída, desmonta compostos) ─────────────────
                elif id_tipo == 4:
                    if receita:
                        for id_ingr, qtd_ingr in receita.items():
                            id_ingr_str = str(id_ingr)
                            mapa_ingr = _garantir_produto(id_ingr_str)
                            qtd_perdida = qtd_mov * qtd_ingr
                            _consumir_fifo(id_ingr_str, qtd_perdida)
                            mapa_ingr["quantidadeTotal"] -= qtd_perdida
                            mapa_ingr["valorTotalEstoque"] -= qtd_perdida * mapa_ingr["custoMedio"]
                            mapa_ingr["totalPerdas"] += qtd_perdida
                    else:
                        _consumir_fifo(id_produto_str, qtd_mov)
                        mapa["quantidadeTotal"] -= qtd_mov
                        mapa["valorTotalEstoque"] -= qtd_mov * mapa["custoMedio"]
                        mapa["totalPerdas"] += qtd_mov

                # ── DEVOLUÇÃO (Entrada, desmonta compostos) ───────────
                elif id_tipo == 3:
                    if receita:
                        for id_ingr, qtd_ingr in receita.items():
                            id_ingr_str = str(id_ingr)
                            mapa_ingr = _garantir_produto(id_ingr_str)
                            qtd_dev = qtd_mov * qtd_ingr
                            mapa_ingr["quantidadeTotal"] += qtd_dev
                            mapa_ingr["valorTotalEstoque"] += qtd_dev * mapa_ingr["custoMedio"]
                            mapa_ingr["totalDevolucoes"] += qtd_dev
                            # Devolução gera lote reutilizável
                            idx = _registrar_lote(id_nota, id_tipo, id_ingr_str, variacao, qtd_dev, mapa_ingr["custoMedio"], data_nota)
                            mapa_ingr["lotes"].append(idx)
                    else:
                        mapa["quantidadeTotal"] += qtd_mov
                        mapa["valorTotalEstoque"] += qtd_mov * mapa["custoMedio"]
                        mapa["totalDevolucoes"] += qtd_mov
                        idx = _registrar_lote(id_nota, id_tipo, id_produto_str, variacao, qtd_mov, mapa["custoMedio"], data_nota)
                        mapa["lotes"].append(idx)

    # ─────────────────────────────────────────────────────────────────
    # INSERT — Inserção de Novas Notas
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _obter_id_nota_origem_valido(cls, id_nota_origem: Optional[int], id_nota_atual: int, id_produto: int, id_tipo_nota: int) -> int:
        """
        Garante que APENAS a Nota de Compra (id_tipo_nota == 1) pode se autoreferenciar (id_notaOrigem == id_nota_atual).
        Para qualquer outro tipo de nota (Venda, Devolução, Perda, Compensação), o id_notaOrigem retornado
        será obrigatoriamente diferente de id_nota_atual.
        """
        # Nota de Compra (tipo 1): única que se autoreferencia
        if id_tipo_nota == 1:
            return id_nota_atual

        # Se id_nota_origem fornecido for válido e diferente de id_nota_atual:
        if id_nota_origem is not None:
            try:
                id_orig_int = int(id_nota_origem)
                if id_orig_int != int(id_nota_atual):
                    return id_orig_int
            except (ValueError, TypeError):
                pass

        # Tenta recuperar o ID de uma nota de compra de origem no mapa de lotes do produto
        id_str = str(id_produto)
        mapa = cls._mapaProdutos.get(id_str, {})
        lotes = mapa.get("lotes", [])
        if lotes:
            for idx in reversed(lotes):
                parts = str(idx).split(".")
                if len(parts) >= 2:
                    try:
                        nota_compra_id = int(parts[1])
                        if nota_compra_id != int(id_nota_atual):
                            return nota_compra_id
                    except ValueError:
                        pass

        # Tenta buscar qualquer Nota de Compra cadastrada na memória
        for n_compra in cls._NotasCompras:
            dados_c = n_compra.getDados()
            c_id = dados_c.get("id")
            if c_id and int(c_id) != int(id_nota_atual):
                return int(c_id)

        # Busca no banco de dados SQLite qualquer Nota de Compra existente
        try:
            from br.com.pdv.src.BDD.bancodb import BancoDB
            conn = BancoDB.obter_conexao()
            row = conn.execute("SELECT id FROM fluxosNotasEstoque WHERE id_tipoNota = 1 AND id != ? ORDER BY id DESC LIMIT 1", (id_nota_atual,)).fetchone()
            if row and row["id"]:
                return int(row["id"])
        except Exception:
            pass

        # Fallback de segurança: nunca permite auto-referência fora de compra
        return 1 if int(id_nota_atual) != 1 else 2

    @classmethod
    def _obter_custo_lote_compra(cls, id_compra_lote: Optional[int], id_produto: int) -> float:
        """Busca o valor de custo unitário registrado na nota de compra do lote."""
        if id_compra_lote:
            try:
                from br.com.pdv.src.BDD.bancodb import BancoDB
                conn = BancoDB.obter_conexao()
                row = conn.execute(
                    "SELECT valorUnidario FROM fluxoEstoque WHERE id_fluxo_nota = ? AND id_produto = ? AND id_tipoNota = 1 LIMIT 1",
                    (id_compra_lote, id_produto)
                ).fetchone()
                if row and row["valorUnidario"] is not None:
                    return float(row["valorUnidario"])
            except Exception:
                pass
        return cls._get_custo_medio(str(id_produto))

    @classmethod
    def insert_compra(cls, dados: dict) -> Optional[NotaCompra]:
        """
        Registra uma nova Nota de Compra no banco e atualiza os índices em memória.

        Formato esperado de 'dados':
        {
            "id_fornecedor": int,
            "data": "YYYY-MM-DD" (opcional, default=hoje),
            "data_vencimento": "YYYY-MM-DD" (opcional),
            "produtos": [
                {"id": int, "quantidade": float, "valorUnidario": float},
                ...
            ]
        }
        Retorna a instância NotaCompra em caso de sucesso, None em caso de falha.
        """
        try:
            from br.com.pdv.src.memory.supplierClassFactory import SupplierClassFactory
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory

            id_forn = dados.get("id_fornecedor")
            if not id_forn:
                raise ValueError("'id_fornecedor' é obrigatório.")

            lista_produtos = dados.get("produtos")
            if not lista_produtos:
                raise ValueError("'produtos' é obrigatório e não pode estar vazio.")

            fornecedor = SupplierClassFactory.fabricar(id_forn)
            if not fornecedor:
                raise ValueError(f"Fornecedor ID {id_forn} não encontrado.")

            data_emissao = cls._parse_data(dados.get("data")) or date.today()
            data_venc = cls._parse_data(dados.get("data_vencimento"))

            # Salva o cabeçalho no banco (tipo 1 = COMPRA)
            id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(1, id_forn, str(data_venc or data_emissao))
            if not id_nota or id_nota <= 0:
                raise ValueError("Falha ao inserir o cabeçalho da nota de compra no banco.")

            notaCompra = NotaCompra(id=id_nota, fornecedor=fornecedor, dataEmissao=data_emissao, dataVencimento=data_venc)

            for item in lista_produtos:
                id_prod = item.get("id")
                qtd = item.get("quantidade")
                val_unit = item.get("valorUnidario")
                if not all([id_prod, qtd is not None, val_unit is not None]):
                    raise ValueError(f"Item inválido em 'produtos': {item}")

                produto = ProductClassFactory.testar_e_fabricar(id_prod)
                if not produto:
                    raise ValueError(f"Produto ID {id_prod} não encontrado.")

                produto.insertPropertValue(valorUnidario=val_unit, quantidade=qtd)
                notaCompra.adicionarProduto(produto)

                # Persiste no fluxo de estoque (id_notaOrigem = auto-referência: compra de si mesma)
                dados_prod = produto.getDados(f=True)
                DB.INSERT.FLUXO_ESTOQUE.executar(
                    id_nota,   # id_notaOrigem = própria nota de compra (sem NULL)
                    id_nota, 1, id_prod,
                    dados_prod.get("quantidadeEntrada", qtd),
                    dados_prod.get("valorUnidario", val_unit),
                    dados_prod.get("valorTotalLucro", 0),
                    str(data_emissao)
                )

            notaCompra.salvar()
            cls._NotasCompras.add(notaCompra)

            # Atualiza os índices em memória sem recarregar tudo
            cls._atualizar_mapa_com_nota(notaCompra, id_tipo=1)

            print(f"[InventoryManager] Nota de Compra ID {id_nota} registrada com sucesso.")
            return notaCompra

        except Exception as e:
            print(f"[InventoryManager] Erro ao inserir nota de compra: {e}")
            return None

    @classmethod
    def insert_venda(cls, dados: dict) -> Optional[NotaVenda]:
        """
        Registra uma nova Nota de Venda com rastreabilidade FIFO automática.

        Formato esperado de 'dados':
        {
            "id_cliente": int,
            "data": "YYYY-MM-DD" (opcional),
            "produtos": [
                {"id": int, "quantidade": float, "valorVenda": float},
                ...
            ]
        }
        Retorna a instância NotaVenda, ou None em caso de falha.
        Salva snapshot sazonal automaticamente após inserção.
        """
        try:
            from br.com.pdv.src.memory.clientClassFactory import ClientClassFactory
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
            from br.com.pdv.src.apis.gerenciadorSazonal import GerenciadorSazonal

            id_cli = dados.get("id_cliente")
            if not id_cli:
                raise ValueError("'id_cliente' é obrigatório.")

            lista_produtos = dados.get("produtos")
            if not lista_produtos:
                raise ValueError("'produtos' é obrigatório.")

            cliente = ClientClassFactory.fabricar(id_cli)
            if not cliente:
                raise ValueError(f"Cliente ID {id_cli} não encontrado.")

            data_emissao = cls._parse_data(dados.get("data")) or date.today()
            data_venc = cls._parse_data(dados.get("data_vencimento"))

            # Salva cabeçalho no banco (tipo 2 = VENDA)
            id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(2, id_cli, str(data_venc or data_emissao))
            if not id_nota or id_nota <= 0:
                raise ValueError("Falha ao inserir o cabeçalho da nota de venda no banco.")

            notaVenda = NotaVenda(id=id_nota, clienteFornecedor=cliente, dataEmissao=data_emissao, dataVencimento=data_venc)

            for item in lista_produtos:
                id_prod = item.get("id")
                qtd = item.get("quantidade")
                val_venda = item.get("valorVenda")
                if not all([id_prod, qtd is not None, val_venda is not None]):
                    raise ValueError(f"Item inválido em 'produtos': {item}")

                produto = ProductClassFactory.testar_e_fabricar(id_prod)
                if not produto:
                    raise ValueError(f"Produto ID {id_prod} não encontrado.")

                id_prod_str = str(id_prod)
                receita = produto.getDados().get("Receita")

                if receita and isinstance(receita, dict):
                    # ── PRODUTO COMPOSTO ─────────────────────────────────
                    # Consome FIFO de cada ingrediente e calcula o CUSTO REAL PONDERADO dos lotes retirados
                    itens_rastro: list = []
                    custo_total_real_comp = 0.0

                    for id_ingr, qtd_por_un in receita.items():
                        qtd_por_un = float(qtd_por_un)
                        prod_ingr = ProductClassFactory.testar_e_fabricar(int(id_ingr))
                        if prod_ingr:
                            qtd_por_un = prod_ingr.normalizarQuantidade(qtd_por_un)

                        qtd_ingr_total = qtd * qtd_por_un
                        rastro_ingr = cls._consumir_fifo_interno(str(id_ingr), qtd_ingr_total)

                        custo_real_ingr = 0.0
                        if rastro_ingr:
                            for idx_lote, qtd_c in rastro_ingr:
                                lote = cls._mapaEstoque.get(idx_lote)
                                c_unit = lote["custo_unitario"] if lote else cls._get_custo_medio(str(id_ingr))
                                custo_real_ingr += c_unit * qtd_c
                        else:
                            custo_real_ingr = cls._get_custo_medio(str(id_ingr)) * qtd_ingr_total

                        custo_total_real_comp += custo_real_ingr
                        itens_rastro.append((id_ingr, rastro_ingr, qtd_ingr_total, custo_real_ingr))

                    # Custo unitário real do produto composto (Custo Real Total / Quantidade Vendida)
                    custo_unit_real_comp = (custo_total_real_comp / qtd) if qtd > 0 else 0.0

                    # Executa a venda no produto composto com o CUSTO REAL dos lotes
                    produto.insertPropertValue(valorUnidario=custo_unit_real_comp, quantidade=qtd)
                    produto.vender(quantidadeVendas=qtd, valorVenda=val_venda)

                    dados_prod = produto.getDados(f=True)
                    val_total_lucro = dados_prod.get("valorTotalLucro", 0) or 0
                    venda_total_comp = val_venda * qtd

                    # Persiste no banco cada ingrediente/lote com seu lucro real exato
                    mapa_origem: dict = {}
                    for id_ingr, rastro_ingr, qtd_ingr_total, custo_real_ingr in itens_rastro:
                        if rastro_ingr:
                            mapa_origem[id_ingr] = int(rastro_ingr[0][0].split(".")[1])
                            total_qtd_rastro = sum(q for _, q in rastro_ingr)
                            for idx_lote, qtd_consumida in rastro_ingr:
                                id_nota_orig_lote = int(idx_lote.split(".")[1])
                                lote = cls._mapaEstoque.get(idx_lote)
                                c_unit_lote = lote["custo_unitario"] if lote else cls._get_custo_medio(str(id_ingr))
                                custo_lote = c_unit_lote * qtd_consumida

                                # Distribuição 100% genérica proporcional à quantidade física consumida de cada lote
                                parcela_venda_lote = (qtd_consumida / total_qtd_rastro) * venda_total_comp if total_qtd_rastro > 0 else 0
                                lucro_frac = round(parcela_venda_lote - custo_lote, 4)
                                val_venda_banco = round(parcela_venda_lote / qtd_consumida, 4) if qtd_consumida > 0 else 0

                                DB.INSERT.FLUXO_ESTOQUE.executar(
                                    id_nota_orig_lote,      # id_notaOrigem = nota de compra do lote real
                                    id_nota, 2, int(id_ingr),
                                    qtd_consumida, val_venda_banco, lucro_frac,
                                    str(data_emissao)
                                )
                        else:
                            # Sem lote rastreável
                            id_orig_valido = cls._obter_id_nota_origem_valido(None, id_nota, int(id_ingr), 2)
                            lucro_frac = round((1.0 / len(receita)) * val_total_lucro, 4) if receita else 0
                            DB.INSERT.FLUXO_ESTOQUE.executar(
                                id_orig_valido,
                                id_nota, 2, int(id_ingr),
                                qtd_ingr_total, val_venda, lucro_frac,
                                str(data_emissao)
                            )

                    notaVenda.adicionarProduto(produto, id_nota_origem=mapa_origem or None)

                else:
                    # ── PRODUTO SIMPLES ──────────────────────────────────
                    # Consome FIFO e calcula o CUSTO REAL dos lotes retirados
                    rastro = cls._consumir_fifo_interno(id_prod_str, qtd)
                    id_nota_origem_mem = int(rastro[0][0].split(".")[1]) if rastro else None

                    custo_total_real = 0.0
                    if rastro:
                        for idx_lote, qtd_c in rastro:
                            lote = cls._mapaEstoque.get(idx_lote)
                            c_unit = lote["custo_unitario"] if lote else cls._get_custo_medio(id_prod_str)
                            custo_total_real += c_unit * qtd_c
                    else:
                        custo_total_real = cls._get_custo_medio(id_prod_str) * qtd

                    custo_unit_real = (custo_total_real / qtd) if qtd > 0 else 0.0

                    produto.insertPropertValue(valorUnidario=custo_unit_real, quantidade=qtd)
                    produto.vender(quantidadeVendas=qtd, valorVenda=val_venda)
                    notaVenda.adicionarProduto(produto, id_nota_origem=id_nota_origem_mem)

                    venda_total = val_venda * qtd

                    if rastro:
                        for idx_lote, qtd_consumida in rastro:
                            id_nota_orig_lote = int(idx_lote.split(".")[1])
                            # Se o lote é proveniente de reposição (tipo 6), o custo financeiro de aquisição é 0.0 -> Lucro é 100%!
                            is_reposicao = lote and (lote.get("id_tipo") == 6 or lote.get("e_reposicao"))
                            c_unit_lote = 0.0 if is_reposicao else (lote["custo_unitario"] if lote else cls._get_custo_medio(id_prod_str))

                            custo_lote = c_unit_lote * qtd_consumida
                            parcela_venda_lote = val_venda * qtd_consumida
                            lucro_frac = round(parcela_venda_lote - custo_lote, 4)

                            DB.INSERT.FLUXO_ESTOQUE.executar(
                                id_nota_orig_lote,          # id_notaOrigem = nota de compra do lote real
                                id_nota, 2, id_prod,
                                qtd_consumida, val_venda, lucro_frac,
                                str(data_emissao)
                            )
                    else:
                        # Sem lote rastreável: garante origem sem auto-referenciar nota de venda
                        id_orig_valido = cls._obter_id_nota_origem_valido(None, id_nota, id_prod, 2)
                        lucro_real = round(venda_total - custo_total_real, 4)
                        DB.INSERT.FLUXO_ESTOQUE.executar(
                            id_orig_valido,
                            id_nota, 2, id_prod,
                            qtd, val_venda, lucro_real, str(data_emissao)
                        )

            notaVenda.salvar()
            cls._NotasVendas.add(notaVenda)
            cls._atualizar_mapa_com_nota(notaVenda, id_tipo=2)

            # Snapshot sazonal automático
            try:
                GerenciadorSazonal.salvar_snapshot_sazonal(id_nota)
            except Exception as e_saz:
                print(f"[InventoryManager] Aviso: snapshot sazonal falhou: {e_saz}")

            print(f"[InventoryManager] Nota de Venda ID {id_nota} registrada com sucesso.")
            return notaVenda

        except Exception as e:
            print(f"[InventoryManager] Erro ao inserir nota de venda: {e}")
            return None

    @classmethod
    def insert_perda(cls, dados: dict) -> Optional[NotaPerda]:
        """
        Registra uma nova Nota de Perda.

        Suporta 3 cenários automáticos com base no 'id_nota_origem':
        1. id_nota_origem = NOTA DE VENDA (Tipo 2):
           Gera em cadeia: Nota de Devolução (Tipo 3) + Nota de Perda Pós-Devolução (Tipo 4).
        2. id_nota_origem = NOTA DE COMPRA (Tipo 1):
           Gera Nota de Perda de Estoque (Tipo 5) consumindo especificamente o lote daquela compra.
        3. id_nota_origem = NOTA DE DEVOLUÇÃO (Tipo 3):
           Gera Nota de Perda Pós-Devolução (Tipo 4) citando a devolução original.
        4. Sem id_nota_origem (None / omissão):
           Gera Nota de Perda Geral de Estoque (Tipo 5) consumindo os lotes ativos via FIFO.

        Formato esperado de 'dados':
        {
            "id_nota_origem": int (opcional — ID da Nota de Venda, Compra ou Devolução),
            "origem": "ESTOQUE" | "DEVOLUCAO" (opcional),
            "id_cliente": int (opcional),
            "data": "YYYY-MM-DD" (opcional),
            "produtos": [
                {"id": int, "quantidade": float, "valorUnidario": float (opcional)},
                ...
            ]
        }
        Salva snapshot sazonal automaticamente após inserção.
        """
        try:
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
            from br.com.pdv.src.apis.gerenciadorSazonal import GerenciadorSazonal

            id_nota_orig = dados.get("id_nota_origem")
            lista_produtos = dados.get("produtos")
            if not lista_produtos:
                raise ValueError("'produtos' é obrigatório.")

            # ── 1. Verifica no banco o tipo da nota apontada em id_nota_origem ──
            tipo_nota_orig = None
            if id_nota_orig:
                try:
                    from br.com.pdv.src.BDD.bancodb import BancoDB
                    conn_orig = BancoDB.obter_conexao().execute(
                        "SELECT id_tipoNota, id_representante FROM fluxosNotasEstoque WHERE id = ?",
                        (int(id_nota_orig),)
                    ).fetchone()
                    if conn_orig:
                        tipo_nota_orig = conn_orig["id_tipoNota"]
                except Exception:
                    pass

            # ── 2. Se id_nota_origem apontar para NOTA DE VENDA (Tipo 2): ──
            # Gera primeiro a Nota de Devolução e depois vincula a Nota de Perda à essa Devolução!
            if tipo_nota_orig == 2:
                payload_dev = {
                    "id_cliente": dados.get("id_cliente") or conn_orig["id_representante"] or 1,
                    "id_nota_venda_origem": int(id_nota_orig),
                    "data": dados.get("data"),
                    "produtos": lista_produtos
                }
                nota_dev = cls.insert_devolucao(payload_dev)
                id_nota_dev_gerada = nota_dev.getDados()["id"] if nota_dev else id_nota_orig

                dados_perda_dev = dict(dados)
                dados_perda_dev["origem"] = "DEVOLUCAO"
                dados_perda_dev["id_nota_origem"] = id_nota_dev_gerada
                return cls.insert_perda(dados_perda_dev)

            # ── 3. Define origem real (DEVOLUCAO se tipo 3, senão ESTOQUE) ──
            origem = "DEVOLUCAO" if (tipo_nota_orig == 3 or dados.get("origem", "").upper() == "DEVOLUCAO") else "ESTOQUE"
            data_emissao = cls._parse_data(dados.get("data")) or date.today()
            id_tipo_nota = 4  # 4 = PERDA no banco de dados (tiposNotas)
            id_rep = dados.get("id_representante") or 1
            id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
                id_tipo_nota, id_rep, str(data_emissao)
            )
            if not id_nota or id_nota <= 0:
                raise ValueError("Falha ao inserir o cabeçalho da nota de perda no banco.")

            from br.com.pdv.src.financeiro.notaPerda import NotaPerda
            notaPerda = NotaPerda(id=id_nota, id_nota_origem=id_nota_orig,
                                  tipo_origem=origem, dataEmissao=data_emissao)

            for item in lista_produtos:
                id_prod = item.get("id")
                qtd = item.get("quantidade")
                if not id_prod or qtd is None or qtd <= 0:
                    raise ValueError(f"Item inválido em 'produtos': {item}")

                produto = ProductClassFactory.testar_e_fabricar(id_prod)
                if not produto:
                    raise ValueError(f"Produto ID {id_prod} não encontrado.")

                receita = produto.getDados().get("Receita")

                if origem == "DEVOLUCAO":
                    # Perda Pós-Devolução: id_notaOrigem referencia a Nota de Devolução de Origem (ou id_nota_orig)
                    id_orig_p = id_nota_orig or cls._obter_id_nota_origem_valido(id_nota_orig, id_nota, id_prod, 4)
                    custo_calculado = 0.0
                    if receita and isinstance(receita, dict):
                        for id_ingr, qtd_por_un in receita.items():
                            c_ingr = cls._get_custo_medio(str(id_ingr))
                            prod_ingr = ProductClassFactory.testar_e_fabricar(int(id_ingr))
                            if prod_ingr:
                                qtd_por_un = prod_ingr.normalizarQuantidade(float(qtd_por_un))
                            custo_calculado += float(qtd_por_un) * c_ingr

                    val_unit = item.get("valorUnidario") or custo_calculado or cls._get_custo_medio(str(id_prod))
                    valor_abatido_lucro = round(val_unit * qtd, 4)
                    produto.insertPropertValue(valorUnidario=val_unit, quantidade=qtd)
                    notaPerda.adicionarProduto(produto)

                    DB.INSERT.FLUXO_ESTOQUE.executar(
                        id_orig_p,  # id_notaOrigem = ID da Nota de Devolução original
                        id_nota, 4, id_prod, qtd, val_unit, valor_abatido_lucro, str(data_emissao)
                    )
                else:
                    # Perda em Estoque: Consome lotes FIFO ativos em estoque e grava fatia por lote
                    if receita and isinstance(receita, dict):
                        for id_ingr, qtd_por_un in receita.items():
                            qtd_por_un = float(qtd_por_un)
                            prod_ingr = ProductClassFactory.testar_e_fabricar(int(id_ingr))
                            if prod_ingr:
                                qtd_por_un = prod_ingr.normalizarQuantidade(qtd_por_un)

                            qtd_perd_ingr = qtd * qtd_por_un
                            rastro_ingr = cls._consumir_fifo_interno(str(id_ingr), qtd_perd_ingr)

                            if rastro_ingr:
                                for idx_lote, qtd_lote in rastro_ingr:
                                    lote_data = cls._mapaEstoque.get(idx_lote, {})
                                    c_lote = lote_data.get("custo_unitario") or cls._get_custo_medio(str(id_ingr))
                                    id_compra_lote = lote_data.get("id_nota") or cls._obter_id_nota_origem_valido(None, id_nota, int(id_ingr), 5)
                                    valor_abatido_lucro = round(c_lote * qtd_lote, 4)

                                    ingr = ProductClassFactory.testar_e_fabricar(id_ingr)
                                    ingr.insertPropertValue(valorUnidario=c_lote, quantidade=qtd_lote)
                                    notaPerda.adicionarProduto(ingr)

                                    DB.INSERT.FLUXO_ESTOQUE.executar(
                                        id_compra_lote,  # id_notaOrigem = Nota de Compra do Lote Perdiddo
                                        id_nota, 4, int(id_ingr), qtd_lote, c_lote, valor_abatido_lucro, str(data_emissao)
                                    )
                            else:
                                c_fallback = cls._get_custo_medio(str(id_ingr))
                                id_orig_f = cls._obter_id_nota_origem_valido(None, id_nota, int(id_ingr), 5)
                                valor_abatido_lucro = round(c_fallback * qtd_perd_ingr, 4)
                                ingr = ProductClassFactory.testar_e_fabricar(id_ingr)
                                ingr.insertPropertValue(valorUnidario=c_fallback, quantidade=qtd_perd_ingr)
                                notaPerda.adicionarProduto(ingr)
                                DB.INSERT.FLUXO_ESTOQUE.executar(
                                    id_orig_f, id_nota, 4, int(id_ingr), qtd_perd_ingr, c_fallback, valor_abatido_lucro, str(data_emissao)
                                )
                    else:
                        rastro_prod = cls._consumir_fifo_interno(str(id_prod), qtd)
                        if rastro_prod:
                            for idx_lote, qtd_lote in rastro_prod:
                                lote_data = cls._mapaEstoque.get(idx_lote, {})
                                c_lote = lote_data.get("custo_unitario") or cls._get_custo_medio(str(id_prod))
                                id_compra_lote = lote_data.get("id_nota") or cls._obter_id_nota_origem_valido(None, id_nota, id_prod, 5)
                                valor_abatido_lucro = round(c_lote * qtd_lote, 4)

                                produto.insertPropertValue(valorUnidario=c_lote, quantidade=qtd_lote)
                                notaPerda.adicionarProduto(produto)

                                DB.INSERT.FLUXO_ESTOQUE.executar(
                                    id_compra_lote,  # id_notaOrigem = Nota de Compra do Lote Perdiddo
                                    id_nota, 4, id_prod, qtd_lote, c_lote, valor_abatido_lucro, str(data_emissao)
                                )
                        else:
                            c_fallback = cls._get_custo_medio(str(id_prod))
                            id_orig_f = cls._obter_id_nota_origem_valido(None, id_nota, id_prod, 5)
                            valor_abatido_lucro = round(c_fallback * qtd, 4)
                            produto.insertPropertValue(valorUnidario=c_fallback, quantidade=qtd)
                            notaPerda.adicionarProduto(produto)
                            DB.INSERT.FLUXO_ESTOQUE.executar(
                                id_orig_f, id_nota, 4, id_prod, qtd, c_fallback, valor_abatido_lucro, str(data_emissao)
                            )

            notaPerda.salvar()
            cls._NotasPerdas.add(notaPerda)
            cls._atualizar_mapa_com_nota(notaPerda, id_tipo=4)

            try:
                GerenciadorSazonal.salvar_snapshot_sazonal(id_nota)
            except Exception as e_saz:
                print(f"[InventoryManager] Aviso: snapshot sazonal falhou: {e_saz}")

            print(f"[InventoryManager] Nota de Perda ID {id_nota} registrada com sucesso.")
            return notaPerda

        except Exception as e:
            print(f"[InventoryManager] Erro ao inserir nota de perda: {e}")
            return None

    @classmethod
    def insert_devolucao(cls, dados: dict) -> Optional[NotaDevolucao]:
        """
        Registra uma Nota de Devolução. Produtos compostos são desmontados.
        Resgata o custo real dos lotes de compra originais a partir da Nota de Venda.

        Formato esperado de 'dados':
        {
            "id_cliente": int,
            "id_nota_venda_origem": int (OBRIGATÓRIO — ID da Nota de Venda devolvida),
            "data": "YYYY-MM-DD" (opcional),
            "produtos": [
                {"id": int, "quantidade": float, "valorUnidario": float (opcional — resgatado da venda se omitido)},
                ...
            ]
        }
        """
        try:
            from br.com.pdv.src.memory.clientClassFactory import ClientClassFactory
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory

            id_cli = dados.get("id_cliente")
            id_nota_venda = dados.get("id_nota_venda_origem")
            lista_produtos = dados.get("produtos")
            if not id_cli or not id_nota_venda or not lista_produtos:
                raise ValueError("'id_cliente', 'id_nota_venda_origem' e 'produtos' são obrigatórios.")

            cliente = ClientClassFactory.fabricar(id_cli)
            if not cliente:
                raise ValueError(f"Cliente ID {id_cli} não encontrado.")

            data_emissao = cls._parse_data(dados.get("data")) or date.today()
            data_venc = cls._parse_data(dados.get("data_vencimento"))

            id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
                3, id_cli, str(data_venc or data_emissao)
            )
            if not id_nota or id_nota <= 0:
                raise ValueError("Falha ao inserir o cabeçalho da nota de devolução no banco.")

            from br.com.pdv.src.financeiro.notaDevolucao import NotaDevolucao
            notaDev = NotaDevolucao(id=id_nota, clienteFornecedor=cliente,
                                    id_nota_venda_origem=id_nota_venda,
                                    dataEmissao=data_emissao, dataVencimento=data_venc)

            for item in lista_produtos:
                id_prod = item.get("id")
                qtd = item.get("quantidade")
                if not id_prod or qtd is None or qtd <= 0:
                    raise ValueError(f"Item inválido em 'produtos': {item}")

                produto = ProductClassFactory.testar_e_fabricar(id_prod)
                if not produto:
                    raise ValueError(f"Produto ID {id_prod} não encontrado.")

                # Busca valor de venda original praticado na nota de venda se não informado no item
                val_unit_fornecido = item.get("valorUnidario")

                receita = produto.getDados().get("Receita")
                if receita and isinstance(receita, dict):
                    # Desmonta: devolve os ingredientes rastreando os lotes de compra originais da nota de venda
                    rows_venda = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota_venda) or []
                    for id_ingr, qtd_por_un in receita.items():
                        qtd_por_un = float(qtd_por_un)
                        prod_ingr = ProductClassFactory.testar_e_fabricar(int(id_ingr))
                        if prod_ingr:
                            qtd_por_un = prod_ingr.normalizarQuantidade(qtd_por_un)

                        qtd_dev_ingr = qtd * qtd_por_un
                        rows_ingr = [r for r in rows_venda if r["id_produto"] == int(id_ingr)]

                        qtd_restante_dev = qtd_dev_ingr

                        if rows_ingr:
                            for r_v in rows_ingr:
                                if qtd_restante_dev <= 0:
                                    break
                                qtd_venda_lote = r_v.get("quantidade", 0.0)
                                id_compra_lote = r_v.get("id_notaOrigem")

                                # Custo unitário de compra real do lote e proporção de lucro devolvido
                                custo_lote = cls._obter_custo_lote_compra(id_compra_lote, int(id_ingr))
                                lucro_venda_lote = r_v.get("lucroTotal", 0.0)

                                qtd_reverter = min(qtd_restante_dev, qtd_venda_lote)
                                if qtd_reverter <= 0:
                                    continue

                                qtd_restante_dev -= qtd_reverter
                                lucro_devolvido = round((lucro_venda_lote / qtd_venda_lote) * qtd_reverter, 4) if qtd_venda_lote > 0 else 0.0

                                ingr = ProductClassFactory.testar_e_fabricar(id_ingr)
                                ingr.insertPropertValue(valorUnidario=custo_lote, quantidade=qtd_reverter)
                                notaDev.adicionarProduto(ingr)

                                DB.INSERT.FLUXO_ESTOQUE.executar(
                                    id_nota_venda,  # id_notaOrigem = NOTA DE VENDA ORIGINAL
                                    id_nota, 3, id_ingr, qtd_reverter, custo_lote, lucro_devolvido, str(data_emissao)
                                )

                        if qtd_restante_dev > 0:
                            c_fallback = cls._get_custo_medio(str(id_ingr))
                            ingr = ProductClassFactory.testar_e_fabricar(id_ingr)
                            ingr.insertPropertValue(valorUnidario=c_fallback, quantidade=qtd_restante_dev)
                            notaDev.adicionarProduto(ingr)
                            DB.INSERT.FLUXO_ESTOQUE.executar(
                                id_nota_venda, id_nota, 3, id_ingr, qtd_restante_dev, c_fallback, 0, str(data_emissao)
                            )
                else:
                    rows_venda = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota_venda) or []
                    rows_prod = [r for r in rows_venda if r["id_produto"] == int(id_prod)]

                    qtd_restante_dev = qtd

                    if rows_prod:
                        for r_v in rows_prod:
                            if qtd_restante_dev <= 0:
                                break
                            qtd_venda_lote = r_v.get("quantidade", 0.0)
                            id_compra_lote = r_v.get("id_notaOrigem")

                            # Custo unitário de compra real do lote e proporção de lucro devolvido
                            custo_lote = cls._obter_custo_lote_compra(id_compra_lote, int(id_prod))
                            lucro_venda_lote = r_v.get("lucroTotal", 0.0)

                            qtd_reverter = min(qtd_restante_dev, qtd_venda_lote)
                            if qtd_reverter <= 0:
                                continue

                            qtd_restante_dev -= qtd_reverter
                            lucro_devolvido = round((lucro_venda_lote / qtd_venda_lote) * qtd_reverter, 4) if qtd_venda_lote > 0 else 0.0

                            produto.insertPropertValue(valorUnidario=custo_lote, quantidade=qtd_reverter)
                            notaDev.adicionarProduto(produto)

                            DB.INSERT.FLUXO_ESTOQUE.executar(
                                id_nota_venda,  # id_notaOrigem = NOTA DE VENDA ORIGINAL
                                id_nota, 3, id_prod, qtd_reverter, custo_lote, lucro_devolvido, str(data_emissao)
                            )

                    if qtd_restante_dev > 0:
                        val_unit = cls._get_custo_medio(str(id_prod))
                        produto.insertPropertValue(valorUnidario=val_unit, quantidade=qtd_restante_dev)
                        notaDev.adicionarProduto(produto)
                        DB.INSERT.FLUXO_ESTOQUE.executar(
                            id_nota_venda, id_nota, 3, id_prod, qtd_restante_dev, val_unit, 0, str(data_emissao)
                        )

            notaDev.salvar()
            cls._NotasDevolucoes.add(notaDev)
            cls._atualizar_mapa_com_nota(notaDev, id_tipo=3)

            print(f"[InventoryManager] Nota de Devolução ID {id_nota} registrada com sucesso.")
            return notaDev

        except Exception as e:
            print(f"[InventoryManager] Erro ao inserir nota de devolução: {e}")
            return None

    @classmethod
    def insert_compensacao(cls, dados: dict) -> Optional[NotaCompensacao]:
        """
        Registra uma Nota de Compensação (reposição de estoque após perda).

        Formato esperado de 'dados':
        {
            "id_nota_perda_origem": int,
            "data": "YYYY-MM-DD" (opcional),
            "produtos": [
                {"id": int, "quantidade": float, "valorUnidario": float},
                ...
            ]
        }
        """
        try:
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory

            id_rep = dados.get("id_representante") or 1
            id_perda_orig = dados.get("id_nota_perda_origem")
            lista_produtos = dados.get("produtos")
            if not lista_produtos:
                raise ValueError("'produtos' é obrigatório.")

            # Se id_nota_perda_origem for omisso, busca a Nota de Perda (Tipo 4 ou 5) mais recente/FIFO do fornecedor
            if not id_perda_orig:
                try:
                    from br.com.pdv.src.BDD.bancodb import BancoDB
                    row_p = BancoDB.obter_conexao().execute(
                        "SELECT id FROM fluxosNotasEstoque WHERE id_tipoNota IN (4, 5) AND id_representante = ? ORDER BY id DESC LIMIT 1",
                        (id_rep,)
                    ).fetchone()
                    if row_p:
                        id_perda_orig = row_p["id"]
                except Exception:
                    pass

            if not id_perda_orig:
                id_perda_orig = 1  # Fallback de segurança

            data_emissao = cls._parse_data(dados.get("data")) or date.today()
            data_venc = cls._parse_data(dados.get("data_vencimento"))

            id_nota = DB.INSERT.FLUXO_NOTA_ESTOQUE.executar(
                5, id_rep, str(data_venc or data_emissao)
            )
            if not id_nota or id_nota <= 0:
                raise ValueError("Falha ao inserir o cabeçalho da nota de compensação no banco.")

            from br.com.pdv.src.financeiro.notaCompensacao import NotaCompensacao
            notaComp = NotaCompensacao(id=id_nota, id_nota_perda_origem=id_perda_orig,
                                       dataEmissao=data_emissao, dataVencimento=data_venc)

            for item in lista_produtos:
                id_prod = item.get("id")
                qtd = item.get("quantidade")
                if not id_prod or qtd is None or qtd <= 0:
                    raise ValueError(f"Item inválido em 'produtos': {item}")

                val_unit = item.get("valorUnidario")
                if not val_unit:
                    # Busca valoração do produto perdido na Nota de Perda de Origem
                    try:
                        from br.com.pdv.src.BDD.bancodb import BancoDB
                        row_val = BancoDB.obter_conexao().execute(
                            "SELECT valorUnidario FROM fluxoEstoque WHERE id_fluxo_nota = ? AND id_produto = ? LIMIT 1",
                            (id_perda_orig, id_prod)
                        ).fetchone()
                        if row_val and row_val["valorUnidario"]:
                            val_unit = float(row_val["valorUnidario"])
                    except Exception:
                        pass

                val_unit = val_unit or cls._get_custo_medio(str(id_prod))

                produto = ProductClassFactory.testar_e_fabricar(id_prod)
                if not produto:
                    raise ValueError(f"Produto ID {id_prod} não encontrado.")

                produto.insertPropertValue(valorUnidario=val_unit, quantidade=qtd)
                notaComp.adicionarProduto(produto)

                # Entrada da Reposição: id_tipoNota = 5 (REPOSIÇÃO), lucroTotal é 0.0
                DB.INSERT.FLUXO_ESTOQUE.executar(
                    id_perda_orig,  # id_notaOrigem = ID da Nota de Perda de Origem
                    id_nota, 5, id_prod, qtd, val_unit, 0.0, str(data_emissao)
                )

            notaComp.salvar()
            cls._NotasCompensacao.add(notaComp)
            cls._atualizar_mapa_com_nota(notaComp, id_tipo=5)

            print(f"[InventoryManager] Nota de Compensação ID {id_nota} registrada com sucesso.")
            return notaComp

        except Exception as e:
            print(f"[InventoryManager] Erro ao inserir nota de compensação: {e}")
            return None

    @classmethod
    def deletar_nota(cls, id_nota: int, cancelar_dependentes: bool = True) -> bool:
        """
        Cancela/Exclui uma nota do sistema.
        
        Se 'cancelar_dependentes=True' (padrão), localiza e deleta recursivamente
        quaisquer Devoluções, Perdas ou Reposições dependentes que tenham sido geradas 
        a partir desta nota, mantendo a integridade histórica perfeita.
        """
        try:
            from br.com.pdv.src.BDD.bancodb import BancoDB
            conn = BancoDB.obter_conexao()

            nota = conn.execute("SELECT * FROM fluxosNotasEstoque WHERE id = ?", (id_nota,)).fetchone()
            if not nota:
                print(f"[InventoryManager] Nota ID {id_nota} não encontrada para deleção.")
                return False

            id_tipo = nota["id_tipoNota"]

            # 1. Busca notas dependentes que citam 'id_nota' como id_notaOrigem em fluxoEstoque
            rows_dep = conn.execute(
                "SELECT DISTINCT id_fluxo_nota FROM fluxoEstoque WHERE id_notaOrigem = ? AND id_fluxo_nota != ?",
                (id_nota, id_nota)
            ).fetchall()
            ids_dependentes = [r["id_fluxo_nota"] for r in rows_dep if r["id_fluxo_nota"] != id_nota]

            if ids_dependentes:
                if not cancelar_dependentes:
                    str_deps = ", ".join([f"#{d}" for d in ids_dependentes])
                    raise ValueError(f"Não é possível excluir a Nota #{id_nota}: existem documentos dependentes vinculados ({str_deps}).")
                
                # Deleta recursivamente os documentos dependentes primeiro
                for id_dep in ids_dependentes:
                    cls.deletar_nota(id_dep, cancelar_dependentes=True)

            # 2. Se for Reposição/Compensação (tipo 5), valida se o lote já foi consumido por vendas posteriores
            if id_tipo == 5:
                itens_rep = conn.execute("SELECT id_produto, quantidade FROM fluxoEstoque WHERE id_fluxo_nota = ?", (id_nota,)).fetchall()
                for r in itens_rep:
                    id_p_str = str(r["id_produto"])
                    mapa = cls._mapaProdutos.get(id_p_str)
                    if mapa and mapa["quantidadeTotal"] < float(r["quantidade"]):
                        raise ValueError(f"Não é possível cancelar a Reposição #{id_nota}: o produto ID {id_p_str} já foi consumido por vendas posteriores.")

            # 3. Deleta no SQLite usando DELETE CASCADE (apaga fluxosNotasEstoque, fluxoEstoque e fluxoPagamentoNotas)
            conn.execute("DELETE FROM fluxosNotasEstoque WHERE id = ?", (id_nota,))
            conn.commit()

            # 4. Re-carrega o estado da memória para sincronizar 100% com o banco
            cls.carregarTudo()
            print(f"[InventoryManager] Nota ID {id_nota} (Tipo {id_tipo}) e seus vínculos deletados com SUCESSO via CASCADE.")
            return True

        except Exception as e:
            print(f"[InventoryManager] Erro ao deletar nota ID {id_nota}: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────
    # GET — Consultas e Relatórios
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def get_estoque_produto(cls, id_produto: int) -> dict:
        """
        Retorna o dict agregado do produto com totais e lotes FIFO disponíveis.

        Exemplo de retorno:
        {
            "quantidadeTotal": 87.0,
            "custoMedio": 2.0,
            "valorTotalEstoque": 174.0,
            "totalCompras": 87.0, "totalVendas": 0.0, ...
            "composicao": None,
            "lotes": [
                {"idx": "1.405.1.265.0", "qtd_disponivel": 87.0, "custo_unitario": 2.0, "data_entrada": ...}
            ]
        }
        """
        id_str = str(id_produto)
        mapa = cls._mapaProdutos.get(id_str)
        if not mapa:
            return {}
        resultado = dict(mapa)
        # Expande os lotes com os detalhes
        detalhes_lotes = []
        for idx_lote in mapa.get("lotes", []):
            lote = cls._mapaEstoque.get(idx_lote, {})
            detalhes_lotes.append({
                "idx": idx_lote,
                "qtd_disponivel": lote.get("qtd_disponivel", 0.0),
                "custo_unitario": lote.get("custo_unitario", 0.0),
                "data_entrada": lote.get("data_entrada")
            })
        resultado["lotes"] = detalhes_lotes
        return resultado

    @classmethod
    def get_nota(cls, id_nota: int) -> dict:
        """
        Retorna os dados completos de qualquer nota carregada em memória.
        Pesquisa por ID em todos os tipos de notas.
        """
        todas = list(cls._NotasCompras) + list(cls._NotasVendas) + \
                list(cls._NotasDevolucoes) + list(cls._NotasPerdas) + \
                list(cls._NotasCompensacao)
        for nota in todas:
            dados = nota.getDados()
            if dados.get("id") == id_nota:
                return dados
        return {}

    @classmethod
    def get_status(cls) -> dict:
        """
        Retorna um snapshot geral do estado do sistema.

        Retorno:
        {
            "total_produtos_distintos": int,
            "total_notas": {"compra": int, "venda": int, "devolucao": int, "perda": int, "compensacao": int},
            "valor_total_estoque": float,
            "produtos_negativos": [{"id_produto": str, "quantidadeTotal": float}],
            "produtos_sem_estoque": [str],
            "total_lotes_ativos": int
        }
        """
        valor_total = 0.0
        negativos = []
        sem_estoque = []

        for id_str, mapa in cls._mapaProdutos.items():
            qtd = mapa.get("quantidadeTotal", 0.0)
            valor_total += max(mapa.get("valorTotalEstoque", 0.0), 0.0)
            if qtd < 0:
                negativos.append({"id_produto": id_str, "quantidadeTotal": round(qtd, 4)})
            elif qtd == 0 and mapa.get("composicao") is None:
                sem_estoque.append(id_str)

        lotes_ativos = sum(1 for l in cls._mapaEstoque.values() if not l.get("consumido", True))

        return {
            "total_produtos_distintos": len(cls._mapaProdutos),
            "total_notas": {
                "compra": len(cls._NotasCompras),
                "venda": len(cls._NotasVendas),
                "devolucao": len(cls._NotasDevolucoes),
                "perda": len(cls._NotasPerdas),
                "compensacao": len(cls._NotasCompensacao)
            },
            "valor_total_estoque": round(valor_total, 2),
            "total_lotes_ativos": lotes_ativos,
            "produtos_negativos": negativos,
            "produtos_sem_estoque_count": len(sem_estoque)
        }

    @classmethod
    def get_triangulacao_sazonal(cls, id_produto: Optional[int] = None) -> list:
        """
        Retorna a triangulação de notas (Venda/Perda) com seus snapshots sazonais.

        Se id_produto=None, retorna todas as triangulações.
        Cada item retornado:
        {
            "id_nota": int,
            "tipo": "VENDA" | "PERDA",
            "data": date,
            "produtos": dict,
            "snapshot_sazonal": dict | None
        }
        """
        resultado = []
        notas_relevantes = list(cls._NotasVendas) + list(cls._NotasPerdas)

        for nota in notas_relevantes:
            dados = nota.getDados()
            id_nota = dados.get("id")
            tipo_str = "VENDA" if isinstance(nota, NotaVenda) else "PERDA"

            # Filtra por produto se especificado
            if id_produto is not None:
                ids_prod = [str(p["id"]) for p in dados.get("produtos", {}).values()]
                if str(id_produto) not in ids_prod:
                    continue

            # Busca snapshot sazonal no banco
            snapshot = DB.SELECT.SNAPSHOT_POR_NOTA.buscar_um(id_nota)

            resultado.append({
                "id_nota": id_nota,
                "tipo": tipo_str,
                "data": dados.get("dataEmissao") or dados.get("data"),
                "produtos": dados.get("produtos", {}),
                "snapshot_sazonal": snapshot
            })

        # Ordena por data
        resultado.sort(key=lambda x: x["data"] or date.min)
        return resultado

    @classmethod
    def analisar_tendencias_sazonais(cls, id_produto: Optional[int] = None) -> dict:
        """
        Cruza notas de Venda/Perda com seus snapshots sazonais e retorna
        um dict pronto para renderização de gráficos, cards e indicadores na UI.

        Parâmetro:
          id_produto: filtra por produto específico. None = todos os produtos.

        Estrutura do retorno (UI-ready):
        {
            "resumo": {
                "total_notas_analisadas": int,
                "notas_com_snapshot": int,
                "cobertura_pct": float,       # % de notas com dados sazonais
            },
            "por_clima": {
                "QUENTE": {"total_vendas": float, "total_perdas": float, "qtd_notas": int, "media_vendas": float},
                "FRIO":   {...},
                "AMENO":  {...},
            },
            "por_chuva": {
                "SECO": {...}, "MODERADO": {...}, "CHUVOSO": {...}
            },
            "por_rio": {
                "NORMAL": {...}, "CHEIA": {...}, "SECA": {...}
            },
            "por_temperatura": {
                # Faixas de 5°C para histograma de barras
                "ate_20":  {"total_vendas": float, "total_perdas": float, "qtd_notas": int},
                "20_25":   {...},
                "25_30":   {...},
                "30_35":   {...},
                "acima_35":{...},
            },
            "por_eventos": {
                # Agrupado por qtd de eventos proximos
                "0":     {"total_vendas": float, "total_perdas": float, "qtd_notas": int},
                "1_2":   {...},
                "3_mais":{...},
            },
            "serie_temporal_semanal": [
                # Série cronológica para gráfico de linha
                {"semana": "2026-W28", "total_vendas": float, "total_perdas": float, "qtd_notas": int}
            ],
            "indicadores": {
                # Indicadores prontos para cards na UI
                "clima_mais_vendas":   str,   # ex: "QUENTE"
                "clima_mais_perdas":   str,   # ex: "CHUVOSO"
                "temperatura_media_vendas": float,
                "risco_perda_clima":   str,   # clima com maior razão perda/venda
                "eventos_impacto":     str,   # "3_mais" ou "0" — onde vende mais
            },
            "alertas": [
                # Lista de strings prontas para exibir na UI
                "Vendas 40% maiores em clima QUENTE",
                "Chuva moderada associada a 25% das perdas",
            ]
        }
        """
        triangulacoes = cls.get_triangulacao_sazonal(id_produto)

        # ── Estruturas base ──────────────────────────────────────────
        def _bloco():
            return {"total_vendas": 0.0, "total_perdas": 0.0, "qtd_notas": 0}

        por_clima = {"QUENTE": _bloco(), "FRIO": _bloco(), "AMENO": _bloco()}
        por_chuva = {"SECO": _bloco(), "MODERADO": _bloco(), "CHUVOSO": _bloco()}
        por_rio   = {"NORMAL": _bloco(), "CHEIA": _bloco(), "SECA": _bloco()}
        por_temp  = {"ate_20": _bloco(), "20_25": _bloco(), "25_30": _bloco(),
                     "30_35": _bloco(), "acima_35": _bloco()}
        por_evento = {"0": _bloco(), "1_2": _bloco(), "3_mais": _bloco()}
        semanas: dict = {}

        total_notas = len(triangulacoes)
        notas_com_snap = 0
        soma_temp_vendas = 0.0
        qtd_temp_vendas = 0

        # ── Processa cada triangulação ────────────────────────────────
        for item in triangulacoes:
            tipo = item["tipo"]          # "VENDA" | "PERDA"
            snap = item.get("snapshot_sazonal")
            data_nota = item.get("data")

            # Calcula volume do item (soma de quantidades dos produtos)
            vol = sum(
                p.get("vendas", p.get("quantidadeEntrada", 0.0)) or 0.0
                for p in item.get("produtos", {}).values()
            )
            is_venda = tipo == "VENDA"

            if snap:
                notas_com_snap += 1
                clima = snap.get("indicador_clima", "AMENO")
                chuva = snap.get("indicador_chuva", "SECO")
                rio   = snap.get("indicador_rio",   "NORMAL")
                temp  = snap.get("temperatura_atual") or 0.0
                eventos = snap.get("qtd_eventos_proximos") or 0

                # ── Por Clima ──
                bloco_c = por_clima.get(clima, por_clima["AMENO"])
                bloco_c["qtd_notas"] += 1
                if is_venda: bloco_c["total_vendas"] += vol
                else:        bloco_c["total_perdas"] += vol

                # ── Por Chuva ──
                bloco_ch = por_chuva.get(chuva, por_chuva["SECO"])
                bloco_ch["qtd_notas"] += 1
                if is_venda: bloco_ch["total_vendas"] += vol
                else:        bloco_ch["total_perdas"] += vol

                # ── Por Rio ──
                bloco_r = por_rio.get(rio, por_rio["NORMAL"])
                bloco_r["qtd_notas"] += 1
                if is_venda: bloco_r["total_vendas"] += vol
                else:        bloco_r["total_perdas"] += vol

                # ── Por Temperatura (faixas de 5°C) ──
                if temp <= 20:   faixa = "ate_20"
                elif temp <= 25: faixa = "20_25"
                elif temp <= 30: faixa = "25_30"
                elif temp <= 35: faixa = "30_35"
                else:            faixa = "acima_35"
                bloco_t = por_temp[faixa]
                bloco_t["qtd_notas"] += 1
                if is_venda:
                    bloco_t["total_vendas"] += vol
                    soma_temp_vendas += temp * vol
                    qtd_temp_vendas += 1
                else:
                    bloco_t["total_perdas"] += vol

                # ── Por Eventos ──
                if eventos == 0:      chave_ev = "0"
                elif eventos <= 2:    chave_ev = "1_2"
                else:                 chave_ev = "3_mais"
                bloco_e = por_evento[chave_ev]
                bloco_e["qtd_notas"] += 1
                if is_venda: bloco_e["total_vendas"] += vol
                else:        bloco_e["total_perdas"] += vol

            # ── Série Temporal Semanal ─────────────────────────────────
            if data_nota:
                try:
                    d = data_nota if isinstance(data_nota, date) else date.fromisoformat(str(data_nota))
                    # Número da semana ISO: ex "2026-W28"
                    chave_semana = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
                    if chave_semana not in semanas:
                        semanas[chave_semana] = {"semana": chave_semana,
                                                  "total_vendas": 0.0,
                                                  "total_perdas": 0.0,
                                                  "qtd_notas": 0}
                    semanas[chave_semana]["qtd_notas"] += 1
                    if is_venda: semanas[chave_semana]["total_vendas"] += vol
                    else:        semanas[chave_semana]["total_perdas"] += vol
                except Exception:
                    pass

        # ── Adiciona media_vendas em por_clima ─────────────────────────
        for bloco in por_clima.values():
            n = bloco["qtd_notas"]
            bloco["media_vendas"] = round(bloco["total_vendas"] / n, 2) if n > 0 else 0.0

        # ── Calcula Indicadores para cards da UI ──────────────────────
        clima_max_venda  = max(por_clima, key=lambda k: por_clima[k]["total_vendas"])
        clima_max_perda  = max(por_clima, key=lambda k: por_clima[k]["total_perdas"])
        evento_max_venda = max(por_evento, key=lambda k: por_evento[k]["total_vendas"])
        temp_media_venda = round(soma_temp_vendas / qtd_temp_vendas, 1) if qtd_temp_vendas > 0 else 0.0

        # Risco = clima onde (perdas / (vendas + perdas)) é maior
        def _risco(bloco):
            tot = bloco["total_vendas"] + bloco["total_perdas"]
            return bloco["total_perdas"] / tot if tot > 0 else 0.0
        clima_risco = max(por_clima, key=lambda k: _risco(por_clima[k]))

        # ── Alertas automáticos ───────────────────────────────────────
        alertas = []
        q_max = por_clima[clima_max_venda]["total_vendas"]
        q_min = min(por_clima[k]["total_vendas"] for k in por_clima if por_clima[k]["total_vendas"] > 0) if any(por_clima[k]["total_vendas"] > 0 for k in por_clima) else 1
        if q_min > 0 and q_max / q_min >= 1.3:
            pct = round((q_max / q_min - 1) * 100)
            alertas.append(f"Vendas {pct}% maiores em clima {clima_max_venda} vs. outros climas.")
        if por_chuva["CHUVOSO"]["total_perdas"] > por_chuva["SECO"]["total_perdas"] * 1.2:
            alertas.append("Clima CHUVOSO associado a aumento significativo de perdas.")
        if por_rio["CHEIA"]["total_vendas"] > por_rio["NORMAL"]["total_vendas"] * 1.15:
            alertas.append("Rio em CHEIA associado a aumento de vendas (possível demanda por suprimentos).")
        if por_evento["3_mais"]["total_vendas"] > por_evento["0"]["total_vendas"] * 1.2:
            alertas.append("Presenca de 3+ eventos proximos eleva significativamente as vendas.")

        serie = sorted(semanas.values(), key=lambda x: x["semana"])
        cobertura = round(notas_com_snap / total_notas * 100, 1) if total_notas > 0 else 0.0

        return {
            "resumo": {
                "total_notas_analisadas": total_notas,
                "notas_com_snapshot": notas_com_snap,
                "cobertura_pct": cobertura,
            },
            "por_clima":      por_clima,
            "por_chuva":      por_chuva,
            "por_rio":        por_rio,
            "por_temperatura": por_temp,
            "por_eventos":    por_evento,
            "serie_temporal_semanal": serie,
            "indicadores": {
                "clima_mais_vendas":        clima_max_venda,
                "clima_mais_perdas":        clima_max_perda,
                "temperatura_media_vendas": temp_media_venda,
                "risco_perda_clima":        clima_risco,
                "eventos_impacto":          evento_max_venda,
            },
            "alertas": alertas
        }

    @classmethod
    def get_produtos_lista(cls) -> list:
        """
        Retorna lista resumida de todos os produtos mapeados.
        Ideal para popular dropdowns, tabelas de seleção e auto-complete na UI.

        Cada item:
        {
            "id": int,
            "id_str": str,                  # chave do _mapaProdutos
            "qtd_estoque": float,
            "valor_estoque": float,
            "custo_medio": float,
            "total_compras": float,
            "total_vendas": float,
            "total_perdas": float,
            "total_devolucoes": float,
            "eh_composto": bool,            # True se tem receita/composicao
            "lotes_disponiveis": int,       # qtd de lotes ativos FIFO
            "alerta_negativo": bool,        # estoque < 0
        }
        """
        resultado = []
        for id_str, mapa in cls._mapaProdutos.items():
            qtd = mapa.get("quantidadeTotal", 0.0)
            resultado.append({
                "id": int(id_str),
                "id_str": id_str,
                "qtd_estoque": round(qtd, 4),
                "valor_estoque": round(max(mapa.get("valorTotalEstoque", 0.0), 0.0), 2),
                "custo_medio": round(mapa.get("custoMedio", 0.0), 4),
                "total_compras": mapa.get("totalCompras", 0.0),
                "total_vendas": mapa.get("totalVendas", 0.0),
                "total_perdas": mapa.get("totalPerdas", 0.0),
                "total_devolucoes": mapa.get("totalDevolucoes", 0.0),
                "eh_composto": mapa.get("composicao") is not None,
                "lotes_disponiveis": len(mapa.get("lotes", [])),
                "alerta_negativo": qtd < 0,
            })
        # Ordenado por id numérico
        resultado.sort(key=lambda x: x["id"])
        return resultado

    @classmethod
    def get_notas_por_tipo(cls, tipo: int, limit: int = 50, offset: int = 0) -> list:
        """
        Retorna lista paginada de notas de um tipo específico.
        Ideal para telas de histórico com scroll infinito ou paginação.

        Parâmetros:
          tipo   : 1=Compra, 2=Venda, 3=Devolução, 4=Perda, 5=Compensação
          limit  : máximo de registros por página (default 50)
          offset : deslocamento para paginação (default 0)

        Cada item retornado é o dict completo de getDados() da nota,
        acrescido de 'tipo_label' para facilitar a UI.

        Retorno:
        {
            "total": int,         # total sem paginação (para a UI calcular páginas)
            "limit": int,
            "offset": int,
            "dados": [lista de dicts das notas]
        }
        """
        _tipo_label = {1: "COMPRA", 2: "VENDA", 3: "DEVOLUCAO", 4: "PERDA", 5: "COMPENSACAO"}
        _colecoes = {
            1: cls._NotasCompras,
            2: cls._NotasVendas,
            3: cls._NotasDevolucoes,
            4: cls._NotasPerdas,
            5: cls._NotasCompensacao,
        }

        colecao = _colecoes.get(tipo)
        if colecao is None:
            return {"total": 0, "limit": limit, "offset": offset, "dados": []}

        # Ordena por data antes de paginar
        notas_ordenadas = sorted(
            colecao,
            key=lambda n: n.getDados().get("dataEmissao") or n.getDados().get("data") or date.min,
            reverse=True  # mais recentes primeiro
        )
        total = len(notas_ordenadas)
        pagina = notas_ordenadas[offset: offset + limit]

        label = _tipo_label.get(tipo, str(tipo))
        dados = []
        for nota in pagina:
            d = nota.getDados()
            d["tipo_label"] = label
            dados.append(d)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "dados": dados
        }

    @classmethod
    def atualizar_valores_gerais(cls) -> dict:
        """
        Força o recálculo completo de _mapaProdutos e _mapaEstoque
        a partir das notas já carregadas em memória.
        Retorna o novo get_status() após a atualização.
        """
        cls.mapearProdutos()
        return cls.get_status()



    # ─────────────────────────────────────────────────────────────────
    # Helpers Internos
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _get_custo_medio(cls, id_produto_str: str) -> float:
        """Retorna o custo médio atual do produto no mapa."""
        return cls._mapaProdutos.get(id_produto_str, {}).get("custoMedio", 0.0)

    @classmethod
    def _consumir_fifo_interno(cls, id_produto_str: str, qtd_necessaria: float) -> list:
        """
        Consome qtd_necessaria de lotes FIFO do produto e atualiza o _mapaEstoque e _mapaProdutos.
        Retorna lista de (idx_lote, qtd_consumida).
        """
        mapa = cls._mapaProdutos.get(id_produto_str, {})
        lotes_fifo = mapa.get("lotes", [])
        rastro = []
        restante = qtd_necessaria
        for idx_lote in lotes_fifo[:]:
            if restante <= 0:
                break
            lote = cls._mapaEstoque.get(idx_lote)
            if not lote or lote["qtd_disponivel"] <= 0:
                continue
            consumivel = min(lote["qtd_disponivel"], restante)
            lote["qtd_disponivel"] -= consumivel
            if lote["qtd_disponivel"] <= 0:
                lote["consumido"] = True
                lotes_fifo.remove(idx_lote)
            restante -= consumivel
            rastro.append((idx_lote, consumivel))
        return rastro

    @classmethod
    def _atualizar_mapa_com_nota(cls, nota, id_tipo: int) -> None:
        """
        Atualiza incrementalmente _mapaProdutos e _mapaEstoque com uma nota recém inserida,
        sem precisar reprocessar todas as notas. Usa a mesma lógica do mapearProdutos.
        """
        dados = nota.getDados()
        id_nota = dados.get("id")
        data_nota = dados.get("dataEmissao") or date.today()
        produtos_dict = dados.get("produtos", {})

        def _garantir_produto(id_str):
            if id_str not in cls._mapaProdutos:
                cls._mapaProdutos[id_str] = {
                    "quantidadeTotal": 0.0, "valorTotalEstoque": 0.0, "custoMedio": 0.0,
                    "totalCompras": 0.0, "totalVendas": 0.0, "totalPerdas": 0.0,
                    "totalDevolucoes": 0.0, "composicao": None, "lotes": []
                }
            return cls._mapaProdutos[id_str]

        for chave, prod in produtos_dict.items():
            id_prod_str = str(prod["id"])
            receita = prod.get("Receita")
            partes = str(chave).split(".")
            variacao = int(partes[-1]) if partes else 0
            qtd_mov = prod.get("vendas", prod.get("quantidadeEntrada", 0.0)) if id_tipo == 2 else prod.get("quantidadeEntrada", 0.0)

            mapa = _garantir_produto(id_prod_str)
            if receita:
                mapa["composicao"] = receita

            if id_tipo in (1, 5):
                custo = prod.get("ValorTotal", 0.0)
                custo_unit = (custo / qtd_mov) if qtd_mov > 0 else prod.get("valorUnitario", 0.0)
                mapa["quantidadeTotal"] += qtd_mov
                mapa["valorTotalEstoque"] += custo
                mapa["totalCompras"] += qtd_mov
                if mapa["quantidadeTotal"] > 0:
                    mapa["custoMedio"] = mapa["valorTotalEstoque"] / mapa["quantidadeTotal"]
                cls._contadorLote += 1
                idx = f"{cls._contadorLote}.{id_nota}.{id_tipo}.{id_prod_str}.{variacao}"
                cls._mapaEstoque[idx] = {
                    "id_nota": id_nota, "id_tipo": id_tipo, "id_produto": int(id_prod_str),
                    "variacao": variacao, "qtd_inicial": qtd_mov, "qtd_disponivel": qtd_mov,
                    "custo_unitario": custo_unit, "data_entrada": data_nota, "consumido": False
                }
                mapa["lotes"].append(idx)
            elif id_tipo == 2:
                if receita:
                    for id_ingr, qtd_ingr in receita.items():
                        mi = _garantir_produto(str(id_ingr))
                        qc = qtd_mov * qtd_ingr
                        mi["quantidadeTotal"] -= qc
                        mi["valorTotalEstoque"] -= qc * mi["custoMedio"]
                        mi["totalVendas"] += qc
                else:
                    mapa["quantidadeTotal"] -= qtd_mov
                    mapa["valorTotalEstoque"] -= qtd_mov * mapa["custoMedio"]
                    mapa["totalVendas"] += qtd_mov
            elif id_tipo == 4:
                if receita:
                    for id_ingr, qtd_ingr in receita.items():
                        mi = _garantir_produto(str(id_ingr))
                        qp = qtd_mov * qtd_ingr
                        mi["quantidadeTotal"] -= qp
                        mi["valorTotalEstoque"] -= qp * mi["custoMedio"]
                        mi["totalPerdas"] += qp
                else:
                    mapa["quantidadeTotal"] -= qtd_mov
                    mapa["valorTotalEstoque"] -= qtd_mov * mapa["custoMedio"]
                    mapa["totalPerdas"] += qtd_mov
            elif id_tipo == 3:
                if receita:
                    for id_ingr, qtd_ingr in receita.items():
                        mi = _garantir_produto(str(id_ingr))
                        qd = qtd_mov * qtd_ingr
                        mi["quantidadeTotal"] += qd
                        mi["valorTotalEstoque"] += qd * mi["custoMedio"]
                        mi["totalDevolucoes"] += qd
                        cls._contadorLote += 1
                        idx = f"{cls._contadorLote}.{id_nota}.{id_tipo}.{str(id_ingr)}.{variacao}"
                        cls._mapaEstoque[idx] = {
                            "id_nota": id_nota, "id_tipo": id_tipo, "id_produto": id_ingr,
                            "variacao": variacao, "qtd_inicial": qd, "qtd_disponivel": qd,
                            "custo_unitario": mi["custoMedio"], "data_entrada": data_nota, "consumido": False
                        }
                        mi["lotes"].append(idx)
                else:
                    mapa["quantidadeTotal"] += qtd_mov
                    mapa["valorTotalEstoque"] += qtd_mov * mapa["custoMedio"]
                    mapa["totalDevolucoes"] += qtd_mov
                    cls._contadorLote += 1
                    idx = f"{cls._contadorLote}.{id_nota}.{id_tipo}.{id_prod_str}.{variacao}"
                    cls._mapaEstoque[idx] = {
                        "id_nota": id_nota, "id_tipo": id_tipo, "id_produto": int(id_prod_str),
                        "variacao": variacao, "qtd_inicial": qtd_mov, "qtd_disponivel": qtd_mov,
                        "custo_unitario": mapa["custoMedio"], "data_entrada": data_nota, "consumido": False
                    }
                    mapa["lotes"].append(idx)

    @staticmethod
    def _parse_data(valor) -> Optional[date]:
        """Converte string 'YYYY-MM-DD' ou date para date. Retorna None se inválido."""
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str):
            try:
                return datetime.strptime(valor, "%Y-%m-%d").date()
            except ValueError:
                pass
        return None


if False:
    InventoryManager.carregarTudo()

    # 1. Venda de 60 cartelas por R$ 20,00 (Gera Nota #6 - VENDA)
    venda_payload = {
        "id_cliente": 7,
        "produtos": [
            {"id": 6, "quantidade": 60, "valorVenda": 20.0}
        ]
    }
    n_venda = InventoryManager.insert_venda(venda_payload)

    # 2. Devolução direta de 30 cartelas referentes à Venda #6 (Gera Nota #7 - DEVOLUÇÃO)
    devolucao_payload = {
        "id_cliente": 7,
        "id_nota_venda_origem": 6,
        "produtos": [
            {"id": 6, "quantidade": 30}
        ]
    }
    n_dev = InventoryManager.insert_devolucao(devolucao_payload)

    # 3. Perda Inteligente de 18 cartelas citando a Venda #6 (Gera Devolução #8 + Perda Pós-Devolução #9)
    perda_payload = {
        "id_nota_origem": 6,
        "produtos": [
            {"id": 6, "quantidade": 18}
        ]
    }
    n_perda = InventoryManager.insert_perda(perda_payload)

    # 4. Ressarcimento / Compensação Financeira referente à Perda #9 (Gera Nota #10 - COMPENSAÇÃO)
    compensacao_payload = {
        "id_nota_perda_origem": 9,
        "produtos": [
            {"id": 6, "quantidade": 18}
        ]
    }
    n_comp = InventoryManager.insert_compensacao(compensacao_payload)

    # 5. Perda Geral de Estoque via FIFO (Gera Nota #11 - PERDA-ESTOQUE GERAL)
    perda_estoque_geral_payload = {
        "origem": "ESTOQUE",
        "produtos": [
            {"id": 6, "quantidade": 10}
        ]
    }
    n_perda_est = InventoryManager.insert_perda(perda_estoque_geral_payload)

    # 6. Perda de Estoque de Lote Específico de Compra (Gera Nota #12 - PERDA-ESTOQUE LOTE #1)
    perda_lote_especifico_payload = {
        "id_nota_origem": 1,
        "produtos": [
            {"id": 1, "quantidade": 1.0}
        ]
    }
    n_perda_lote = InventoryManager.insert_perda(perda_lote_especifico_payload)


    InventoryManager.deletar_nota(6)