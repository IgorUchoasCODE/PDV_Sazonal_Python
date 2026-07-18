
from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.pessoa.cliente import Cliente
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.produto.produto import Produto
from typing import Union
from datetime import date

class NotaVenda(ComportamentoNota):
    def __init__(self,id:int,
                clienteFornecedor: Union[Cliente, Pessoa], 
                dataEmissao:date=date.today(),
                dataVencimento:date=None):
        self.__I = id
        self.__E = clienteFornecedor
        self.__dataE = dataEmissao
        self.__dataV = dataVencimento
        self.__produtos: list[Produto] = []


    
    def adicionarProduto(self, produto:Produto)-> bool:
        pass

    
    def removerProduto(self, idProduto:int)-> bool:
        pass

    
    def alterarProduto(self, idProduto:int, produto:Produto)-> bool:
        pass

    
    def getProdutos(self) -> tuple[Produto]:
        pass
   
    
    def getDados(self)-> dict:
        pass 
