from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union


class Cliente:
    """
    Classe que representa um Cliente no sistema PDV.
    Baseada na estrutura do Fornecedor, gerencia notas de venda,
    devolução e perda (após vendas).
    """
    # Variáveis estáticas globais — acumulam os valores de TODOS os clientes
    __saldoTotalGlobal: int = 0
    __vendasTotalGlobal: int = 0
    __devolucaoTotalGlobal: int = 0
    __perdaTotalGlobal: int = 0
    __lucroTotalGlobal: int = 0

    def __init__(self, id: int, tipoCliente: Union[Pessoa, Empresa]):
        self.__id = id
        self.__origem = tipoCliente

        # Dicionários de notas deste cliente
        self.__notasVenda: dict[int, object] = {}
        self.__notasDevolucao: dict[int, object] = {}
        self.__notasPerda: dict[int, object] = {}

        # Totais individuais deste cliente
        self.__vendaTotal = 0
        self.__devolucaoTotal = 0
        self.__perdaTotal = 0
        self.__lucroTotal = 0

    # ========== NOTAS DE VENDA ==========

    def adicionarNotaVenda(self, nota) -> bool:
        """Adiciona uma nota de venda ao cliente."""
        try:
            dados = nota.getDados()
            idNota = dados["id"]

            if idNota in self.__notasVenda:
                print(f"Nota de venda com id {idNota} já existe neste cliente")
                return False

            self.__notasVenda[idNota] = nota
            return True

        except Exception as e:
            print(f" Erro ao adicionar nota de venda: {e}")
            return False

    def removerNotaVenda(self, idNotaVenda: int) -> bool:
        """Remove uma nota de venda pelo id."""
        if idNotaVenda not in self.__notasVenda:
            print(f"Nota de venda {idNotaVenda} não encontrada")
            return False

        del self.__notasVenda[idNotaVenda]
        return True

    def alterarNotaVenda(self, idNotaVenda: int, nota) -> bool:
        """Substitui uma nota existente por uma nova."""
        if idNotaVenda not in self.__notasVenda:
            print(f"Nota de venda {idNotaVenda} não encontrada para alteração")
            return False

        self.__notasVenda[idNotaVenda] = nota
        return True

    def getNotaVenda(self, idNotaVenda: int):
        """Retorna uma nota específica pelo id."""
        if idNotaVenda not in self.__notasVenda:
            return None
        return self.__notasVenda[idNotaVenda]

    def getNotasVenda(self) -> tuple:
        """Retorna todas as notas de venda deste cliente."""
        return tuple(self.__notasVenda.values())

    # ========== NOTAS DE DEVOLUÇÃO ==========

    def adicionarNotaDevolucao(self, nota) -> bool:
        """Adiciona uma nota de devolução ao cliente."""
        try:
            dados = nota.getDados()
            idNota = dados["id"]

            if idNota in self.__notasDevolucao:
                print(f"Nota de devolução com id {idNota} já existe neste cliente")
                return False

            self.__notasDevolucao[idNota] = nota
            return True

        except Exception as e:
            print(f" Erro ao adicionar nota de devolução: {e}")
            return False

    def removerNotaDevolucao(self, idNotaDevolucao: int) -> bool:
        if idNotaDevolucao not in self.__notasDevolucao:
            return False
        del self.__notasDevolucao[idNotaDevolucao]
        return True

    def getNotaDevolucao(self, idNotaDevolucao: int):
        if idNotaDevolucao not in self.__notasDevolucao:
            return None
        return self.__notasDevolucao[idNotaDevolucao]

    def getNotasDevolucao(self) -> tuple:
        return tuple(self.__notasDevolucao.values())

    # ========== NOTAS DE PERDA ==========

    def adicionarNotaPerda(self, nota) -> bool:
        """Adiciona uma nota de perda (após venda) ao cliente."""
        try:
            dados = nota.getDados()
            idNota = dados["id"]

            if idNota in self.__notasPerda:
                print(f"Nota de perda com id {idNota} já existe neste cliente")
                return False

            self.__notasPerda[idNota] = nota
            return True

        except Exception as e:
            print(f" Erro ao adicionar nota de perda: {e}")
            return False

    def removerNotaPerda(self, idNotaPerda: int) -> bool:
        if idNotaPerda not in self.__notasPerda:
            return False
        del self.__notasPerda[idNotaPerda]
        return True

    def getNotaPerda(self, idNotaPerda: int):
        if idNotaPerda not in self.__notasPerda:
            return None
        return self.__notasPerda[idNotaPerda]

    def getNotasPerda(self) -> tuple:
        return tuple(self.__notasPerda.values())

    # ========== CONTABILIDADE ==========

    def atualizarContabilidade(self, valorVenda: int = 0, valorDevolucao: int = 0,
                                valorPerda: int = 0, lucro: int = 0) -> bool:
        """
        Chamado pelo método salvar() das notas para atualizar os totais
        do cliente e os totais globais estáticos.
        Recebe valores em milhar (int) já calculados pela nota.
        """
        try:
            # Atualiza totais do cliente
            self.__vendaTotal += valorVenda
            self.__devolucaoTotal += valorDevolucao
            self.__perdaTotal += valorPerda
            self.__lucroTotal += lucro

            # Atualiza totais globais (estáticos)
            Cliente.__vendasTotalGlobal += valorVenda
            Cliente.__devolucaoTotalGlobal += valorDevolucao
            Cliente.__perdaTotalGlobal += valorPerda
            Cliente.__lucroTotalGlobal += lucro
            Cliente.__saldoTotalGlobal = (
                Cliente.__vendasTotalGlobal
                - Cliente.__devolucaoTotalGlobal
                - Cliente.__perdaTotalGlobal
            )

            return True

        except Exception as e:
            print(f" Erro ao atualizar contabilidade do cliente: {e}")
            return False

    def getDados(self) -> dict:
        """Retorna os dados do cliente e seus totais."""
        return {
            "id": self.__id,
            "origem": self.__origem.info(),
            "quantidadeNotasVenda": len(self.__notasVenda),
            "quantidadeNotasDevolucao": len(self.__notasDevolucao),
            "quantidadeNotasPerda": len(self.__notasPerda),
            "vendaTotal": MoedaReal.parseMilharParaReais(self.__vendaTotal),
            "devolucaoTotal": MoedaReal.parseMilharParaReais(self.__devolucaoTotal),
            "perdaTotal": MoedaReal.parseMilharParaReais(self.__perdaTotal),
            "lucroTotal": MoedaReal.parseMilharParaReais(self.__lucroTotal),
        }

    @classmethod
    def getDadosGlobais(cls) -> dict:
        """Retorna os totais globais de todos os clientes."""
        return {
            "saldoTotalGlobal": MoedaReal.parseMilharParaReais(cls.__saldoTotalGlobal),
            "vendasTotalGlobal": MoedaReal.parseMilharParaReais(cls.__vendasTotalGlobal),
            "devolucaoTotalGlobal": MoedaReal.parseMilharParaReais(cls.__devolucaoTotalGlobal),
            "perdaTotalGlobal": MoedaReal.parseMilharParaReais(cls.__perdaTotalGlobal),
            "lucroTotalGlobal": MoedaReal.parseMilharParaReais(cls.__lucroTotalGlobal),
        }
