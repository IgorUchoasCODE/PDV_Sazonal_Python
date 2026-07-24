import sqlite3
from datetime import datetime, date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaPerda import NotaPerda
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory
from br.com.pdv.src.memory.returnNoteClassFactory import ReturnNoteClassFactory
from br.com.pdv.src.memory.saleNoteClassFactory import SaleNoteClassFactory


class LossNoteClassFactory:
    """
    Fábrica responsável por instanciar e reconstruir objetos NotaPerda.
    Suporta dois cenários de perda:
      - Perda após devolução/venda: tipo_origem='DEVOLUCAO' (referencia NotaDevolucao / NotaVenda)
      - Perda do estoque: tipo_origem='ESTOQUE' (referencia NotaCompra)
    Para produtos compostos (que possuem receita), registra e reverte a perda dos ingredientes no estoque.
    """

    __lossNote: dict[int, NotaPerda] = {}

    @classmethod
    def fabricar(cls, id: int) -> NotaPerda:
        if id in cls.__lossNote:
            return cls.__lossNote[id]

        try:
            nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id)
            if not nota:
                raise ValueError(f"Erro ao fabricar nota de perda {id}: nota não encontrada no banco.")

            id_tipo = nota.get("id_tipoNota")
            if id_tipo not in (4, 5):
                raise ValueError(f"Erro ao fabricar nota de perda {id}: a nota no banco é do tipo {id_tipo} (esperado tipo 4 ou 5: PERDA).")

            # Define o tipo de origem com base no tipo da nota ou no vínculo
            id_nota_origem = nota.get("id_notaOrigem")
            tipo_origem = "DEVOLUCAO" if id_tipo == 4 else "ESTOQUE"

            # Tenta instanciar a nota de origem correspondente no banco
            if id_nota_origem and id_nota_origem > 0 and id_nota_origem != id:
                nota_orig_db = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_nota_origem)
                if nota_orig_db:
                    tipo_orig_id = nota_orig_db.get("id_tipoNota")
                    if tipo_orig_id == 1:
                        PurchaseNoteClassFactory.fabricar(id_nota_origem)
                    elif tipo_orig_id == 2:
                        SaleNoteClassFactory.fabricar(id_nota_origem)
                    elif tipo_orig_id == 3:
                        ReturnNoteClassFactory.fabricar(id_nota_origem)

            data_emissao = nota.get("data") or nota.get("data_vencimento")
            if isinstance(data_emissao, str):
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").date()
            elif data_emissao is None:
                data_emissao = date.today()

            notaPerda = NotaPerda(
                id=id,
                id_nota_origem=id_nota_origem,
                tipo_origem=tipo_origem,
                dataEmissao=data_emissao
            )

            if not cls.reconstruir_produtos(notaPerda, id):
                raise ValueError(f"Erro ao reconstruir produtos para a nota de perda {id}")

        except Exception as e:
            print(f"Erro ao fabricar nota de perda {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de perda {e}")
            return None

        if notaPerda and notaPerda.salvar():
            cls.__lossNote[id] = notaPerda
            return notaPerda
        return None

    @classmethod
    def reconstruir_produtos(cls, notaPerda: NotaPerda, id_nota: int) -> bool:
        """
        Auxilia na reconstrução dos produtos em uma nota de perda.
        Para produtos compostos (com receita), contabiliza a perda dos seus ingredientes.
        """
        try:
            itens = DB.SELECT.VW_FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)
            if not itens:
                itens = DB.SELECT.FLUXO_ESTOQUE_POR_NOTA.buscar(id_nota)

            if not itens:
                return False

            for ntp in itens:
                id_produto = ntp["id_produto"]
                quantidade = ntp["quantidade"]
                valor_unidario = ntp["valorUnidario"]

                # Fabricar a instância do produto
                produto = ProductClassFactory.testar_e_fabricar(id_produto)
                receita = produto.getDados().get("Receita")

                # Se o produto for composto (possuir receita): registra a perda dos ingredientes
                if receita and isinstance(receita, dict):
                    for id_ingrediente, qtd_por_unidade in receita.items():
                        qtd_perda_ingrediente = quantidade * qtd_por_unidade

                        ingrediente = ProductClassFactory.testar_e_fabricar(id_ingrediente)
                        cls._referenciar_nota_compra_ingrediente(id_ingrediente)
                        custo_ingrediente = cls._obter_custo_ingrediente(id_ingrediente)

                        ingrediente.insertPropertValue(valorUnidario=custo_ingrediente, quantidade=qtd_perda_ingrediente)
                        notaPerda.adicionarProduto(ingrediente)
                else:
                    # Produto simples: registra a perda do produto diretamente
                    produto.insertPropertValue(valorUnidario=valor_unidario, quantidade=quantidade)
                    notaPerda.adicionarProduto(produto)

            return True
        except Exception as e:
            print(f"Erro ao reconstruir produtos da nota de perda {id_nota}: {e}")
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
    np = LossNoteClassFactory.fabricar(573)
    if np:
        print("NotaPerda 7:\n", np.getDados())
