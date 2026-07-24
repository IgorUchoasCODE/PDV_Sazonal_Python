import sqlite3
from datetime import datetime, date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaCompensacao import NotaCompensacao
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory
from br.com.pdv.src.memory.lossNoteClassFactory import LossNoteClassFactory


class CompensationNoteClassFactory:
    """
    Fábrica responsável por instanciar e reconstruir objetos NotaCompensacao (Reposição).
    Cita obrigatoriamente a NotaPerda de origem (id_notaOrigem -> perda).
    A compensação recupera a disponibilidade dos produtos/ingredientes perdidos
    obtendo todos os dados contábeis da NotaCompra de origem através de PurchaseNoteClassFactory.
    """

    __compensationNote: dict[int, NotaCompensacao] = {}

    @classmethod
    def fabricar(cls, id: int) -> NotaCompensacao:
        if id in cls.__compensationNote:
            return cls.__compensationNote[id]

        try:
            nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id)
            if not nota:
                raise ValueError(f"Erro ao fabricar nota de compensação {id}: nota não encontrada no banco.")

            if nota.get("id_tipoNota") != 5:
                raise ValueError(f"Erro ao fabricar nota de compensação {id}: a nota no banco é do tipo {nota.get('id_tipoNota')} (esperado tipo 5: REPOSIÇÃO/COMPENSAÇÃO).")

            id_nota_perda_origem = nota.get("id_notaOrigem")
            if not id_nota_perda_origem:
                raise ValueError(f"Nota de compensação {id} precisa referenciar uma nota de perda de origem.")

            # Instancia/referencia a NotaPerda de origem via LossNoteClassFactory
            LossNoteClassFactory.fabricar(id_nota_perda_origem)

            data_emissao = nota.get("data") or nota.get("data_vencimento")
            data_vencimento = nota.get("data_vencimento")

            if isinstance(data_emissao, str):
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").date()
            elif data_emissao is None:
                data_emissao = date.today()

            if isinstance(data_vencimento, str):
                data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()

            notaCompensacao = NotaCompensacao(
                id=id,
                id_nota_perda_origem=id_nota_perda_origem,
                dataEmissao=data_emissao,
                dataVencimento=data_vencimento
            )

            if not cls.reconstruir_produtos(notaCompensacao, id):
                raise ValueError(f"Erro ao reconstruir produtos para a nota de compensação {id}")

        except Exception as e:
            print(f"Erro ao fabricar nota de compensação {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de compensação {e}")
            return None

        if notaCompensacao and notaCompensacao.salvar():
            cls.__compensationNote[id] = notaCompensacao
            return notaCompensacao
        return None

    @classmethod
    def reconstruir_produtos(cls, notaCompensacao: NotaCompensacao, id_nota: int) -> bool:
        """
        Auxilia na reconstrução dos produtos em uma nota de compensação.
        Obtém os dados contábeis de origem de cada produto/ingrediente via PurchaseNoteClassFactory.
        """
        try:
            itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            if not itens:
                itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)

            if not itens:
                return False

            for ntc in itens:
                id_produto = ntc["id_produto"]
                quantidade = ntc["quantidade"]
                valor_unidario = ntc["valorUnidario"]

                produto = ProductClassFactory.testar_e_fabricar(id_produto)
                receita = produto.getDados().get("Receita")

                # Se for produto composto (tiver receita), compensa os ingredientes
                if receita and isinstance(receita, dict):
                    for id_ingrediente, qtd_por_unidade in receita.items():
                        qtd_compensar = quantidade * qtd_por_unidade

                        ingrediente = ProductClassFactory.testar_e_fabricar(id_ingrediente)
                        cls._referenciar_nota_compra_ingrediente(id_ingrediente)
                        custo_ingrediente = cls._obter_custo_ingrediente(id_ingrediente)

                        ingrediente.insertPropertValue(valorUnidario=custo_ingrediente, quantidade=qtd_compensar)
                        notaCompensacao.adicionarProduto(ingrediente)
                else:
                    # Produto simples: compensa o produto diretamente
                    cls._referenciar_nota_compra_ingrediente(id_produto)
                    produto.insertPropertValue(valorUnidario=valor_unidario, quantidade=quantidade)
                    notaCompensacao.adicionarProduto(produto)

            return True
        except Exception as e:
            print(f"Erro ao reconstruir produtos da nota de compensação {id_nota}: {e}")
            return False

    @classmethod
    def _referenciar_nota_compra_ingrediente(cls, id_ingrediente: int) -> int:
        """
        Busca e referencia a nota de compra de origem para obter os dados contábeis da compra,
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
            print(f"Erro ao referenciar nota de compra para o produto {id_ingrediente}: {e}")
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
    nc = CompensationNoteClassFactory.fabricar(11)
    if nc:
        print("NotaCompensacao 11:\n", nc.getDados())
