from enum import Enum
from br.com.pdv.src.registro.validarResgistro import IValidador


class Documento(Enum):
    CPF = ("CPF", 11)
    CNPJ = ("CNPJ", 14)

    def __init__(self, descricao: str, tamanho: int):
        self.__descricao = descricao
        self.__tamanho = tamanho

    def getNome(self) -> str:
        return self.__descricao

    def parse(self, documento: str) -> str:
        documento = ''.join(filter(str.isdigit, documento))

        if not self.validar(documento):
            raise ValueError(f"{self.__descricao} inválido.")

        return documento

    def validar(self, documento: str) -> bool:
        documento = ''.join(filter(str.isdigit, documento))

        if len(documento) != self.__tamanho:
            return False

        if documento == documento[0] * len(documento):
            return False

        if self == Documento.CPF:
            return self.__validarCPF(documento)

        return self.__validarCNPJ(documento)

    def __validarCPF(self, cpf: str) -> bool:
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        dv1 = 0 if resto == 10 else resto

        if dv1 != int(cpf[9]):
            return False

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        dv2 = 0 if resto == 10 else resto

        return dv2 == int(cpf[10])

    def __validarCNPJ(self, cnpj: str) -> bool:
        pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]

        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto

        if dv1 != int(cnpj[12]):
            return False

        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto

        return dv2 == int(cnpj[13])
    

