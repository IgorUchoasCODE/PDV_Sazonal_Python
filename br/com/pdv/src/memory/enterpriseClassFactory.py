

from br.com.pdv.src.pessoa.cargos import Cargo
from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.registro.registroGenerico import RegistroGenerico
from br.com.pdv.src.BDD.queryEnum import DB
import sqlite3
from br.com.pdv.src.pessoa.empresa import Empresa
class EnterpriseClassFactory:
    __empresas: dict[int, Empresa] = {}

    @staticmethod
    def fabricar(id:int) -> Empresa:
        if id in EnterpriseClassFactory.__empresas:return EnterpriseClassFactory.__empresas[id]

        try:
            e = DB.SELECT.EMPRESA_POR_ID.buscar_um(id)
            if e == None : raise ValueError(f"empresa não encontrada {id}")

            empresa = Empresa(id, e['nome'])

            entidade = DB.SELECT.ENTIDADE_TODOS.buscar()
            if entidade != None :
                for i in entidade:
                    if i['id_empresa'] == id: 
                        ctts = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(i['id'])

                        if ctts != None:
                            for ctt in ctts:
                                rgt = RegistroGenerico.por_codigo(ctt['id_tipos_registros'])
                                r = Registro(rgt, ctt['registro'])
                                empresa.adicionarRegistro(r)
                                
                        if i["id_pessoa"] != None:
                            p = PeopleClassFactory.fabricar(i["id_pessoa"])
                            
                            if p != None:

                                cargo_rows = DB.SELECT.CARGO_POR_ENTIDADE.buscar(i['id'])

                                if cargo_rows:
                                    for c_row in cargo_rows:
                                        id_cargo = c_row.get('id_cargo')
                                        for cargo in Cargo:
                                            if cargo.codigo == id_cargo:
                                                empresa.adicionarRepresentante(p, cargo)
                                                break
        
        except ValueError as e:
            print(f"erro => {e}")
            return None
        except sqlite3.Error as e:
            print(f"erro => {e}")
            return None
        
        EnterpriseClassFactory.__empresas[id] = empresa
        return empresa
                                    
                            
                         

