from enum import Enum
from br.com.pdv.src.registro.validarResgistro import IValidador
import re


class Email(Enum):
    
    COMUM = ("E-mail", r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    
    def __init__(self, descricao: str, regex: str):
        self.__descricao = descricao
        self.__regex = regex



    def getNome(self) -> str:
        return self.__descricao

    def validar(self, valor: str) -> bool:
        if not isinstance(valor, str):
            return False

        valor = valor.strip().lower()

        if len(valor) == 0:
            return False

        # Deve possuir apenas um @
        if valor.count("@") != 1:
            return False

        usuario, dominio = valor.split("@")

        if not usuario:
            return False

        if not dominio:
            return False

        # Deve possuir ponto no domínio
        if "." not in dominio:
            return False

        # Não pode começar ou terminar com ponto
        if dominio.startswith(".") or dominio.endswith("."):
            return False

        # Não aceita espaços
        if " " in valor:
            return False

        # Regex simples para validar e-mail
        padrao = self.__regex

        return re.fullmatch(padrao, valor) is not None
    
    def parse(self, valor: str) -> str:
        valor = valor.strip().lower()

        if not self.validar(valor):
            raise ValueError(f"{self.__descricao} inválido.")

        return valor

    
    

