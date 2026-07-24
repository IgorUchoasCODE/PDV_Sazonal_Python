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
        Auxilia na reconstrução dos produtos em uma nota de venda,
        suportando produtos simples e compostos (com receita).
        Mantém a referência da classe PurchaseNoteClassFactory através do id_notaOrigem
        dos produtos e de seus ingredientes para retornar a NotaVenda construída.
        """
        try:
            itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            if not itens:
                itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)

            if not itens:
                return False

            for ntv in itens:
                id_produto = ntv["id_produto"]
                quantidade = ntv["quantidade"]
                valor_unidario = ntv["valorUnidario"]

                # Obtém o id_notaOrigem do item ou do cabeçalho da nota
                id_nota_origem = ntv.get("id_notaOrigem")
                if id_nota_origem is None:
                    nota_hdr = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_nota)
                    if nota_hdr:
                        id_nota_origem = nota_hdr.get("id_notaOrigem")

                # Se houver id_notaOrigem (nota de compra), instancia/referencia a NotaCompra via PurchaseNoteClassFactory
                if id_nota_origem is not None and id_nota_origem > 0:
                    PurchaseNoteClassFactory.fabricar(id_nota_origem)

                # Fabricar a instância de Produto
                produto = ProductClassFactory.testar_e_fabricar(id_produto)

                # Se o produto for composto (tiver receita), busca e referencia as notas de compra de cada ingrediente
                receita = produto.getDados().get("Receita")
                custo_unitario_ingredientes = 0.0
                if receita and isinstance(receita, dict):
                    mapa_ingredientes = {}
                    for id_ingrediente, qtd_por_unid in receita.items():
                        id_compra_ing = cls._referenciar_nota_compra_ingrediente(id_ingrediente, id_nota)
                        if id_compra_ing:
                            mapa_ingredientes[id_ingrediente] = id_compra_ing
                        custo_unitario_ingredientes += cls._obter_custo_ingrediente(id_ingrediente) * qtd_por_unid
                    if mapa_ingredientes:
                        id_nota_origem = mapa_ingredientes
                else:
                    custo_unitario_ingredientes = cls._obter_custo_ingrediente(id_produto)
                    if id_nota_origem is not None and isinstance(id_nota_origem, int) and id_nota_origem > 0:
                        PurchaseNoteClassFactory.fabricar(id_nota_origem)

                # Configura custo unitário e registra a venda
                produto.insertPropertValue(valorUnidario=custo_unitario_ingredientes, quantidade=quantidade)
                produto.vender(quantidadeVendas=quantidade, valorVenda=valor_unidario)

                # Adiciona o produto na nota de venda vinculando o id da nota de origem de compra
                notaVenda.adicionarProduto(produto, id_nota_origem=id_nota_origem)

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