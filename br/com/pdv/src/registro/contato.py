from enum import Enum
from br.com.pdv.src.registro.validarResgistro import IValidador

class Contato(Enum):
    TELEFONE = ("Telefone", 10)
    CELULAR = ("Celular", 11)

    def __init__(self, descricao: str, tamanho: int):
        self.__descricao = descricao
        self.__tamanho = tamanho

    def getNome(self) -> str:
        return self.__descricao

    def parse(self, numero: str) -> str:
        numero = ''.join(filter(str.isdigit, numero))

        if not self.validar(numero):
            raise ValueError(f"{self.__descricao} inválido.")

        return numero

    def validar(self, numero: str) -> bool:
        numero = ''.join(filter(str.isdigit, numero))

        # Tamanho
        if len(numero) != self.__tamanho:
            return False

        # Não aceita todos os números iguais
        if numero == numero[0] * len(numero):
            return False

        ddd = numero[:2]

        # DDD apenas entre 11 e 99
        if not ddd.isdigit():
            return False

        ddd = int(ddd)

        if ddd < 11 or ddd > 99:
            return False

        if self == Contato.TELEFONE:
            return self.__validarTelefone(numero)

        return self.__validarCelular(numero)

    def __validarTelefone(self, numero: str) -> bool:
        primeiro = numero[2]

        # Telefones fixos começam entre 2 e 5
        return primeiro in "2345"

    def __validarCelular(self, numero: str) -> bool:
        # Celular brasileiro possui 9 após o DDD
        if numero[2] != "9":
            return False

        # Segundo dígito normalmente entre 6 e 9
        if numero[3] not in "6789":
            return False

        return True