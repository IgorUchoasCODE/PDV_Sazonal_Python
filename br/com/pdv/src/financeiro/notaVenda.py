from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.pessoa.cliente import Cliente
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.memory.idClassFactory import IdClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union
from datetime import date


class NotaVenda(ComportamentoNota):
    """
    Nota de Venda — representa uma transação de saída de produtos para um cliente.
    Cada produto vendido mantém vínculo com sua nota de compra de origem.
    """

    def __init__(self, id: int,
                 clienteFornecedor: Union[Cliente, Pessoa],
                 dataEmissao: date = date.today(),
                 dataVencimento: date = None):
        try:
            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")

            if clienteFornecedor is None:
                raise ValueError("O cliente deve ser informado")

            if not isinstance(clienteFornecedor, (Cliente, Pessoa)):
                raise ValueError("O cliente deve ser uma instância de Cliente ou Pessoa")

            if not isinstance(dataEmissao, date):
                raise ValueError("A data de emissão deve ser uma instância de date")

            if not isinstance(dataVencimento, date) and dataVencimento is not None:
                raise ValueError("A data de vencimento deve ser uma instância de date")

        except ValueError as e:
            print(f" Erro na inicialização do objeto NotaVenda: {e}")
            return

        # Propriedades de identificação
        self.__I = id
        self.__C = clienteFornecedor
        self.__dataE = dataEmissao
        self.__dataV = dataVencimento

        # Dicionário de produtos vendidos {id_composto: Produto}
        self.__produtos: dict[str, Produto] = {}

        # Vínculo produto → nota de origem {id_composto_venda: id_nota_compra}
        self.__origemProdutos: dict[str, int] = {}

        # Propriedades de valor da nota
        self.__valorTotalVenda = 0
        self.__custoTotal = 0
        self.__lucroTotal = 0

        # Flag de salvamento
        self.__salvo = False

    def adicionarProduto(self, produto: Produto, id_nota_origem: Union[int, dict] = None) -> bool:
        """
        Adiciona um produto à nota de venda.
        id_nota_origem: ID da nota de compra ou dict de IDs para ingredientes de produtos compostos.
        """
        p = produto
        lp = self.__produtos

        try:
            if not isinstance(p, Produto):
                raise ValueError("O produto deve ser uma instância de Produto")

            if "Receita" in p.getDados().keys() and "valorTotalVendas" not in p.getDados().keys():
                raise ValueError("Produto composto não pode ser vendido diretamente sem definir valores de venda")

            key = IdClassFactory.gerar_id_produto_nota(lp, p.getDados(), 2)

        except ValueError as e:
            print(f" Erro ao adicionar o produto na venda: {e}")
            return False

        lp[key] = p
        if id_nota_origem is not None:
            self.__origemProdutos[key] = id_nota_origem
        self.__salvo = False
        return True

    def removerProduto(self, idProduto: int) -> bool:
        idp = str(idProduto) if not isinstance(idProduto, str) else idProduto
        lp = self.__produtos

        if idp not in lp.keys():
            return False

        del lp[idp]
        self.__origemProdutos.pop(idp, None)
        self.__salvo = False
        return True

    def alterarProduto(self, idProduto: int, produto: Produto) -> bool:
        idp = str(idProduto) if not isinstance(idProduto, str) else idProduto
        lp = self.__produtos

        if idp not in lp.keys():
            print(f"Produto '{idp}' não encontrado na nota de venda.")
            return False

        lp[idp] = produto
        self.__salvo = False
        return True

    def getProdutos(self) -> tuple[Produto]:
        return tuple(self.__produtos.values())

    def getDados(self) -> dict:
        return {
            "id": self.__I,
            "cliente": self.__C.getDados() if hasattr(self.__C, 'getDados') else self.__C.info(),
            "dataEmissao": self.__dataE,
            "dataVencimento": self.__dataV,
            "produtos": {k: p.getDados(True) for k, p in self.__produtos.items()},
            "origemProdutos": dict(self.__origemProdutos),
            "valorTotalVenda": MoedaReal.parseMilharParaReais(self.__valorTotalVenda),
            "custoTotal": MoedaReal.parseMilharParaReais(self.__custoTotal),
            "lucroTotal": MoedaReal.parseMilharParaReais(self.__lucroTotal),
            "salvo": self.__salvo
        }

    def __recalcularTotais(self) -> bool:
        """Recalcula todos os totais a partir dos produtos."""
        self.__valorTotalVenda = 0
        self.__custoTotal = 0
        self.__lucroTotal = 0

        for key, p in self.__produtos.items():
            dados = p.getDados(f=False)
            self.__valorTotalVenda += dados.get("valorTotalVendas", 0) or 0
            self.__custoTotal += dados.get("ValorTotal", 0) or 0
            self.__lucroTotal += dados.get("valorTotalLucro", 0) or 0

        return True

    def salvar(self) -> bool:
        """
        Salva a nota de venda:
        1. Recalcula os totais
        2. Atualiza contabilidade do cliente
        3. Marca como salva
        """
        try:
            self.__recalcularTotais()

            if isinstance(self.__C, Cliente):
                self.__C.atualizarContabilidade(
                    valorVenda=self.__valorTotalVenda,
                    lucro=self.__lucroTotal
                )

            self.__salvo = True
            return True

        except Exception as e:
            print(f" Erro ao salvar a nota de venda: {e}")
            return False
