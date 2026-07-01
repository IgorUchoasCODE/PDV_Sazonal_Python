from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.cargos import Cargo
from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.registro.validarResgistro import IValidador
from br.com.pdv.src.financeiro.Real import MoedaReal



class Empresa:

    def __init__(self, id:str, nome:str):
        self.__I = id;
        self.__N = nome

        self.__registros: list[Registro] = []
        self.__representantes :dict[str,list[Pessoa]] = {}

    def adicionarRepresentante(self, repredentante:Pessoa, cargo:Cargo) -> bool:

        chave = cargo.getNome()

        if chave not in self.__representantes:
            self.__representantes[chave] = []

        if repredentante in self.__representantes[chave]:
            return False

        self.__representantes[chave].append(repredentante)

        return True

    
    def adicionarRegistro(self, registro: Registro) -> bool:

        if registro in self.__registros:

            return False
        
        self.__registros.append(registro)

    def removerRepresentante(self, cargo: Cargo, representante : Pessoa):
        
        chave = cargo.getNome()

        if chave not in self.__representantes:
            return False
        if representante not in self.__representantes[chave]:
            return False
        
        self.__representantes[chave].remove(representante)



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
    
    def propriedadeEmpresa(self) -> dict:
        r = self.__registros
        p = self.__representantes

        dados = {
            "id"   : self.__I,
            "nome" : self.__N,

            "contatos" : {},
            "representantes" :{}
        }

        for c in r:

            tipo = c.tipo.getNome()

            if tipo not in dados["contatos"]:
                dados["contatos"][tipo] = c.valor
            else:

                if not isinstance(dados["registros"][tipo], list):

                    dados["registros"][tipo] = [dados["registros"][tipo]]

            dados["registros"][tipo].append(c.valor)

            

  

   

    
