from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.cargos import Cargo
from br.com.pdv.src.registro.registro import Registro

class Empresa:
    ''' essa classe representa empresa e seus representantes '''

    def __init__(self, id:str, nome:str):
        self.__I = id;
        self.__N = nome

        self.__registros      : list[Registro]         = []
        self.__representantes : dict[str,list[Pessoa]] = {}


    def adicionarRepresentante(self, repredentante:Pessoa, cargo:Cargo) -> bool:
        
        n = repredentante.nome
        c = cargo.getNome()
        v = self.buscarRepresentantes(n)

        if  v["b"]: return False

        if c not in self.__representantes:

            self.__representantes[c] = []

        self.__representantes[c].append(repredentante)        

        return True

  
    def buscarRepresentantes(self, nome:str) -> dict :

        n = " ".join(nome.split()).upper()
        b = {

            "b"             : False,
            "cargo"         : False,
            "representante" : False

            }
        

        for c in self.__representantes.keys():

            i = -1

            if len(self.__representantes[c]) == 0: continue

            for p in self.__representantes[c]:

                i += 1

                if p.nome == n:

                    for cargo in Cargo:

                        if c == cargo.descricao:

                            b["b"]             = True
                            b["cargo"]         = cargo
                            b["representante"] = p 
                            b["i"] = i  

                            return b
                        
        return b
        

    def adicionarRegistro(self, registro: Registro) -> bool:

        for r in self.__registros:

            n = r.valor

            if n == registro.valor:
                return False
        
        self.__registros.append(registro)

    def buscarRegistro(self, registros:str) -> Registro | bool:

        r = " ".join(registros.split()).upper()

        i = -1
        for rg in self.__registros:

            i += 1

            if r == rg.valor:

                return rg
            
        return False


    def removerRepresentante(self, nome : str) -> bool:

        n = " ".join(nome.split()).upper()
        v = self.buscarRepresentantes(n)

        if not v["b"]: return False

        self.__representantes[v["cargo"].descricao].pop(v["i"])

        if len(self.__representantes[v["cargo"].descricao]) == 0:

            self.__representantes.pop(v["cargo"].descricao)

        return True


    def removerRegistro(self, registro: Registro) -> bool:
        
        i = -1
        for r in self.__registros:

            i += 1
            n = r.valor

            if n == registro.valor:
                
                self.__registros.pop(i)

                return True
        
        return False


    def alterarRegistro(self, antigo: Registro, novo: Registro) -> bool:
        
        i = -1
        for r in self.__registros:

            i += 1
            n = r.valor

            if n == antigo.valor and not n == novo.valor:
            
                self.__registros[i] = novo
                return True
        
        return False


    def info(self) -> dict:

        r = self.__registros
        cr = self.__representantes

        dados = {
            "id"   : self.__I,
            "nome" : self.__N,
            "contatos" : {},
            "representantes" :{}
        }

        for c in r:

            n = c.tipo.getNome()
            
            if n not in dados["contatos"]:

                dados["contatos"][n] = c.valor

            else:

                if not isinstance( dados["contatos"][n], list):
                    dados["contatos"][n] = [dados["contatos"][n]]

                dados["contatos"][n].append(c.valor)

        
        for n in cr:
            
            listapessoa = ""
            i = -1
            if n not in dados["representantes"]:

                for p in cr[n]:
                    i += 1

                    nomePessoa = p.nome
                    
                    if i <= 0:

                        listapessoa = nomePessoa
                    else:

                        listapessoa = [listapessoa]
                        listapessoa.append(nomePessoa)

                dados["representantes"][n] = listapessoa
            
            else:

                print("errrrrrrrrrrro" , n)


        
        return dados







