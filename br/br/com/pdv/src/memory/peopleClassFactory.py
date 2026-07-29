from br.com.pdv.src.registro.registro import Registro
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.registro.registroGenerico import RegistroGenerico
from br.com.pdv.src.registro.sexo import Sexo
import sqlite3
from br.com.pdv.src.BDD.queryEnum import DB


class PeopleClassFactory:
    __pessoas: dict[int, Pessoa] = {}

    @staticmethod
    def fabricar(id: int) -> Pessoa:

        if id in PeopleClassFactory.__pessoas:
            return PeopleClassFactory.__pessoas[id]

        try:
            p = DB.SELECT.PESSOA_POR_ID.buscar_um(id)

            if isinstance(p, type(None)):
                raise ValueError(f"id não registrado {id}")

            s = p["sexo"]

            for g in Sexo:
                if s == g.codigo:
                    s = g
                    break

            pessoa = Pessoa(p["id"], p["nome"], s)

            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()

            entp = None
            for ent in entidades:
                if ent["id_pessoa"] == id and ent["id_empresa"] is None:
                    entp = ent["id"]

            ctts = DB.SELECT.REGISTRO_POR_ENTIDADE.buscar(entp)

            if ctts is not None:
                for rgt in ctts:
                    r = RegistroGenerico.por_codigo(rgt["id_tipos_registros"])
                    pessoa.adicionarRegistro(registro=Registro(r, rgt["registro"]))

            PeopleClassFactory.__pessoas[id] = pessoa

            return pessoa

        except (ValueError, sqlite3.Error) as e:
            print(f"erro => {e}")
            return None

    @staticmethod
    def salvar(pessoa: Pessoa) -> int:
        """
        Recebe uma instância de Pessoa criada pela UI, persiste no banco de dados
        e registra no cache da fábrica.

        Fluxo:
          1. INSERT em `pessoas` (nome + sexo)
          2. INSERT em `entidades` criando o vínculo (sem empresa, não é fornecedor nem cliente por padrão)
          3. INSERT dos registros de contato em `registro`

        Retorna o ID gerado em `pessoas`, ou -1 em caso de falha.
        """
        try:
            dados = pessoa.info()

            # Determina o código do sexo (int) para persistir
            sexo_codigo = None
            for g in Sexo:
                if g.descricao.upper() == dados.get("sexo", "").upper():
                    sexo_codigo = g.codigo
                    break
            if sexo_codigo is None:
                raise ValueError(f"Sexo não reconhecido: {dados.get('sexo')}")

            # 1. Salva a pessoa
            id_pessoa = DB.INSERT.PESSOA.executar(dados["nome"], sexo_codigo)

            # 2. Cria a entidade individual (sem empresa, flags neutros)
            id_entidade = DB.INSERT.ENTIDADE.executar(
                id_pessoa, None, 0, 0, 0
            )

            # 3. Salva os registros de contato
            for tipo, valores in dados.get("contados", {}).items():
                tipo_enum = RegistroGenerico.por_nome(tipo)
                if tipo_enum is None:
                    continue
                id_tipo = tipo_enum.getCodigo()
                if isinstance(valores, list):
                    for v in valores:
                        DB.INSERT.REGISTRO.executar(id_tipo, id_entidade, v)
                else:
                    DB.INSERT.REGISTRO.executar(id_tipo, id_entidade, valores)

            # Limpa cache para forçar re-fabricação atualizada
            if id_pessoa in PeopleClassFactory.__pessoas:
                del PeopleClassFactory.__pessoas[id_pessoa]

            print(f"[PeopleClassFactory.salvar] Pessoa '{dados['nome']}' salva com ID {id_pessoa}.")
            return id_pessoa

        except Exception as e:
            print(f"[PeopleClassFactory.salvar] Erro ao salvar pessoa: {e}")
            return -1

    @staticmethod
    def alterar(id: int, nome: str = None, sexo: Sexo = None) -> "Pessoa | None":
        """
        Altera dados cadastrais de uma Pessoa no banco de dados.

        Campos permitidos (não comprometem rastreabilidade — são dados cadastrais):
          - nome (str)  : novo nome completo
          - sexo (Sexo) : novo sexo

        A rastreabilidade das notas é feita por id_entidade, não pelo nome/sexo,
        portanto esses campos podem ser atualizados sem risco.

        Retorna a instância atualizada de Pessoa, ou None em caso de erro.
        """
        try:
            dados_db = DB.SELECT.PESSOA_POR_ID.buscar_um(id)
            if not dados_db:
                print(f"[PeopleClassFactory.alterar] Pessoa ID {id} não encontrada.")
                return None

            novo_nome = nome if nome is not None else dados_db["nome"]
            novo_sexo_codigo = dados_db["sexo"]  # mantém o atual como padrão

            if sexo is not None:
                if not isinstance(sexo, Sexo):
                    print(f"[PeopleClassFactory.alterar] 'sexo' deve ser uma instância de Sexo.")
                    return None
                novo_sexo_codigo = sexo.codigo

            DB.UPDATE.PESSOA.executar(novo_nome, novo_sexo_codigo, id)

            # Invalida cache e re-fabrica
            if id in PeopleClassFactory.__pessoas:
                del PeopleClassFactory.__pessoas[id]

            pessoa_atualizada = PeopleClassFactory.fabricar(id)
            print(f"[PeopleClassFactory.alterar] Pessoa ID {id} atualizada com sucesso.")
            return pessoa_atualizada

        except Exception as e:
            print(f"[PeopleClassFactory.alterar] Erro ao alterar pessoa ID {id}: {e}")
            return None

    @staticmethod
    def adicionar_registro(id_pessoa: int, registro: Registro) -> bool:
        """
        Adiciona um novo registro de contato (telefone, e-mail, CPF, etc.) a uma Pessoa
        sem remover os registros existentes.

        Retorna True em sucesso, False caso a entidade não seja encontrada.
        """
        try:
            # Encontra a entidade individual da pessoa (sem empresa vinculada)
            entidades = DB.SELECT.ENTIDADE_TODOS.buscar()
            id_entidade = None
            for ent in entidades:
                if ent["id_pessoa"] == id_pessoa and ent["id_empresa"] is None:
                    id_entidade = ent["id"]
                    break

            if id_entidade is None:
                print(f"[PeopleClassFactory.adicionar_registro] Entidade da Pessoa ID {id_pessoa} não encontrada.")
                return False

            id_tipo = registro.tipo.getCodigo()
            DB.INSERT.REGISTRO.executar(id_tipo, id_entidade, registro.valor)

            # Invalida cache para incluir o novo registro na próxima fabricação
            if id_pessoa in PeopleClassFactory.__pessoas:
                del PeopleClassFactory.__pessoas[id_pessoa]

            print(f"[PeopleClassFactory.adicionar_registro] Registro adicionado à Pessoa ID {id_pessoa}.")
            return True

        except Exception as e:
            print(f"[PeopleClassFactory.adicionar_registro] Erro: {e}")
            return False
