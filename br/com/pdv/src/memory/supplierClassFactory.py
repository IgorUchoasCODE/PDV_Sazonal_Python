
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.memory.enterpriseClassFactory import EnterpriseClassFactory
from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
import sqlite3
from br.com.pdv.src.pessoa.fornecedor import Fornecedor

class SupplierClassFactory:
    __supplier : dict[int:Fornecedor] = {}

    @staticmethod
    def fabricar(id:int) -> Fornecedor:
        if id in SupplierClassFactory.__supplier:
            return SupplierClassFactory.__supplier[id]
        
        entidade = DB.SELECT.ENTIDADE_POR_ID.buscar_um(id)

        if entidade == None:
            raise ValueError(f"Entidade com id {id} não encontrada")
        if not entidade["fornecedor"]:
            raise ValueError(f"Entidade com id {id} não é fornecedor")

        ide = entidade["id_empresa"]
        idp = entidade["id_pessoa"]

        if ide is None and idp is None:
            raise ValueError(f"Entidade com id {id} não tem empresa nem pessoa")
        
        if ide is not None:
            empresa = EnterpriseClassFactory.fabricar(ide)
            fornecedor = Fornecedor(id, empresa)
        elif idp is not None:
            pessoa = PeopleClassFactory.fabricar(idp)
            fornecedor = Fornecedor(id, pessoa)

        

        try:
            pass
        except Exception as e:
            print(f"Erro ao fabricar fornecedor {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar fornecedor {e}")
            return None

        SupplierClassFactory.__supplier[id] = fornecedor
        return fornecedor
        


