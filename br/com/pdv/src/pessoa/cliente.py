from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.financeiro.comportamentoNota import ComportamentoNota


class Cliente(Pessoa):

    def __init__(self, id:str, id_pessoa, nome, sexo):

        super().__init__(id_pessoa, nome, sexo)

        self.__Empresa:
        self.__I = id
        self.__notas:dict[str:ComportamentoNota] = {}
