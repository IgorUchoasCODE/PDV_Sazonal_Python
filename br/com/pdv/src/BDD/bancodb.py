import sqlite3
import os


class BancoDB:
    """
    Gerenciador de Conexão com o Banco de Dados SQLite.
    Centraliza a criação de tabelas e abertura de conexões.
    """
    _DB_NAME = "databaseSazonalizei.db"

    @staticmethod
    def obter_conexao():
        """Retorna uma nova conexão ativa com o banco SQLite."""

        conn = sqlite3.connect(BancoDB._DB_NAME) # Cria a conexão com o banco de dados
        conn.execute("PRAGMA foreign_keys = ON;") # Habilita suporte a chaves estrangeiras no SQLite
        conn.row_factory = sqlite3.Row # Retorna os resultados das queries como dicionários
        return conn

    @staticmethod
    def inicializar_banco():
        """Cria as tabelas necessárias se elas não existirem."""
        with BancoDB.obter_conexao() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
               CREATE TABLE IF NOT EXISTS unidadeMedida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                fatorConjunto INTEGER,
                CONSTRAINT chk_fator_conjunto CHECK (
                    descricao != 'Conjunto/Pacote' OR fatorConjunto IS NOT NULL
                ));
            """)

          
            cursor.execute("SELECT COUNT(*) FROM unidadeMedida;")
            if cursor.fetchone()[0] == 0:
                unidades_padrao = [
                    ('Unidade', None),
                    ('Kilograma', None),
                    ('Litros', None),
                    ('Metros', None),
                    ('Conjunto/Pacote', 1)
                ]
                cursor.executemany(
                    "INSERT INTO unidadeMedida (descricao, fatorConjunto) VALUES (?, ?);",
                    unidades_padrao
                )


            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produto (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    diasDuraveis INTEGER DEFAULT 365,
                    unidadeMedida INTEGER DEFAULT 1,
                    receita BOOLEAN DEFAULT 0,
                    varejo DECIMAL(10, 3) DEFAULT 0.000,
                    atacado DECIMAL(10, 3) DEFAULT 0.000,
                    promocao DECIMAL(10, 3) DEFAULT 0.000,
                    FOREIGN KEY (unidadeMedida) REFERENCES unidadeMedida (id)
                );  
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS receita (
                id_produto INTEGER NOT NULL,
                id_ingrediente INTEGER NOT NULL,
                qntdd NUMERIC NOT NULL,
                PRIMARY KEY (id_produto, id_ingrediente),
                FOREIGN KEY (id_produto) REFERENCES produto (id),
                FOREIGN KEY (id_ingrediente) REFERENCES produto (id)
            );
            """)
            conn.commit()















