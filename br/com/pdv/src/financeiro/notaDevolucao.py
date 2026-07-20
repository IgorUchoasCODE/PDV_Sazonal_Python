from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.pessoa.cliente import Cliente
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.memory.idClassFactory import IdClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union
from datetime import date


class NotaDevolucao(ComportamentoNota):
    """
    Nota de Devolução — representa o retorno de produtos vendidos.
    Obrigatoriamente cita a NotaVenda de origem (id_notaOrigem).
    Reverte os produtos devolvidos ao estoque e recalcula o lucro.
    """

    def __init__(self, id: int,
                 clienteFornecedor: Union[Cliente, Pessoa],
                 id_nota_venda_origem: int = None,
                 dataEmissao: date = date.today(),
                 dataVencimento: date = None):
        try:
            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")

            if clienteFornecedor is None:
                raise ValueError("O cliente deve ser informado")

            if id_nota_venda_origem is None:
                raise ValueError("A nota de venda de origem deve ser informada para devolução")

            if not isinstance(dataEmissao, date):
                raise ValueError("A data de emissão deve ser uma instância de date")

            if not isinstance(dataVencimento, date) and dataVencimento is not None:
                raise ValueError("A data de vencimento deve ser uma instância de date")

        except ValueError as e:
            print(f" Erro na inicialização do objeto NotaDevolucao: {e}")
            return

        # Propriedades de identificação
        self.__I = id
        self.__C = clienteFornecedor
        self.__notaVendaOrigem = id_nota_venda_origem
        self.__dataE = dataEmissao
        self.__dataV = dataVencimento

        # Dicionário de produtos devolvidos
        self.__produtos: dict[str, Produto] = {}

        # Propriedades de valor
        self.__valorTotalDevolucao = 0
        self.__custoRevertido = 0

        # Flag de salvamento
        self.__salvo = False

    def adicionarProduto(self, produto: Produto) -> bool:
        """Adiciona um produto à nota de devolução."""
        p = produto
        lp = self.__produtos

        try:
            if not isinstance(p, Produto):
                raise ValueError("O produto deve ser uma instância de Produto")

            key = IdClassFactory.gerar_id_produto_nota(lp, p.getDados(), 3)

        except ValueError as e:
            print(f" Erro ao adicionar o produto na devolução: {e}")
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
            "tipo": "DEVOLUÇÃO",
            "cliente": self.__C.getDados() if hasattr(self.__C, 'getDados') else self.__C.info(),
            "notaVendaOrigem": self.__notaVendaOrigem,
            "dataEmissao": self.__dataE,
            "dataVencimento": self.__dataV,
            "produtos": {k: p.getDados(True) for k, p in self.__produtos.items()},
            "valorTotalDevolucao": MoedaReal.parseMilharParaReais(self.__valorTotalDevolucao),
            "custoRevertido": MoedaReal.parseMilharParaReais(self.__custoRevertido),
            "salvo": self.__salvo
        }

    def __recalcularTotais(self) -> bool:
        self.__valorTotalDevolucao = 0
        self.__custoRevertido = 0

        for key, p in self.__produtos.items():
            dados = p.getDados(f=False)
            self.__valorTotalDevolucao += dados.get("valorTotalVendas", 0) or 0
            self.__custoRevertido += dados.get("ValorTotal", 0) or 0

        return True

    def salvar(self) -> bool:
        """
        Salva a nota de devolução:
        1. Recalcula totais
        2. Atualiza contabilidade do cliente (subtrai devolução)
        3. Marca como salva
        """
        try:
            self.__recalcularTotais()

            if isinstance(self.__C, Cliente):
                self.__C.atualizarContabilidade(
                    valorDevolucao=self.__valorTotalDevolucao
                )

            self.__salvo = True
            return True

        except Exception as e:
            print(f" Erro ao salvar a nota de devolução: {e}")
            return False
