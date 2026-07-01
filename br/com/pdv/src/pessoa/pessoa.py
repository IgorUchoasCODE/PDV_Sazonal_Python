from abc import ABC, abstractmethod

from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.registro.registro import Registro


class Pessoa(ABC):

    def __init__(self,id:str, nome: str, sexo:Sexo):

        self.__I  = id
        self.__N  = nome
        self.__S  = sexo
        self.__registros: list[Registro] = [];

    @property
    def nome(self) -> str:

        return self.__nome;

    @nome.setter
    def nome(self, nome: str):

        self.__nome = nome

    @property
    def registros(self) -> tuple:

        return tuple(self.__registros)

    def adicionarRegistro(self, registro: Registro) -> bool:

        if registro in self.__registros:

            return False
        
        if registro.tipo.getNome() == "CPF":

            for r in self.__registros:

                if r.tipo.getNome() == "CPF":

                    return False

        self.__registros.append(registro)

        return True

    def removerRegistro(self, registro: Registro) -> bool:

        if registro not in self.__registros:

            return False

        self.__registros.remove(registro)

        return True

    def alterarRegistro(self, antigo: Registro, novo: Registro) -> bool:

        try:

            indice = self.__registros.index(antigo)

        except ValueError:

            return False

        self.__registros[indice] = novo

        return True

    def localizar(self, tipo):

        return tuple(

            registro
            for registro in self.__registros
            if registro.tipo == tipo

        )
    
    def vizualizar(self) -> dict:

        dados = {
            "id"  : self.__I,
            "nome": self.__N,
            "sexo": self.__S.descricao,
            "registros": {}
        }

        for r in self.__registros:

            tipo = r.tipo.getNome()

        
            if tipo not in dados["registros"]:

                dados["registros"][tipo] = r.valor
            else:

                if not isinstance(dados["registros"][tipo], list):

                    dados["registros"][tipo] = [dados["registros"][tipo]]

                dados["registros"][tipo].append(r.valor)

        return dados









    

