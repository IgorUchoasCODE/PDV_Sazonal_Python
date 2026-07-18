from br.com.pdv.src.financeiro.notaVenda import NotaVenda
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from typing import Union

class Cliente:
    __saldoTotalGlobal : int = 0
    __vendasTotalGlobal : int = 0
    __lucroTotalGlobal : int = 0
    __notasVenda:dict[int, list[NotaVenda]] = {}

    def __init__(self, id:int, tipoClinete: Union[Pessoa, Empresa]):
        pass

    def adicionarNotaVenda(self, nota:NotaVenda)->bool:
        pass
    
    def removerNotaVenda(self, idNotaVenda:int)->bool:
        pass
    
    def alterarNotaVenda(self, idNotaVenda:int, nota:NotaVenda)->bool:
        pass
    
    def getNotaVenda(self, idNotaVenda:int)->NotaVenda:
        pass
    
    def getNotasVenda(self)->tuple[NotaVenda]:
        pass
    
    def getSaldoTotalGlobal(self)->int:
        pass
    
    def getVendasTotalGlobal(self)->int:
        pass
    
    def getLucroTotalGlobal(self)->int:
        pass    

        
       
    



