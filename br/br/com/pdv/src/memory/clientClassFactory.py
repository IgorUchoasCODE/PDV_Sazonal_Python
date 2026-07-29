from br.com.pdv.src.memory.peopleClassFactory import PeopleClassFactory
from br.com.pdv.src.memory.enterpriseClassFactory import EnterpriseClassFactory
import sqlite3
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.pessoa.cliente import Cliente
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from typing import Union


class ClientClassFactory:
    __client: dict[int, Cliente] = {}

    @staticmethod
    def fabricar(id: int) -> Cliente:
        if id in ClientClassFactory.__client:
            return ClientClassFactory.__client[id]

        try:
            entidade = DB.SELECT.ENTIDADE_POR_ID.buscar_um(id)

            if entidade is None:
                raise ValueError(f"entidade não encontrada {id}")
            if not entidade["cliente"]:
                raise ValueError(f"entidade não é cliente {entidade}")

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

    @staticmethod
    def salvar(sujeito: Union[Pessoa, Empresa], id_pessoa_ou_empresa: int = None) -> int:
        """
        Cria o vínculo de Cliente no banco de dados para uma Pessoa ou Empresa já existente.

        Parâmetros:
          - sujeito              : instância de Pessoa ou Empresa já salva no banco
          - id_pessoa_ou_empresa : ID já existente no banco de `pessoas` ou `empresas`
                                   (se None, a factory usará o id do sujeito via info())

        Retorna o ID gerado em `entidades` (id_entidade do cliente), ou -1 em caso de falha.

        NOTA: A factory NÃO possui alterar() — alterações nos dados cadastrais são feitas
        diretamente em PeopleClassFactory.alterar() ou EnterpriseClassFactory.alterar(),
        pois o Cliente é apenas um rótulo (flag cliente=1) sobre uma entidade existente.
        """
        try:
            dados = sujeito.info()
            id_ref = id_pessoa_ou_empresa if id_pessoa_ou_empresa is not None else dados.get("id")

            if isinstance(sujeito, Pessoa):
                # Verifica se já existe uma entidade para essa pessoa como cliente
                entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
                for ent in entidades:
                    if ent["id_pessoa"] == id_ref and ent["id_empresa"] is None and ent["cliente"]:
                        print(
                            f"[ClientClassFactory.salvar] Pessoa ID {id_ref} já é cliente "
                            f"(entidade ID {ent['id']})."
                        )
                        return ent["id"]

                # Cria entidade com flag cliente=1
                id_entidade = DB.INSERT.ENTIDADE.executar(
                    id_ref, None, 0, 1, 0  # id_pessoa, id_empresa, fornecedor, cliente, funcionario
                )

            elif isinstance(sujeito, Empresa):
                # Verifica se já existe entidade principal da empresa como cliente
                entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
                for ent in entidades:
                    if ent["id_empresa"] == id_ref and ent["id_pessoa"] is None and ent["cliente"]:
                        print(
                            f"[ClientClassFactory.salvar] Empresa ID {id_ref} já é cliente "
                            f"(entidade ID {ent['id']})."
                        )
                        return ent["id"]

                id_entidade = DB.INSERT.ENTIDADE.executar(
                    None, id_ref, 0, 1, 0
                )

            else:
                print("[ClientClassFactory.salvar] sujeito deve ser Pessoa ou Empresa.")
                return -1

            # Limpa cache
            if id_entidade in ClientClassFactory.__client:
                del ClientClassFactory.__client[id_entidade]

            print(
                f"[ClientClassFactory.salvar] Cliente criado com entidade ID {id_entidade} "
                f"para {type(sujeito).__name__} '{dados.get('nome', '')}'."
            )
            return id_entidade

        except Exception as e:
            print(f"[ClientClassFactory.salvar] Erro ao salvar cliente: {e}")
            return -1
