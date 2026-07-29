from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.memory.idClassFactory import IdClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.Real import MoedaReal
from datetime import date


class NotaPerda(ComportamentoNota):
    """
    Nota de Perda — representa a perda de produtos.
    Dois cenários:
      - Perda após venda: cita a NotaDevolucao de origem
      - Perda do estoque: cita a NotaCompra de origem
    Remove produtos do estoque sem gerar receita.
    """

    def __init__(self, id: int,
                 id_nota_origem: int = None,
                 tipo_origem: str = "ESTOQUE",
                 dataEmissao: date = date.today()):
        """
        Args:
            id: ID da nota de perda
            id_nota_origem: ID da nota de origem (devolução ou compra)
            tipo_origem: 'DEVOLUCAO' se a perda é após venda, 'ESTOQUE' se é do estoque direto
            dataEmissao: Data da perda
        """
        try:
            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")

            if tipo_origem not in ("DEVOLUCAO", "ESTOQUE"):
                raise ValueError("tipo_origem deve ser 'DEVOLUCAO' ou 'ESTOQUE'")

        except ValueError as e:
            print(f" Erro na inicialização do objeto NotaPerda: {e}")
            return

        self.__I = id
        self.__notaOrigem = id_nota_origem
        self.__tipoOrigem = tipo_origem
        self.__dataE = dataEmissao

        # Dicionário de produtos perdidos
        self.__produtos: dict[str, Produto] = {}

        # Propriedades de valor
        self.__valorTotalPerda = 0

        # Flag
        self.__salvo = False

    def adicionarProduto(self, produto: Produto) -> bool:
        """Adiciona um produto à nota de perda."""
        p = produto
        lp = self.__produtos

        try:
            if not isinstance(p, Produto):
                raise ValueError("O produto deve ser uma instância de Produto")

            key = IdClassFactory.gerar_id_produto_nota(lp, p.getDados(), 4)

        except ValueError as e:
            print(f" Erro ao adicionar o produto na perda: {e}")
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
            "tipo": "PERDA",
            "notaOrigem": self.__notaOrigem,
            "tipoOrigem": self.__tipoOrigem,
            "dataEmissao": self.__dataE,
            "produtos": {k: p.getDados(True) for k, p in self.__produtos.items()},
            "valorTotalPerda": MoedaReal.parseMilharParaReais(self.__valorTotalPerda),
            "salvo": self.__salvo
        }

    def __recalcularTotais(self) -> bool:
        self.__valorTotalPerda = 0

        for key, p in self.__produtos.items():
            dados = p.getDados(f=False)
            # Perda é calculada pelo custo (ValorTotal), não pelo preço de venda
            self.__valorTotalPerda += dados.get("ValorTotal", 0) or 0

        return True

    def salvar(self) -> bool:
        """
        Salva a nota de perda:
        1. Recalcula o valor total da perda
        2. Marca como salva
        """
        try:
            self.__recalcularTotais()
            self.__salvo = True
            return True

        except Exception as e:
            print(f" Erro ao salvar a nota de perda: {e}")
            return False
