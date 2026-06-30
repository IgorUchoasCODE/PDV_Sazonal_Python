from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

class MoedaReal(Enum):
    Real = ("Real",1,100,1000)

   
    def __init__(self,descricao:str, unidade:int, centena:int, milhares:int):
        self.__T = descricao;
        self.__U = unidade;
        self.__C = centena;
        self.__M = milhares;

    def getNome(self)-> str:
        return self.__T
    
    def calculo_PQV_T(self, proporcao:int, Quatidade:int, valor_Milhar:int)-> int:
        
        return  (Quatidade * valor_Milhar) // proporcao
    
    def calculo_QeVp_Vu(self, proporcao:int, valor_Milhar:int) -> int:
       
        if valor_Milhar < proporcao:
            raise TypeError("Valor menor que 1/10 de centavos")

        return valor_Milhar // proporcao
    
    def calculo_QpQsVuVv_L(self, quantidade_Sainda_milhar:int, valor_Custo_U:int, valor_Venda_Milhar:int) -> int:
        qV = quantidade_Sainda_milhar * valor_Venda_Milhar
        qC = quantidade_Sainda_milhar * valor_Custo_U

        return qV - qC


    

    def parseCentavosPorMilhar(self, reais):
        return int(
            (Decimal(str(reais)) * Decimal(self.__M))
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        
   

