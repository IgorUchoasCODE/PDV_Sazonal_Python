from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.memory.idClassFactory import IdClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.Real import MoedaReal
from datetime import date


class NotaCompensacao(ComportamentoNota):
    """
    Nota de Compensação — registra reposição/compensação referente a perdas.
    Cita as notas de perda independentemente (id_notaOrigem → perda).
    Uma compensação pode cobrir uma perda específica.
    """

    def __init__(self, id: int,
                 id_nota_perda_origem: int = None,
                 dataEmissao: date = date.today(),
                 dataVencimento: date = None):
        """
        Args:
            id: ID da nota de compensação
            id_nota_perda_origem: ID da nota de perda que está sendo compensada
            dataEmissao: Data da compensação
            dataVencimento: Data de vencimento (se aplicável)
        """
        try:
            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")

            if id_nota_perda_origem is None:
                raise ValueError("A nota de perda de origem deve ser informada")

        except ValueError as e:
            print(f" Erro na inicialização do objeto NotaCompensacao: {e}")
            return

        self.__I = id
        self.__notaPerdaOrigem = id_nota_perda_origem
        self.__dataE = dataEmissao
        self.__dataV = dataVencimento

        # Dicionário de produtos compensados
        self.__produtos: dict[str, Produto] = {}

        # Propriedades de valor
        self.__valorTotalCompensacao = 0

        # Flag
        self.__salvo = False

    def adicionarProduto(self, produto: Produto) -> bool:
        """Adiciona um produto à nota de compensação."""
        p = produto
        lp = self.__produtos

        try:
            if not isinstance(p, Produto):
                raise ValueError("O produto deve ser uma instância de Produto")

            key = IdClassFactory.gerar_id_produto_nota(lp, p.getDados(), 5)

        except ValueError as e:
            print(f" Erro ao adicionar o produto na compensação: {e}")
            return False

        lp[key] = p
        self.__salvo = False
        return True

    def removerProduto(self, idProduto: int) -> bool:
        idp = str(idProduto) if not isinstance(idProduto, str) else idProduto
        if idp not in self.__produtos:
            return False
        del self.__produtos[idp]
        self.__salvo = False
        return True

    def alterarProduto(self, idProduto: int, produto: Produto) -> bool:
        idp = str(idProduto) if not isinstance(idProduto, str) else idProduto
        if idp not in self.__produtos:
            return False
        self.__produtos[idp] = produto
        self.__salvo = False
        return True

    def getProdutos(self) -> tuple[Produto]:
        return tuple(self.__produtos.values())

    def getDados(self) -> dict:
        return {
            "id": self.__I,
            "tipo": "COMPENSAÇÃO",
            "notaPerdaOrigem": self.__notaPerdaOrigem,
            "dataEmissao": self.__dataE,
            "dataVencimento": self.__dataV,
            "produtos": {k: p.getDados(True) for k, p in self.__produtos.items()},
            "valorTotalCompensacao": MoedaReal.parseMilharParaReais(self.__valorTotalCompensacao),
            "salvo": self.__salvo
        }

    def __recalcularTotais(self) -> bool:
        self.__valorTotalCompensacao = 0

        for key, p in self.__produtos.items():
            dados = p.getDados(f=False)
            self.__valorTotalCompensacao += dados.get("ValorTotal", 0) or 0

        return True

    def salvar(self) -> bool:
        """
        Salva a nota de compensação:
        1. Recalcula o valor total
        2. Marca como salva
        """
        try:
            self.__recalcularTotais()
            self.__salvo = True
            return True

        except Exception as e:
            print(f" Erro ao salvar a nota de compensação: {e}")
            return False
