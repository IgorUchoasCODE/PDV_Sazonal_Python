from datetime import date
from typing import Union, Dict, Any, Optional
from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.financeiro.Real import MoedaReal
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.notaCompra import NotaCompra
from br.com.pdv.src.financeiro.notaVenda import NotaVenda
from br.com.pdv.src.financeiro.notaDevolucao import NotaDevolucao
from br.com.pdv.src.financeiro.notaPerda import NotaPerda
from br.com.pdv.src.financeiro.notaCompensacao import NotaCompensacao

# Tipo estendido das notas de fluxo aceitas
TipoNotaEstoque = Union[NotaCompra, NotaVenda, NotaDevolucao, NotaPerda, NotaCompensacao]


class NotaPagamento(ComportamentoNota):
    """
    Nota de Pagamento — O Elo de Ligação Contábil do Sistema PDV Sazonal.
    
    Representa os registros de liquidação/pagamento (fluxoPagamentoNotas) e consolida
    a rastreabilidade entre todas as categorias de notas:
      - NotaCompra (Aquisições/Saída de Caixa)
      - NotaVenda (Vendas/Entrada de Caixa)
      - NotaDevolucao (Estornos aos Clientes)
      - NotaPerda (Baixas Contábeis/Prejuízos)
      - NotaCompensacao (Reposições de Estoque sem custo)
    
    Também se conecta com as Condições Sazonais (snapshot_sazonal) para análises
    de impacto de clima, chuvas e eventos nos fluxos financeiros.
    """

    FORMAS_PAGAMENTO_MAP = {
        1: "DINHEIRO",
        2: "PIX",
        3: "CARTÃO DE DÉBITO",
        4: "CARTÃO DE CRÉDITO",
        5: "TRANSFERÊNCIA",
        6: "CHEQUE"
    }

    def __init__(self,
                 id: int,
                 id_fluxo_nota: int,
                 id_forma_pagamento: int = 1,
                 valor: float = 0.0,
                 data_pagamento: date = date.today(),
                 nota_referenciada: Optional[TipoNotaEstoque] = None,
                 snapshot_sazonal: Optional[Dict[str, Any]] = None):
        """
        Inicializa a NotaPagamento.
        """
        try:
            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")
            if int(id_fluxo_nota) <= 0:
                raise ValueError("O id_fluxo_nota deve ser maior que zero")
            if float(valor) < 0:
                raise ValueError("O valor do pagamento não pode ser negativo")
        except ValueError as e:
            print(f" Erro na inicialização da NotaPagamento: {e}")
            return

        self.__I = id
        self.__idFluxoNota = id_fluxo_nota
        self.__idFormaPagamento = id_forma_pagamento
        self.__formaPagamentoDesc = self.FORMAS_PAGAMENTO_MAP.get(id_forma_pagamento, "DINHEIRO")
        self.__valor = float(valor)
        self.__dataPagamento = data_pagamento
        self.__notaReferenciada = nota_referenciada
        self.__snapshotSazonal = snapshot_sazonal

        # Dicionário interno secundário de produtos caso adicionados diretamente
        self.__produtosInternos: dict[str, Produto] = {}

        # Lista de pagamentos encadeados (ex: pagamentos de ingredientes de um produto composto)
        self.__pagamentosVinculados: list['NotaPagamento'] = []

        self.__salvo = False

    # -------------------------------------------------------------------------
    # Getters e Propriedades Contábeis
    # -------------------------------------------------------------------------
    def getId(self) -> int:
        return self.__I

    def getIdFluxoNota(self) -> int:
        return self.__idFluxoNota

    def getValor(self) -> float:
        return self.__valor

    def getFormaPagamento(self) -> str:
        return self.__formaPagamentoDesc

    def getIdFormaPagamento(self) -> int:
        return self.__idFormaPagamento

    def getDataPagamento(self) -> date:
        return self.__dataPagamento

    def getNotaReferenciada(self) -> Optional[TipoNotaEstoque]:
        return self.__notaReferenciada

    def getSnapshotSazonal(self) -> Optional[Dict[str, Any]]:
        return self.__snapshotSazonal

    def vincularPagamentoFilho(self, pagamento_filho: 'NotaPagamento'):
        """Vincula um pagamento de ingrediente/item filho a esta transação."""
        if isinstance(pagamento_filho, NotaPagamento):
            self.__pagamentosVinculados.append(pagamento_filho)

    def setSnapshotSazonal(self, snapshot: Dict[str, Any]):
        """Define o snapshot sazonal associado a este pagamento."""
        self.__snapshotSazonal = snapshot

    def getTipoFluxoContabil(self) -> str:
        """
        Determina o sentido do fluxo contábil baseado no tipo de nota vinculada.
        """
        if isinstance(self.__notaReferenciada, NotaVenda):
            return "ENTRADA_CAIXA"
        elif isinstance(self.__notaReferenciada, NotaCompra):
            return "SAIDA_CAIXA"
        elif isinstance(self.__notaReferenciada, NotaDevolucao):
            return "REEMBOLSO_DEVOLUCAO"
        elif isinstance(self.__notaReferenciada, NotaPerda):
            return "BAIXA_PERDA"
        elif isinstance(self.__notaReferenciada, NotaCompensacao):
            return "REPOSICAO_COMPENSACAO"
        return "INDEFINIDO"

    # -------------------------------------------------------------------------
    # Métodos do ComportamentoNota
    # -------------------------------------------------------------------------
    def adicionarProduto(self, produto: Produto) -> bool:
        if self.__notaReferenciada and hasattr(self.__notaReferenciada, "adicionarProduto"):
            return self.__notaReferenciada.adicionarProduto(produto)
        if isinstance(produto, Produto):
            self.__produtosInternos[str(produto.getDados().get("id"))] = produto
            return True
        return False

    def removerProduto(self, idProduto: int) -> bool:
        if self.__notaReferenciada and hasattr(self.__notaReferenciada, "removerProduto"):
            return self.__notaReferenciada.removerProduto(idProduto)
        idp = str(idProduto)
        if idp in self.__produtosInternos:
            del self.__produtosInternos[idp]
            return True
        return False

    def alterarProduto(self, idProduto: int, produto: Produto) -> bool:
        if self.__notaReferenciada and hasattr(self.__notaReferenciada, "alterarProduto"):
            return self.__notaReferenciada.alterarProduto(idProduto, produto)
        idp = str(idProduto)
        if idp in self.__produtosInternos:
            self.__produtosInternos[idp] = produto
            return True
        return False

    def getProdutos(self) -> tuple[Produto]:
        if self.__notaReferenciada and hasattr(self.__notaReferenciada, "getProdutos"):
            return self.__notaReferenciada.getProdutos()
        return tuple(self.__produtosInternos.values())

    def getDados(self) -> dict:
        dados_nota_ref = self.__notaReferenciada.getDados() if self.__notaReferenciada else None

        return {
            "id": self.__I,
            "id_fluxo_nota": self.__idFluxoNota,
            "tipoFluxoContabil": self.getTipoFluxoContabil(),
            "idFormaPagamento": self.__idFormaPagamento,
            "formaPagamento": self.__formaPagamentoDesc,
            "valor": round(self.__valor, 2),
            "dataPagamento": self.__dataPagamento,
            "notaEstoqueReferenciada": dados_nota_ref,
            "snapshotSazonal": self.__snapshotSazonal,
            "pagamentosVinculados": [p.getDados() for p in self.__pagamentosVinculados],
            "salvo": self.__salvo
        }

    def salvar(self) -> bool:
        self.__salvo = True
        return True
