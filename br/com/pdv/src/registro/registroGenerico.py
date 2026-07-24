from enum import Enum


class RegistroGenerico(Enum):
    """
    Registro genérico sem validações de regra de negócio.
    Suporta qualquer tipo de registro baseado na tabela tipos_registros.
    IDs alinhados com os dados iniciais do banco de dados.
    """
    EMAIL = ("Email", 1)
    TELEFONE = ("Telefone", 2)
    CELULAR = ("Celular", 3)
    FACEBOOK = ("Facebook", 4)
    INSTAGRAM = ("Instagram", 5)
    TWITTER = ("Twitter", 6)
    LINKEDIN = ("LinkedIn", 7)
    OUTRO = ("Outro", 8)

    def __init__(self, descricao: str, codigo: int):
        self.__descricao = descricao
        self.__codigo = codigo

    def getNome(self) -> str:
        return self.__descricao

    @property
    def codigo(self) -> int:
        return self.__codigo

    def validar(self, valor: str) -> bool:
        """Sem validação de regra — aceita qualquer string não vazia."""
        if not isinstance(valor, str):
            return False
        return len(valor.strip()) > 0

    def parse(self, valor: str) -> str:
        """Retorna o valor limpo (strip), sem validação de formato."""
        valor = valor.strip()
        if len(valor) == 0:
            raise ValueError(f"{self.__descricao}: valor não pode ser vazio.")
        return valor

    @classmethod
    def por_codigo(cls, codigo: int) -> RegistroGenerico:
        """Retorna o RegistroGenerico pelo código do banco de dados."""
        for reg in cls:
            if reg.codigo == codigo:
                return reg
        raise ValueError(f"Tipo de registro com código {codigo} não encontrado.")

    @classmethod
    def por_nome(cls, nome: str)-> RegistroGenerico:
        """Retorna o RegistroGenerico pelo nome/descrição."""
        nome_upper = nome.strip().upper()
        for reg in cls:
            if reg.getNome().upper() == nome_upper:
                return reg
        raise ValueError(f"Tipo de registro '{nome}' não encontrado.")
