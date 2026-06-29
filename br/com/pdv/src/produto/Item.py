from abc import ABC, abstractmethod
from financeiro.Real  import Financeiro
from UnidadeMedida import UnidadeMedida
from datetime import date



class ComportamentoEstoque(ABC):
   
    @abstractmethod
    def saida(self, quantidade: int):
        pass

    def entrada(self, quantidade: int):
        pass

    @abstractmethod
    def atualizar(self):
        pass

    @abstractmethod
    def vizualizar(self) -> dict:
        pass



class Item(ComportamentoEstoque):

    def __init__(self, medida:UnidadeMedida, real:Financeiro, diasDurabilidade:int):
        self.__M = medida;
        self.__D = diasDurabilidade;
        self.__R = real;

        self.__estoque:int      = 0;
        self.__valorUni:int     = 0;
        self.__valorEstoque:int = 0;


    def saida(self, quantidade):
        return super().saida(quantidade)
    

    def entrada(self, quantidade:float, valorUnitario:float):

        self.__estoque = int(self.__M.parseInt(quantidade))
        self.__V = valorUnitario
        


    def atualizar(self):
        return super().atualizar()
    
    def vizualizar(self):
        return {
            "M" : self.__M.getDescription(),
            "E" : self.__estoque,
            "V" : self.__V
        }
    


i = Item(UnidadeMedida.kG, Financeiro.Real,7)
i.entrada(0.001,10)
print(i.vizualizar())
f = Financeiro.Real

print(f.getNome())


