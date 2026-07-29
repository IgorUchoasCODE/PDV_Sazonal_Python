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
    def fabricar(id: int) -> Empresa:
        if id in EnterpriseClassFactory.__empresas:
            return EnterpriseClassFactory.__empresas[id]

        try:
            e = DB.SELECT.EMPRESA_POR_ID.buscar_um(id)
            if e is None:
                raise ValueError(f"empresa não encontrada {id}")

            empresa = Empresa(id, e['nome'])

            entidade = DB.SELECT.ENTIDADE_TODOS.buscar()
            if entidade is not None:
                for i in entidade:
                    if i['id_empresa'] == id:
                        ctts = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(i['id'])

                        if ctts is not None:
                            for ctt in ctts:
                                rgt = RegistroGenerico.por_codigo(ctt['id_tipos_registros'])
                                r = Registro(rgt, ctt['registro'])
                                empresa.adicionarRegistro(r)

                        if i["id_pessoa"] is not None:
                            p = PeopleClassFactory.fabricar(i["id_pessoa"])

                            if p is not None:
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

    @staticmethod
    def salvar(empresa: Empresa) -> int:
        """
        Recebe uma instância de Empresa criada pela UI, persiste no banco de dados
        e registra no cache da fábrica.

        Fluxo:
          1. INSERT em `empresas` (nome)
          2. INSERT em `entidades` criando o vínculo (sem pessoa direta, flags neutros)
          3. INSERT dos registros de contato em `registro`
          4. Para cada representante interno (Pessoa + Cargo):
             - Garante que a Pessoa existe no banco via PeopleClassFactory.salvar()
             - INSERT de entidade_cargo na tabela de relacionamento

        Retorna o ID gerado em `empresas`, ou -1 em caso de falha.
        """
        try:
            dados = empresa.info()

            # 1. Salva a empresa
            id_empresa = DB.INSERT.EMPRESA.executar(dados["nome"])

            # 2. Cria entidade principal da empresa (sem pessoa direta)
            id_entidade_principal = DB.INSERT.ENTIDADE.executar(
                None, id_empresa, 0, 0, 0
            )

            # 3. Salva registros de contato da empresa
            for tipo, valores in dados.get("contatos", {}).items():
                tipo_enum = RegistroGenerico.por_nome(tipo)
                if tipo_enum is None:
                    continue
                id_tipo = tipo_enum.getCodigo()
                if isinstance(valores, list):
                    for v in valores:
                        DB.INSERT.REGISTRO.executar(id_tipo, id_entidade_principal, v)
                else:
                    DB.INSERT.REGISTRO.executar(id_tipo, id_entidade_principal, valores)

            # 4. Salva representantes (Pessoa vinculada à empresa por cargo)
            for nome_cargo, nomes_pessoas in dados.get("representantes", {}).items():
                cargo_obj = None
                for c in Cargo:
                    if c.getNome().upper() == nome_cargo.upper():
                        cargo_obj = c
                        break
                if cargo_obj is None:
                    continue

                lista_nomes = nomes_pessoas if isinstance(nomes_pessoas, list) else [nomes_pessoas]
                for nome_pessoa in lista_nomes:
                    # Busca a pessoa no banco pelo nome para obter o id
                    todas_pessoas = DB.SELECT.PESSOA_TODOS.buscar()
                    id_pessoa_rep = None
                    for pp in todas_pessoas:
                        if pp.get("nome", "").upper() == nome_pessoa.upper():
                            id_pessoa_rep = pp["id"]
                            break
                    if id_pessoa_rep is None:
                        continue

                    # Cria entidade vinculando pessoa à empresa
                    id_ent_rep = DB.INSERT.ENTIDADE.executar(
                        id_pessoa_rep, id_empresa, 0, 0, 1  # funcionario=1
                    )
                    DB.INSERT.ENTIDADE_CARGO.executar(id_ent_rep, cargo_obj.codigo)

            # Limpa cache
            if id_empresa in EnterpriseClassFactory.__empresas:
                del EnterpriseClassFactory.__empresas[id_empresa]

            print(f"[EnterpriseClassFactory.salvar] Empresa '{dados['nome']}' salva com ID {id_empresa}.")
            return id_empresa

        except Exception as e:
            print(f"[EnterpriseClassFactory.salvar] Erro ao salvar empresa: {e}")
            return -1

    @staticmethod
    def alterar(id: int, nome: str) -> Empresa | None:
        """
        Altera o nome de uma Empresa no banco de dados.

        Apenas o nome pode ser alterado livremente, pois é um dado cadastral.
        O id da empresa, representantes e vínculos com notas são imutáveis.

        Retorna a instância atualizada de Empresa, ou None em caso de erro.
        """
        try:
            dados_db = DB.SELECT.EMPRESA_POR_ID.buscar_um(id)
            if not dados_db:
                print(f"[EnterpriseClassFactory.alterar] Empresa ID {id} não encontrada.")
                return None

            if not isinstance(nome, str) or not nome.strip():
                print("[EnterpriseClassFactory.alterar] Nome inválido.")
                return None

            DB.UPDATE.EMPRESA.executar(nome, id)

            # Invalida cache e re-fabrica
            if id in EnterpriseClassFactory.__empresas:
                del EnterpriseClassFactory.__empresas[id]

            empresa_atualizada = EnterpriseClassFactory.fabricar(id)
            print(f"[EnterpriseClassFactory.alterar] Empresa ID {id} atualizada com sucesso.")
            return empresa_atualizada

        except Exception as e:
            print(f"[EnterpriseClassFactory.alterar] Erro ao alterar empresa ID {id}: {e}")
            return None

    @staticmethod
    def adicionar_registro(id_empresa: int, registro: Registro) -> bool:
        """
        Adiciona um novo registro de contato (telefone, e-mail, CNPJ, etc.) a uma Empresa
        sem remover os registros existentes.

        Retorna True em sucesso, False caso a entidade da empresa não seja encontrada.
        """
        try:
            # Encontra a entidade principal da empresa (sem pessoa vinculada)
            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            id_entidade = None
            for ent in entidades:
                if ent["id_empresa"] == id_empresa and ent["id_pessoa"] is None:
                    id_entidade = ent["id"]
                    break

            if id_entidade is None:
                print(f"[EnterpriseClassFactory.adicionar_registro] Entidade da Empresa ID {id_empresa} não encontrada.")
                return False

            id_tipo = registro.tipo.getCodigo()
            DB.INSERT.REGISTRO.executar(id_tipo, id_entidade, registro.valor)

            # Invalida cache
            if id_empresa in EnterpriseClassFactory.__empresas:
                del EnterpriseClassFactory.__empresas[id_empresa]

            print(f"[EnterpriseClassFactory.adicionar_registro] Registro adicionado à Empresa ID {id_empresa}.")
            return True

        except Exception as e:
            print(f"[EnterpriseClassFactory.adicionar_registro] Erro: {e}")
            return False
