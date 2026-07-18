from abc import ABC, abstractmethod
from br.com.pdv.src.produto.produto import Produto
from typing import Union
from datetime import date

class ComportamentoNota(ABC):

    @abstractmethod
    def __init__(self, id:int,clienteFornecedor, dataEmissao:date=date.today(),dataVencimento:date=None):
        pass

    @abstractmethod
    def adicionarProduto(self, produto:Produto)-> bool:
        pass

    @abstractmethod
    def removerProduto(self, idProduto:int)-> bool:
        pass

    @abstractmethod
    def alterarProduto(self, idProduto:int, produto:Produto)-> bool:
        pass

    @abstractmethod
    def getProdutos(self) -> tuple[Produto]:
        pass
   
    @abstractmethod
    def getDados(self)-> dict:
        pass

    @abstractmethod
    def salvar(self)-> bool:
        pass



    
   
        