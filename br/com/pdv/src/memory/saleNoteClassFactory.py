import sqlite3
from datetime import datetime, date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaVenda import NotaVenda
from br.com.pdv.src.memory.clientClassFactory import ClientClassFactory
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory


class SaleNoteClassFactory:
    __saleNote: dict[int, NotaVenda] = {}

    @classmethod
    def fabricar(cls, id: int) -> NotaVenda:
        if id in cls.__saleNote:
            return cls.__saleNote[id]

        try:
            nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id)
            if not nota:
                raise ValueError(f"Erro ao fabricar nota de venda {id}: nota não encontrada no banco.")

            if nota.get("id_tipoNota") != 2:
                raise ValueError(f"Erro ao fabricar nota de venda {id}: a nota no banco é do tipo {nota.get('id_tipoNota')} (esperado tipo 2: VENDA).")

            client = ClientClassFactory.fabricar(id=nota["id_representante"])
            if not client:
                raise ValueError(f"Erro ao fabricar cliente (ID {nota['id_representante']}) para a nota de venda {id}.")

            data_emissao = nota.get("data") or nota.get("data_vencimento")
            data_vencimento = nota.get("data_vencimento")

            if isinstance(data_emissao, str):
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").date()
            elif data_emissao is None:
                data_emissao = date.today()

            if isinstance(data_vencimento, str):
                data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()

            notaVenda = NotaVenda(id, client, data_emissao, data_vencimento)

            if not cls.reconstruir_produtos(notaVenda, id):
                raise ValueError(f"Erro ao reconstruir produtos para a nota de venda {id}")

        except Exception as e:
            print(f"Erro ao fabricar nota de venda {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de venda {e}")
            return None

        if notaVenda and notaVenda.salvar():
            cls.__saleNote[id] = notaVenda
            return notaVenda
        return None

    @classmethod
    def reconstruir_produtos(cls, notaVenda: NotaVenda, id_nota: int) -> bool:
        """
        Reconstrói os produtos em uma nota de venda.
        Como a venda agora gera N linhas no fluxoEstoque (uma por lote FIFO de origem),
        agrupa as linhas pelo id_produto antes de criar os objetos Produto.
        Lê id_notaOrigem diretamente do item (fe.id_notaOrigem) — sem NULL.
        """
        try:
            itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            if not itens:
                itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)

            if not itens:
                return False

            # ── Agrega linhas pelo id_produto (múltiplas origens FIFO) ──
            from collections import defaultdict
            grupos: dict = defaultdict(lambda: {
                "quantidade": 0.0,
                "custo_total": 0.0,
                "val_venda": 0.0,
                "origens": []
            })
            for ntv in itens:
                id_produto = ntv["id_produto"]
                qtd_linha = ntv["quantidade"]
                val_unit = ntv["valorUnidario"]
                id_nota_origem = ntv.get("id_notaOrigem")  # Agora vem direto do item

                g = grupos[id_produto]
                g["quantidade"] += qtd_linha
                g["custo_total"] += 0  # custo será recalculado via _obter_custo_ingrediente
                g["val_venda"] = val_unit  # preço de venda é igual para todas as linhas do mesmo produto
                if id_nota_origem and id_nota_origem not in g["origens"]:
                    g["origens"].append(id_nota_origem)
                    if id_nota_origem != id_nota:
                        PurchaseNoteClassFactory.fabricar(id_nota_origem)

            # ── Cria um Produto por grupo ──
            for id_produto, g in grupos.items():
                produto = ProductClassFactory.testar_e_fabricar(id_produto)
                if not produto:
                    continue

                receita = produto.getDados().get("Receita")
                custo_unitario = 0.0

                if receita and isinstance(receita, dict):
                    mapa_ingredientes = {}
                    for id_ingrediente, qtd_por_unid in receita.items():
                        id_compra_ing = cls._referenciar_nota_compra_ingrediente(id_ingrediente, id_nota)
                        if id_compra_ing:
                            mapa_ingredientes[id_ingrediente] = id_compra_ing
                        custo_unitario += cls._obter_custo_ingrediente(id_ingrediente) * qtd_por_unid
                    id_nota_origem_final = mapa_ingredientes if mapa_ingredientes else g["origens"]
                else:
                    custo_unitario = cls._obter_custo_ingrediente(id_produto)
                    origens = g["origens"]
                    if len(origens) == 1:
                        id_nota_origem_final = origens[0]
                    elif len(origens) > 1:
                        # Múltiplas origens FIFO — retorna dict {id_origem: id_origem}
                        id_nota_origem_final = {o: o for o in origens}
                    else:
                        id_nota_origem_final = None

                produto.insertPropertValue(valorUnidario=custo_unitario, quantidade=g["quantidade"])
                produto.vender(quantidadeVendas=g["quantidade"], valorVenda=g["val_venda"])
                notaVenda.adicionarProduto(produto, id_nota_origem=id_nota_origem_final)

            return True
        except Exception as e:
            print(f"Erro ao reconstruir produtos da nota de venda {id_nota}: {e}")
            return False

    @classmethod
    def _referenciar_nota_compra_ingrediente(cls, id_ingrediente: int, id_nota_venda: int) -> int:
        """
        Busca e referencia a nota de compra de origem para um ingrediente específico de um produto composto,
        invocando PurchaseNoteClassFactory.fabricar.
        """
        try:
            # Tenta buscar no fluxo de estoque de compras (id_tipoNota = 1)
            compras = DB.SELECT.ESTOQUE_COMPRA_PRODUTO_TODOS.buscar()
            id_compra_encontrada = None
            if compras:
                for c in compras:
                    if c["id_produto"] == id_ingrediente:
                        id_compra_encontrada = c["id_fluxo_nota"]
                        break

            # Fabricar a NotaCompra via PurchaseNoteClassFactory se encontrada
            if id_compra_encontrada:
                PurchaseNoteClassFactory.fabricar(id_compra_encontrada)
                return id_compra_encontrada

        except Exception as e:
            print(f"Erro ao referenciar nota de compra do ingrediente {id_ingrediente}: {e}")
        return None

    @classmethod
    def _obter_custo_ingrediente(cls, id_ingrediente: int) -> float:
        """
        Retorna o custo unitário mais recente de compra para o ingrediente/produto.
        """
        try:
            compras = DB.SELECT.ESTOQUE_COMPRA_PRODUTO_TODOS.buscar()
            if compras:
                custos = [c["valorUnidario"] for c in compras if c["id_produto"] == id_ingrediente]
                if custos:
                    return max(custos)
        except Exception:
            pass
        return 0.0


if __name__ == "__main__":
    nt = SaleNoteClassFactory.fabricar(17)
    if nt:
        print("\n",nt.getDados())