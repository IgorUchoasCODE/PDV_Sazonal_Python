from abc import ABC, abstractmethod
from br.com.pdv.src.produto.produto import Produto


class ComportamentoNota(ABC):

    @abstractmethod
    def adicionarProduto(self, produto:Produto, quantidade, valorProPOr):
        pass
    
    @abstractmethod
    def adicionarPagamento(self):
        pass
        