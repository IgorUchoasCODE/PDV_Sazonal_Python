from enum import Enum



from enum import Enum

class Sexo(Enum):
    MASCULINO = ("Masculino", "M", 1)
    FEMININO = ("Feminino", "F", 2)
    OUTROS = ("Outros", "O", 3)

    def __init__(self, descricao: str, sigla: str, codigo: int):
        self.__descricao = descricao
        self.__sigla = sigla
        self.__codigo = codigo

    @property
    def descricao(self):
        return self.__descricao

    @property
    def sigla(self):
        return self.__sigla

    @property
    def codigo(self):
        return self.__codigo

 