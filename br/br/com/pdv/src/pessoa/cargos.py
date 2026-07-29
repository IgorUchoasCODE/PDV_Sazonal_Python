from enum import Enum


class Cargo(Enum):
    DONO = ("Dono", 1)
    SOCIO = ("Sócio", 2)

    DIRETOR = ("Diretor", 3)
    GERENTE = ("Gerente", 4)
    SUPERVISOR = ("Supervisor", 5)

    VENDEDOR = ("Vendedor", 6)
    OPERADOR_CAIXA = ("Operador de Caixa", 7)
    ATENDENTE = ("Atendente", 8)

    COMPRADOR = ("Comprador", 9)
    ESTOQUISTA = ("Estoquista", 10)
    ALMOXARIFE = ("Almoxarife", 11)

    FINANCEIRO = ("Financeiro", 12)
    CONTADOR = ("Contador", 13)
    RH = ("Recursos Humanos", 14)

    MARKETING = ("Marketing", 15)
    TI = ("Tecnologia da Informação", 16)

    MOTORISTA = ("Motorista", 17)
    ENTREGADOR = ("Entregador", 18)

    AUXILIAR_ADMINISTRATIVO = ("Auxiliar Administrativo", 19)
    SECRETARIA = ("Secretária", 20)

    OUTROS = ("não definido", 21)

    def __init__(self, descricao: str, codigo: int):
        self.__descricao = descricao
        self.__codigo = codigo

    @property
    def descricao(self) -> str:
        return self.__descricao

    @property
    def codigo(self) -> int:
        return self.__codigo

    def getNome(self) -> str:
        return self.__descricao

    def __str__(self) -> str:
        return self.__descricao