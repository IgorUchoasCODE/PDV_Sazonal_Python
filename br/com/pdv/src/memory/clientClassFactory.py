

from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
from br.com.pdv.src.memory.enterpriseClassFactory import EnterpriseClassFactory
import sqlite3
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.pessoa.cliente import Cliente

class ClientClassFactory:
    __client: dict[int, Cliente] = {}

    @staticmethod
    def fabricar(id:int)-> Cliente:
        if id in ClientClassFactory.__client: return ClientClassFactory.__client[id]

        try:

            entidade = DB.SELECT.ENTIDADE_POR_ID.buscar_um(id)
            
            if entidade == None: raise ValueError(f"entidade não encontrada {id}")
            if not entidade["cliente"]: raise ValueError(f"entidade não é cliente {entidade}")

            idp = entidade["id_pessoa"]
            ide = entidade["id_empresa"]

            if ide is None and idp is not None:
                pessoa = PeopleClassFactory.fabricar(idp)
                cliente = Cliente(id, pessoa)
            elif ide is not None:
                empresa = EnterpriseClassFactory.fabricar(ide)
                cliente = Cliente(id, empresa)
            else: 
                raise ValueError(f"entidade não tem empresa nem pessoa {entidade}")
                     
        except Exception as e:
            print(f"Erro ao fabricar cliente {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar cliente {e}")
            return None
        
        
        
        ClientClassFactory.__client[id] = cliente
        return cliente


