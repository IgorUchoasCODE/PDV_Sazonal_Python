from abc import ABC, abstractmethod
from br.com.pdv.src.registro.contato import Contato
from br.com.pdv.src.registro.cpfcnpj import Documento
from br.com.pdv.src.registro.email import Email
from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.registro.validarResgistro import IValidador
from br.com.pdv.src.registro.registro import Registro





class Pessoa(ABC):

    def __init__(self, nome: str, sexo:Sexo):

        self.__nome = nome
        self.__sexo  = sexo
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
    
    def to_dict(self) -> dict:

        dados = {
            "nome": self.__nome,
            "sexo": self.__sexo.descricao,
            "registros": {}
        }

        for r in self.__registros:

            tipo = r.tipo.getNome()

            # se repetir tipo, vira lista
            if tipo not in dados["registros"]:
                dados["registros"][tipo] = r.valor
            else:
                if not isinstance(dados["registros"][tipo], list):
                    dados["registros"][tipo] = [dados["registros"][tipo]]

                dados["registros"][tipo].append(r.valor)

        return dados



p = Pessoa("igor", Sexo.MASCULINO)

p.adicionarRegistro(Registro(Email.COMUM, "igor@uchoa.com"))
p.adicionarRegistro(Registro(Documento.CPF,"88243733051"))
p.adicionarRegistro(Registro(Contato.CELULAR, "92984176969"))
p.adicionarRegistro(Registro(Contato.CELULAR, "92984111242"))

print(p.registros[0].tipo.getNome(), p.registros[0].valor)
print(p.to_dict())





    

