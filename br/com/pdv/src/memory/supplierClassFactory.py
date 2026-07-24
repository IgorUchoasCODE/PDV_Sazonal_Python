from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.memory.enterpriseClassFactory import EnterpriseClassFactory
from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
import sqlite3
from br.com.pdv.src.pessoa.fornecedor import Fornecedor
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from typing import Union


class SupplierClassFactory:
    __supplier: dict[int, Fornecedor] = {}

    @staticmethod
    def fabricar(id: int) -> Fornecedor:
        if id in SupplierClassFactory.__supplier:
            return SupplierClassFactory.__supplier[id]

        entidade = DB.SELECT.ENTIDADE_POR_ID.buscar_um(id)

        if entidade is None:
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

    @staticmethod
    def salvar(sujeito: Union[Pessoa, Empresa], id_pessoa_ou_empresa: int = None) -> int:
        """
        Cria o vínculo de Fornecedor no banco de dados para uma Pessoa ou Empresa já existente.

        Parâmetros:
          - sujeito              : instância de Pessoa ou Empresa já salva no banco
          - id_pessoa_ou_empresa : ID já existente no banco de `pessoas` ou `empresas`
                                   (se None, a factory usará o id do sujeito via info())

        Retorna o ID gerado em `entidades` (id_entidade do fornecedor), ou -1 em caso de falha.

        NOTA: A factory NÃO possui alterar() — alterações nos dados cadastrais são feitas
        diretamente em PeopleClassFactory.alterar() ou EnterpriseClassFactory.alterar(),
        pois o Fornecedor é apenas um rótulo (flag fornecedor=1) sobre uma entidade existente.
        """
        try:
            dados = sujeito.info()
            id_ref = id_pessoa_ou_empresa if id_pessoa_ou_empresa is not None else dados.get("id")

            if isinstance(sujeito, Pessoa):
                # Verifica se já existe entidade para essa pessoa como fornecedor
                entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
                for ent in entidades:
                    if ent["id_pessoa"] == id_ref and ent["id_empresa"] is None and ent["fornecedor"]:
                        print(
                            f"[SupplierClassFactory.salvar] Pessoa ID {id_ref} já é fornecedora "
                            f"(entidade ID {ent['id']})."
                        )
                        return ent["id"]

                # Cria entidade com flag fornecedor=1
                id_entidade = DB.INSERT.ENTIDADE.executar(
                    id_ref, None, 1, 0, 0  # id_pessoa, id_empresa, fornecedor, cliente, funcionario
                )

            elif isinstance(sujeito, Empresa):
                # Verifica se já existe entidade principal da empresa como fornecedor
                entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
                for ent in entidades:
                    if ent["id_empresa"] == id_ref and ent["id_pessoa"] is None and ent["fornecedor"]:
                        print(
                            f"[SupplierClassFactory.salvar] Empresa ID {id_ref} já é fornecedora "
                            f"(entidade ID {ent['id']})."
                        )
                        return ent["id"]

                id_entidade = DB.INSERT.ENTIDADE.executar(
                    None, id_ref, 1, 0, 0
                )

            else:
                print("[SupplierClassFactory.salvar] sujeito deve ser Pessoa ou Empresa.")
                return -1

            # Limpa cache
            if id_entidade in SupplierClassFactory.__supplier:
                del SupplierClassFactory.__supplier[id_entidade]

            print(
                f"[SupplierClassFactory.salvar] Fornecedor criado com entidade ID {id_entidade} "
                f"para {type(sujeito).__name__} '{dados.get('nome', '')}'."
            )
            return id_entidade

        except Exception as e:
            print(f"[SupplierClassFactory.salvar] Erro ao salvar fornecedor: {e}")
            return -1
