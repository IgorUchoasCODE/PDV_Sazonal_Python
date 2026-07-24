import sqlite3
from datetime import datetime, date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaDevolucao import NotaDevolucao
from br.com.pdv.src.memory.clientClassFactory import ClientClassFactory
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
from br.com.pdv.src.memory.saleNoteClassFactory import SaleNoteClassFactory
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory


class ReturnNoteClassFactory:
    """
    Fábrica responsável por instanciar e reconstruir objetos NotaDevolucao.
    Cita obrigatoriamente a NotaVenda de origem (id_notaOrigem).
    Para produtos compostos (que possuem receita), devolve ao estoque os seus ingredientes.
    """

    __returnNote: dict[int, NotaDevolucao] = {}

    @classmethod
    def fabricar(cls, id: int) -> NotaDevolucao:
        if id in cls.__returnNote:
            return cls.__returnNote[id]

        try:
            nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id)
            if not nota:
                raise ValueError(f"Erro ao fabricar nota de devolução {id}: nota não encontrada no banco.")

            if nota.get("id_tipoNota") != 3:
                raise ValueError(f"Erro ao fabricar nota de devolução {id}: a nota no banco é do tipo {nota.get('id_tipoNota')} (esperado tipo 3: DEVOLUÇÃO).")

            client = ClientClassFactory.fabricar(id=nota["id_representante"])
            if not client:
                raise ValueError(f"Erro ao fabricar cliente (ID {nota['id_representante']}) para a nota de devolução {id}.")

            id_nota_venda_origem = nota.get("id_notaOrigem")
            if not id_nota_venda_origem:
                raise ValueError(f"Nota de devolução {id} precisa referenciar uma nota de venda de origem.")

            # Referencia / fabricar a NotaVenda de origem via SaleNoteClassFactory
            SaleNoteClassFactory.fabricar(id_nota_venda_origem)

            data_emissao = nota.get("data") or nota.get("data_vencimento")
            data_vencimento = nota.get("data_vencimento")

            if isinstance(data_emissao, str):
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").date()
            elif data_emissao is None:
                data_emissao = date.today()

            if isinstance(data_vencimento, str):
                data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()

            notaDevolucao = NotaDevolucao(
                id=id,
                clienteFornecedor=client,
                id_nota_venda_origem=id_nota_venda_origem,
                dataEmissao=data_emissao,
                dataVencimento=data_vencimento
            )

            if not cls.reconstruir_produtos(notaDevolucao, id):
                raise ValueError(f"Erro ao reconstruir produtos para a nota de devolução {id}")

        except Exception as e:
            print(f"Erro ao fabricar nota de devolução {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de devolução {e}")
            return None

        if notaDevolucao and notaDevolucao.salvar():
            cls.__returnNote[id] = notaDevolucao
            return notaDevolucao
        return None

    @classmethod
    def reconstruir_produtos(cls, notaDevolucao: NotaDevolucao, id_nota: int) -> bool:
        """
        Auxilia na reconstrução dos produtos em uma nota de devolução.
        Lembrando que a devolução de produtos compostos devolve ao estoque os seus ingredientes.
        """
        try:
            itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            if not itens:
                itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)

            if not itens:
                return False

            for ntd in itens:
                id_produto = ntd["id_produto"]
                quantidade = ntd["quantidade"]
                valor_unidario = ntd["valorUnidario"]

                # Fabricar a instância do produto
                produto = ProductClassFactory.testar_e_fabricar(id_produto)
                receita = produto.getDados().get("Receita")

                # Se o produto for composto (possuir receita): devolve os ingredientes ao estoque
                if receita and isinstance(receita, dict):
                    for id_ingrediente, qtd_por_unidade in receita.items():
                        qtd_devolver = quantidade * qtd_por_unidade

                        ingrediente = ProductClassFactory.testar_e_fabricar(id_ingrediente)
                        cls._referenciar_nota_compra_ingrediente(id_ingrediente)
                        custo_ingrediente = cls._obter_custo_ingrediente(id_ingrediente)

                        ingrediente.insertPropertValue(valorUnidario=custo_ingrediente, quantidade=qtd_devolver)
                        notaDevolucao.adicionarProduto(ingrediente)
                else:
                    # Produto simples: devolve o produto diretamente
                    produto.insertPropertValue(valorUnidario=valor_unidario, quantidade=quantidade)
                    notaDevolucao.adicionarProduto(produto)

            return True
        except Exception as e:
            print(f"Erro ao reconstruir produtos da nota de devolução {id_nota}: {e}")
            return False

    @classmethod
    def _referenciar_nota_compra_ingrediente(cls, id_ingrediente: int) -> int:
        """
        Busca e referencia a nota de compra de origem para um ingrediente específico,
        invocando PurchaseNoteClassFactory.fabricar.
        """
        try:
            compras = DB.SELECT.ESTOQUE_COMPRA_PRODUTO_TODOS.buscar()
            if compras:
                for c in compras:
                    if c["id_produto"] == id_ingrediente:
                        id_compra = c["id_fluxo_nota"]
                        PurchaseNoteClassFactory.fabricar(id_compra)
                        return id_compra
        except Exception as e:
            print(f"Erro ao referenciar nota de compra do ingrediente {id_ingrediente}: {e}")
        return None

    @classmethod
    def _obter_custo_ingrediente(cls, id_ingrediente: int) -> float:
        """
        Retorna o custo unitário mais recente de compra para o ingrediente.
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
    nd = ReturnNoteClassFactory.fabricar(556)
    if nd:
        print("NotaDevolucao 6: \n", nd.getDados())
