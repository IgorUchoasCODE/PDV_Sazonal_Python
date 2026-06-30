from abc import ABC, abstractmethod
from br.com.pdv.src.financeiro.Real import MoedaReal
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida




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

    def __init__(self, medida:UnidadeMedida, real:MoedaReal, diasDurabilidade:int):
        self.__M = medida;
        self.__D = diasDurabilidade;
        self.__R = real;

        self.__estoque  = 0;
        self.__valorPorUn = 0;
        self.__valorEstoque = 0;

    def entrada(self, quantidade:float, valorUnitario:float):

        self.__estoque    = self.__M.parseInt(quantidade)
        self.__V          = self.__R.parseCentavosPorMilhar(valorUnitario)
        self.__valorEstoque = self.__R.calculo_PQV_T(self.__M.getMultInt(), self.__estoque, self.__V)
        self.__valorPorUn = self.__R.calculo_QeVp_Vu(self.__M.getMultInt(),self.__V)
        

    def saida(self, quantidade,valorVenda) -> int:
        q = self.__M.parseInt(quantidade)
        v = self.__R.parseCentavosPorMilhar(valorVenda)
        print(v)
        if self.__estoque < q :
            raise ValueError(f"Estoque insuficiente{self.__estoque}")
        
        self.__estoque -= q
        self.__valorEstoque -= q * self.__valorPorUn
        
        return self.__R.calculo_QpQsVuVv_L(q,self.__valorPorUn, v)
        

    def atualizar(self):
        return super().atualizar()
    
    def vizualizar(self):
        return {
            "M" : self.__M.getDescription(),
            "E" : self.__estoque,
            "V" : self.__V,
            "U" : self.__valorPorUn,
            "T": self.__valorEstoque

        }
    




i = Item(UnidadeMedida.UNIDADE , MoedaReal.Real, 10)

i.entrada(10,120)

print(i.vizualizar())

print(i.saida(2,130.89))

print(i.vizualizar())