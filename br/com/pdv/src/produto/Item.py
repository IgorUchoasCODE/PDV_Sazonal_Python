from br.com.pdv.src.produto.comportamentoEstoque import ComportamentoEstoque
from br.com.pdv.src.financeiro.Real import MoedaReal
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida


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

        if self.__estoque < q :
            raise ValueError(f"Estoque insuficiente{self.__estoque}")
        
        self.__estoque -= q
        self.__valorEstoque -= q * self.__valorPorUn
        
        return self.__R.calculo_QpQsVuVv_L(q,self.__valorPorUn, v)
        

    def atualizar(self):
        
        if self.__estoque == 0:
            return False
        else:
            return True
    
    def vizualizar(self):
        return {
          "M" : self.__M,
          "D" : self.__D,
          "R" : self.__R,
          "V" : self.__V,

          "Estoque" : self.__estoque,
          "ValorPOrUn" : self.__valorPorUn,
          "ValorEstoque" : self.__valorEstoque
        }
    

