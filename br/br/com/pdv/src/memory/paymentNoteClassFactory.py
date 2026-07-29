import sqlite3
from datetime import datetime, date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaPagamento import NotaPagamento
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory
from br.com.pdv.src.memory.saleNoteClassFactory import SaleNoteClassFactory
from br.com.pdv.src.memory.returnNoteClassFactory import ReturnNoteClassFactory
from br.com.pdv.src.memory.lossNoteClassFactory import LossNoteClassFactory
from br.com.pdv.src.memory.compensationNoteClassFactory import CompensationNoteClassFactory


class PaymentNoteClassFactory:
    """
    Fábrica responsável por fabricar e instanciar objetos NotaPagamento.
    Atua como o ELO CONTÁBIL que une todas as notas do sistema:
      - NotaCompra
      - NotaVenda
      - NotaDevolucao
      - NotaPerda
      - NotaCompensacao
    E vincula os registros de snapshot_sazonal e liquidação contábil.
    """

    __paymentNote: dict[int, NotaPagamento] = {}

    @classmethod
    def fabricar(cls, id_pagamento: int) -> NotaPagamento:
        if id_pagamento in cls.__paymentNote:
            return cls.__paymentNote[id_pagamento]

        try:
            # Busca os dados do pagamento no fluxoPagamentoNotas
            pag_db = DB.SELECT.VW_PAGAMENTOS_NOTA.buscar_um(id_pagamento) if hasattr(DB.SELECT, "VW_PAGAMENTOS_NOTA") else None
            if not pag_db:
                # Query direta fallback caso necessário
                from br.com.pdv.src.BDD.queryEnum import QueryBase
                query = "SELECT * FROM fluxoPagamentoNotas WHERE id = ?"
                conn = sqlite3.connect('databaseSazonalizei.db')
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(query, (id_pagamento,))
                pag_db = dict(cur.fetchone()) if cur.rowcount != 0 else None
                conn.close()

            if not pag_db:
                raise ValueError(f"Erro ao fabricar nota de pagamento {id_pagamento}: pagamento não encontrado no banco.")

            id_fluxo_nota = pag_db["id_fluxo_nota"]
            id_forma_pagamento = pag_db["id_forma_pagamento"]
            valor = pag_db["valor"]

            data_pagamento = pag_db.get("data_pagamento")
            if isinstance(data_pagamento, str):
                data_pagamento = datetime.strptime(data_pagamento, "%Y-%m-%d").date()
            elif data_pagamento is None:
                data_pagamento = date.today()

            # Identifica o tipo de nota de estoque associada
            nota_hdr = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_fluxo_nota)
            nota_referenciada = None
            if nota_hdr:
                id_tipo_nota = nota_hdr.get("id_tipoNota")
                if id_tipo_nota == 1:
                    nota_referenciada = PurchaseNoteClassFactory.fabricar(id_fluxo_nota)
                elif id_tipo_nota == 2:
                    nota_referenciada = SaleNoteClassFactory.fabricar(id_fluxo_nota)
                elif id_tipo_nota == 3:
                    nota_referenciada = ReturnNoteClassFactory.fabricar(id_fluxo_nota)
                elif id_tipo_nota == 4:
                    nota_referenciada = LossNoteClassFactory.fabricar(id_fluxo_nota)
                elif id_tipo_nota == 5:
                    nota_referenciada = CompensationNoteClassFactory.fabricar(id_fluxo_nota)
                    if not nota_referenciada:
                        nota_referenciada = LossNoteClassFactory.fabricar(id_fluxo_nota)

            # Busca o snapshot sazonal atrelado a este fluxo de nota
            snapshot_db = DB.SELECT.SNAPSHOT_POR_NOTA.buscar_um(id_fluxo_nota)
            if snapshot_db:
                snapshot = dict(snapshot_db)
                snapshot["registrado"] = True
            else:
                snapshot = {
                    "registrado": False,
                    "temperatura_atual": "N/A",
                    "indicador_clima": "Estável",
                    "indicador_chuva": "Sem registro",
                    "indicador_rio": "Normal",
                    "detalhe": "Sem snapshot sazonal gravado para esta nota"
                }

            notaPagamento = NotaPagamento(
                id=id_pagamento,
                id_fluxo_nota=id_fluxo_nota,
                id_forma_pagamento=id_forma_pagamento,
                valor=valor,
                data_pagamento=data_pagamento,
                nota_referenciada=nota_referenciada,
                snapshot_sazonal=snapshot
            )

            # Reconstruir elos contábeis de pagamentos filhos (ingredientes/devoluções/perdas vinculadas)
            cls._reconstruir_elo_pagamentos_filhos(notaPagamento, id_fluxo_nota, ids_visitados={id_pagamento})

        except Exception as e:
            print(f"Erro ao fabricar nota de pagamento {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de pagamento {e}")
            return None

        if notaPagamento and notaPagamento.salvar():
            cls.__paymentNote[id_pagamento] = notaPagamento
            return notaPagamento
        return None

    @classmethod
    def fabricar_por_nota_estoque(cls, id_fluxo_nota: int) -> NotaPagamento:
        """
        Busca e fabrica a NotaPagamento associada a um id_fluxo_nota.
        """
        pag = DB.SELECT.FLUXO_PAGAMENTO_POR_NOTA.buscar(id_fluxo_nota)
        if pag and len(pag) > 0:
            id_pag = pag[0]["id"]
            return cls.fabricar(id_pag)
        return None

    @classmethod
    def _reconstruir_elo_pagamentos_filhos(cls, notaPagamento: NotaPagamento, id_fluxo_nota: int, ids_visitados: set = None):
        """
        Busca pagamentos das notas filhas (ex: ingredientes de produtos compostos, notas de devolução ou perdas
        vinculadas) e conecta à NotaPagamento principal.
        """
        if ids_visitados is None:
            ids_visitados = set()

        try:
            # Busca notas filhas que citam id_fluxo_nota como id_notaOrigem
            notas_filhas = DB.SELECT.FLUXO_NOTA_ESTOQUE_TODOS.buscar()
            if notas_filhas:
                for nf in notas_filhas:
                    if nf.get("id_notaOrigem") == id_fluxo_nota and nf["id"] != id_fluxo_nota:
                        id_filha = nf["id"]
                        pags_filhos = DB.SELECT.FLUXO_PAGAMENTO_POR_NOTA.buscar(id_filha)
                        if pags_filhos:
                            for pf in pags_filhos:
                                id_pag_filho = pf["id"]
                                if id_pag_filho not in ids_visitados:
                                    ids_visitados.add(id_pag_filho)
                                    pag_obj = cls.fabricar(id_pag_filho)
                                    if pag_obj:
                                        notaPagamento.vincularPagamentoFilho(pag_obj)
        except Exception as e:
            print(f"Erro ao vincular elos de pagamentos filhos: {e}")



if __name__ == "__main__":
    py = PaymentNoteClassFactory.fabricar(229)
    if py:
        print(py.getDados())