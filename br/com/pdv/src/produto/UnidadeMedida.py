from enum import Enum

class UnidadeMedida(Enum):
    UNIDADE = ("Unidade",1)

    kG = ("kilograma",1000)
    DG = ("Decigrama",10)

    L = ("Litros",1000)
    UI = ("ui",10)

    M = ("Metros",1000)
    ML = ("Milimetro",10)

    
    def __init__(self,descricao : str, proporcaoUmPra : int):
        self.__descricao = descricao
        self.__deUmPra = proporcaoUmPra

    def getDescription(self) -> str:
        return self.__descricao

    def getMultInt(self) -> int:
        return int(self.__deUmPra)

    def parseInt(self, valor: int) -> int:
        return int(valor * self.__deUmPra)
       
    


