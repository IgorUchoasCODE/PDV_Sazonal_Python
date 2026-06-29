from enum import Enum

class Financeiro(Enum):
    Real = ("Real",1,100,1000)

   
    def __init__(self,descricao:str, unidade:int, centena:int, milhares:int):
        self.__T = descricao;
        self.__U = unidade;
        self.__C = centena;
        self.__M = milhares;

    def getNome(self)-> str:
        return self.__T
    
    def parseCentavos(self,Reais) -> int:
        centavos = self.__C * Reais

        if centavos < 1:
            raise TypeError("Valor menor que 1 centavos, converta para milheiros de centavos onde 10 milheiros é 1 centavos")
        
        return int(centavos)
    
    def parseCentavosPorMilhar(self,Reais) -> int:
        centavos = self.__M * Reais 

        if centavos < 0.1:
            raise TypeError("Valor menor que 1/10 de centavos")
        
        return int(centavos)
