from abc import ABC, abstractmethod

from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.registro.validarResgistro import IValidador


class Pessoa(ABC):

    def __init__(self,id:str, nome: str, sexo:Sexo):

        self.__I  = id
        self.__N  = " ".join(nome.split()).upper()
        self.__S  = sexo
        self.__registros: list[Registro] = []

    @property
    def nome(self) -> str:

        return self.__N;


    @nome.setter
    def nome(self, nome: str):

        self.__N = " ".join(nome.split()).upper()


    
    def registros(self) -> tuple:

        return tuple(self.__registros)


    def adicionarRegistro(self, registro: Registro) -> bool:

        n = registro.valor

        for r in self.__registros:

            if n == r.valor:
                return False
            
        self.__registros.append(registro)
        return True


    def removerRegistro(self, registro: Registro) -> bool:

        n = registro.valor
        i = -1 

        for r in self.__registros:

            i += 1
            if n == r.valor:
                self.__registros.pop(i)
                return True
            
        return False


    def alterarRegistro(self, antigo: Registro, novo: Registro) -> bool:

        i = -1
        for r in self.__registros:

            i += 1
            n = r.valor

            if n == antigo.valor and not n == novo.valor:
            
                self.__registros[i] = novo
                return True
        
        return False


    def localizar(self, tipo:IValidador) -> list:
        resultado = []

        for r in self.__registros:

            if r.tipo == tipo.getNome():

                resultado.append(r)

        return resultado            


    def info(self) -> dict:

        dados = {
            "id"  : self.__I,
            "nome": self.__N,
            "sexo": self.__S.descricao,
            "contados": {}
        }

        for r in self.__registros:

            tipo = r.tipo.getNome()

        
            if tipo not in dados["contados"]:

                dados["contados"][tipo] = r.valor
            else:

                if not isinstance(dados["contados"][tipo], list):

                    dados["contados"][tipo] = [dados["contados"][tipo]]

                dados["contados"][tipo].append(r.valor)

        return dados









    

