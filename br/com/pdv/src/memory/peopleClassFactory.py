

from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.registro.registroGenerico import RegistroGenerico
from br.com.pdv.src.registro.sexo import Sexo
import sqlite3
from br.com.pdv.src.pessoa import pessoa
from br.com.pdv.src.BDD.queryEnum import DB

class PeopleClassFactory:
    __pessoas: dict[int, Pessoa] = {}

    @staticmethod
    def fabricar(id:int)-> Pessoa:

        if id in PeopleClassFactory.__pessoas: return PeopleClassFactory.__pessoas[id]

        try:
            p = DB.SELECT.PESSOA_POR_ID.buscar_um(id)

            if isinstance(p, type(None)): raise ValueError(f"id não registrado {id}")

            s = p["sexo"]

            for g in Sexo:
                if s == g.codigo:
                    s = g
                    break

            pessoa = Pessoa(p["id"], p["nome"], s)

            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            
            entp = None
            for ent in entidades:
                if ent["id_pessoa"] == id and ent["id_empresa"] == None:
                    entp = ent["id"]
            
            ctts = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(entp)

            if ctts != None:
                for rgt in ctts:

                    r = RegistroGenerico.por_codigo(rgt["id_tipos_registros"])

                    pessoa.adicionarRegistro(registro= Registro(r,rgt["registro"]))
            

            PeopleClassFactory.__pessoas[id] = pessoa

            return pessoa
            
        except (ValueError, sqlite3.Error) as e:
            print(f"erro => {e}")
            return None


