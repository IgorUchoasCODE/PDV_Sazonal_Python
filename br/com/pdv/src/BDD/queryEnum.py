from enum import Enum
from br.com.pdv.src.BDD.bancodb import BancoDB

class QueryBase(Enum):
    def executar(self, *args):
        """
        Executa comandos DML (INSERT, UPDATE, DELETE).
        Retorna o ID gerado (para INSERT) ou o número de linhas afetadas.
        Garante que qualquer texto (string) enviado seja salvo em minúsculo.
        """
        # Converte todos os argumentos que forem do tipo texto (str) para minúsculo
        args_formatados = tuple(arg.upper() if isinstance(arg, str) else arg for arg in args)
        
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(self.value, args_formatados)
            conn.commit()
            # Se for INSERT, retorna o ID inserido, caso contrário, retorna as linhas afetadas.
            return cursor.lastrowid if "INSERT" in self.value.upper() else cursor.rowcount

    def buscar(self, *args):
        """
        Executa comandos SELECT e retorna uma lista de dicionários.
        """
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(self.value, args)
            return [dict(row) for row in cursor.fetchall()]

    def buscar_um(self, *args):
        """
        Executa comandos SELECT e retorna apenas o primeiro resultado como dicionário.
        """
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(self.value, args)
            row = cursor.fetchone()
            return dict(row) if row else None

class INSERT(QueryBase):
    PRODUTO = """
        INSERT INTO produto (
            nome, diasDuraveis, unidadeMedida, receita, 
            varejo, atacado, promocao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    UNIDADE_MEDIDA = """
        INSERT INTO unidadeMedida (descricao, fatorConjunto) 
        VALUES (?, ?)
    """
    
    RECEITA = """
        INSERT INTO receita (id_produto, id_ingrediente, qntdd) 
        VALUES (?, ?, ?)
    """


class SELECT(QueryBase):
    PRODUTO_POR_ID = "SELECT * FROM produto WHERE id = ?"
    PRODUTO_TODOS = "SELECT * FROM produto"
    
    UNIDADE_MEDIDA_TODOS = "SELECT * FROM unidadeMedida"
    UNIDADE_MEDIDA_POR_ID = "SELECT * FROM unidadeMedida WHERE id = ?"
    
    RECEITA_POR_PRODUTO = "SELECT * FROM receita WHERE id_produto = ?"


class UPDATE(QueryBase):
    PRODUTO = """
        UPDATE produto 
        SET nome = ?, diasDuraveis = ?, unidadeMedida = ?, receita = ?, 
            varejo = ?, atacado = ?, promocao = ?
        WHERE id = ?
    """
    
    UNIDADE_MEDIDA = """
        UPDATE unidadeMedida 
        SET descricao = ?, fatorConjunto = ?
        WHERE id = ?
    """


class DELETE(QueryBase):
    PRODUTO = "DELETE FROM produto WHERE id = ?"
    UNIDADE_MEDIDA = "DELETE FROM unidadeMedida WHERE id = ?"
    RECEITA_POR_PRODUTO = "DELETE FROM receita WHERE id_produto = ?"


class DB:
    """
    Classe utilitária para facilitar o acesso aos enums de query de forma encadeada.
    Exemplo de uso:
    
        # Inserir um registro (retorna o ID do produto criado)
        id_novo = DB.INSERT.PRODUTO.executar("Coca-Cola", 365, 1, 0, 10.0, 9.0, 8.5)
        
        # Buscar todos os produtos
        produtos = DB.SELECT.PRODUTO_TODOS.buscar()
        
        # Buscar um produto específico
        produto = DB.SELECT.PRODUTO_POR_ID.buscar_um(id_novo)
    """
    INSERT = INSERT
    SELECT = SELECT
    UPDATE = UPDATE
    DELETE = DELETE



#print(DB.UPDATE.UNIDADE_MEDIDA.executar("CONJUNTO/PACOTE", 1, 5))
#print(DB.INSERT.PRODUTO.executar("caixa de ovos branco tipo A", 10, 6, 0, 180, 175, 165))
