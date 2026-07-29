from br.com.pdv.src.registro.validarResgistro import IValidador

class Registro:

    def __init__(self, tipo:IValidador, valor: str):
        
        self.__tipo = tipo
        self.__valor = tipo.parse(valor)

    @property
    def tipo(self):
        return self.__tipo

    @property
    def valor(self):
        return self.__valor
