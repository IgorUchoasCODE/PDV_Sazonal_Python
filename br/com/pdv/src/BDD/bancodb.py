import sqlite3
import os
import datetime

# Registra os conversores recomendados para Python 3.12+ (remove DeprecationWarning)
sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())
sqlite3.register_adapter(datetime.datetime, lambda val: val.isoformat(" "))
sqlite3.register_converter("DATE", lambda val: datetime.date.fromisoformat(val.decode()))
sqlite3.register_converter("TIMESTAMP", lambda val: datetime.datetime.fromisoformat(val.decode()))

# Registra o conversor de BOOLEAN para retornar True/False em vez de 1/0
sqlite3.register_converter("BOOLEAN", lambda v: v == b'1')

class BancoDB:
    """
    Gerenciador de Conexão com o Banco de Dados SQLite.
    Centraliza a criação de tabelas e abertura de conexões.
    """
    _DB_NAME = "databaseSazonalizei.db"

    @staticmethod
    def obter_conexao():
        """Retorna uma nova conexão ativa com o banco SQLite."""

        conn = sqlite3.connect(
            BancoDB._DB_NAME,
            detect_types=sqlite3.PARSE_DECLTYPES
        ) # Cria a conexão com o banco de dados
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

            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS "tiposNotas"(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                descricao TEXT NOT NULL UNIQUE
            );
            INSERT OR IGNORE INTO tiposNotas (id, descricao) VALUES
            (1, 'COMPRA'),
            (2, 'VENDA'),
            (3, 'DEVOLUÇÃO'),
            (4, 'PERDA'),
            (5, 'REPOSIÇÃO'),
            (6, 'PAGAMENTO');

            CREATE TABLE IF NOT EXISTS "formaPagamento"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL UNIQUE
            );
            INSERT OR IGNORE INTO formaPagamento (id, descricao) VALUES
            (1, 'DINHEIRO'),
            (2, 'PIX'),
            (3, 'CARTÃO DE DÉBITO'),
            (4, 'CARTÃO DE CRÉDITO'),
            (5, 'TRANSFERÊNCIA'),
            (6, 'CHEQUE');

            CREATE TABLE IF NOT EXISTS "taxasPagamento"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_formaPagamento INTEGER,
                descricao TEXT NOT NULL,
                taxa DECIMAL(3, 3) DEFAULT 0,
                FOREIGN KEY (id_formaPagamento) REFERENCES formaPagamento(id)
            );
            INSERT OR IGNORE INTO taxasPagamento (id_formaPagamento, descricao) VALUES
            (1,'DINHEIRO'),
            (2,'PIX'),
            (3,'CARTÃO DE DÉBITO'),
            (4,'CARTÃO DE CRÉDITO'),
            (5,'TRANSFERÊNCIA'),
            (6,'CHEQUE');


            CREATE TABLE IF NOT EXISTS "fluxosNotasEstoque" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tipoNota INTEGER NOT NULL,
                id_representante INTEGER NOT NULL,
                id_notaOrigem INTEGER REFERENCES "fluxosNotasEstoque" (id) ON DELETE SET NULL,
                data_vencimento DATE,
                FOREIGN KEY (id_tipoNota) REFERENCES tiposNotas (id),
                FOREIGN KEY (id_representante) REFERENCES entidades (id)
            );

            CREATE TABLE IF NOT EXISTS "fluxoPagamentoNotas"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_fluxo_nota INTEGER NOT NULL,
                id_forma_pagamento INTEGER NOT NULL,
                valor DECIMAL(10,3) NOT NULL,
                data_pagamento DATE NOT NULL,
                FOREIGN KEY (id_fluxo_nota) REFERENCES fluxosNotasEstoque(id) ON DELETE CASCADE,
                FOREIGN KEY (id_forma_pagamento) REFERENCES formaPagamento(id)
            );

            CREATE TABLE IF NOT EXISTS "fluxoEstoque"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tipoNota INTEGER NOT NULL,
                id_fluxo_nota INTEGER NOT NULL,
                id_produto INTEGER NOT NULL,
                quantidade DECIMAL(1000,3) NOT NULL,
                valorUnidario DECIMAL(10,3) NOT NULL,
                lucroTotal DECIMAL(10,3) DEFAULT 0,
                data DATE NOT NULL,
                FOREIGN KEY (id_tipoNota) REFERENCES tiposNotas(id),
                FOREIGN KEY (id_fluxo_nota) REFERENCES fluxosNotasEstoque(id) ON DELETE CASCADE,
                FOREIGN KEY (id_produto) REFERENCES produto(id)
            );

            CREATE TABLE IF NOT EXISTS "sexo"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL
            );
            INSERT OR IGNORE INTO sexo (id, descricao) VALUES
            (1, 'Masculino'),
            (2, 'Feminino'),
            (3, 'Outro');

            CREATE TABLE IF NOT EXISTS "pessoas"(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                nome TEXT NOT NULL,
                sexo INTEGER NOT NULL,
                FOREIGN KEY (sexo) REFERENCES sexo(id)
            );

            INSERT OR IGNORE INTO pessoas (id, nome, sexo) VALUES(1, 'NAO INFORMADO', 3);

            CREATE TABLE IF NOT EXISTS "empresas"(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                nome TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS "entidades"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_pessoa INTEGER,
                id_empresa INTEGER,
                fornecedor BOOLEAN DEFAULT 0,
                cliente BOOLEAN DEFAULT 0,
                funcionario BOOLEAN DEFAULT 0,
                FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
                FOREIGN KEY (id_empresa) REFERENCES empresas(id),
                CONSTRAINT chk_entidade_tem_dono CHECK (id_pessoa IS NOT NULL OR id_empresa IS NOT NULL),
                CONSTRAINT uq_entidade_completa UNIQUE (id, id_pessoa, id_empresa)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_individual 
            ON entidades (id_pessoa) 
            WHERE id_empresa IS NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS uq_empresa_individual 
            ON entidades (id_empresa) 
            WHERE id_pessoa IS NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_empresa_relacao 
            ON entidades (id_pessoa, id_empresa) 
            WHERE id_pessoa IS NOT NULL AND id_empresa IS NOT NULL;

            INSERT OR IGNORE INTO entidades (id_pessoa, id_empresa, fornecedor, cliente, funcionario)
            VALUES( 1, NULL, 0, 1, 0);

            CREATE TABLE IF NOT EXISTS "cargos"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL
            );
            INSERT OR IGNORE INTO cargos (id, descricao) VALUES
            (1, 'Dono'),
            (2, 'Sócio'),
            (3, 'Diretor'),
            (4, 'Gerente'),
            (5, 'Supervisor'),
            (6, 'Vendedor'),
            (7, 'Operador de Caixa'),
            (8, 'Atendente'),
            (9, 'Comprador'),
            (10, 'Estoquista'),
            (11, 'Almoxarife'),
            (12, 'Financeiro'),
            (13, 'Contador'),
            (14, 'Recursos Humanos'),
            (15, 'Marketing'),
            (16, 'Tecnologia da Informação'),
            (17, 'Motorista'),
            (18, 'Entregador'),
            (19, 'Auxiliar Administrativo'),
            (20, 'Secretária');

            CREATE TABLE IF NOT EXISTS "entidades_cargos"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_entidade INTEGER NOT NULL,
                id_cargo INTEGER NOT NULL,
                FOREIGN KEY (id_entidade) REFERENCES entidades(id) ON DELETE CASCADE,
                FOREIGN KEY (id_cargo) REFERENCES cargos(id)
            );

            CREATE TRIGGER IF NOT EXISTS tgr_garante_empresa_insert
            BEFORE INSERT ON entidades_cargos
            FOR EACH ROW
            BEGIN
                SELECT RAISE(ABORT, 'Erro: A entidade informada nao pertence a uma empresa.')
                WHERE (SELECT id_empresa FROM entidades WHERE id = NEW.id_entidade) IS NULL;
            END;

            CREATE TRIGGER IF NOT EXISTS tgr_garante_empresa_update
            BEFORE UPDATE ON entidades_cargos
            FOR EACH ROW
            BEGIN
                SELECT RAISE(ABORT, 'Erro: A entidade informada nao pertence a uma empresa.')
                WHERE (SELECT id_empresa FROM entidades WHERE id = NEW.id_entidade) IS NULL;
            END;

            CREATE TABLE IF NOT EXISTS "tipos_registros"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL
            );

            INSERT OR IGNORE INTO tipos_registros (id, descricao) VALUES
            (1, 'Email'),
            (2, 'Telefone'),
            (3, 'Celular'),
            (4, 'Facebook'),
            (5, 'Instagram'),
            (6, 'Twitter'),
            (7, 'LinkedIn'),
            (8, 'Outro');

            CREATE TABLE IF NOT EXISTS "registro"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tipos_registros INTEGER NOT NULL,
                id_entidade INTEGER NOT NULL,
                registro TEXT NOT NULL,
                FOREIGN KEY (id_tipos_registros) REFERENCES tipos_registros(id),
                FOREIGN KEY (id_entidade) REFERENCES entidades(id)
            );

            CREATE TABLE IF NOT EXISTS "snapshot_sazonal"(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_fluxo_nota INTEGER NOT NULL,
                data_registro DATE NOT NULL,
                temperatura_atual DECIMAL(5,2),
                temperatura_min_semana DECIMAL(5,2),
                temperatura_max_semana DECIMAL(5,2),
                precipitacao_mm DECIMAL(10,2),
                precipitacao_previsao_semana DECIMAL(10,2),
                indicador_clima TEXT CHECK(indicador_clima IN ('FRIO','QUENTE','AMENO')),
                nivel_rio_atual DECIMAL(15,2),
                nivel_rio_previsao_semana DECIMAL(15,2),
                indicador_rio TEXT CHECK(indicador_rio IN ('SECA','NORMAL','CHEIA')),
                indicador_chuva TEXT CHECK(indicador_chuva IN ('SECO','MODERADO','CHUVOSO')),
                qtd_eventos_proximos INTEGER DEFAULT 0,
                FOREIGN KEY (id_fluxo_nota) REFERENCES fluxosNotasEstoque(id) ON DELETE CASCADE
            );

            -- Views SQL para facilitar JOINs
            CREATE VIEW IF NOT EXISTS vw_produto_completo AS
            SELECT p.*, um.descricao as unidade_descricao, um.fatorConjunto
            FROM produto p
            JOIN unidadeMedida um ON p.unidadeMedida = um.id;

            CREATE VIEW IF NOT EXISTS vw_entidade_completa AS
            SELECT e.id, e.fornecedor, e.cliente, e.funcionario,
                   p.id as pessoa_id, p.nome as pessoa_nome, p.sexo as pessoa_sexo,
                   emp.id as empresa_id, emp.nome as empresa_nome
            FROM entidades e
            LEFT JOIN pessoas p ON e.id_pessoa = p.id
            LEFT JOIN empresas emp ON e.id_empresa = emp.id;

            CREATE VIEW IF NOT EXISTS vw_fluxo_estoque_completo AS
            SELECT fe.*, p.nome as produto_nome, tn.descricao as tipo_nota,
                   fn.id_representante, fn.data_vencimento, fn.id_notaOrigem
            FROM fluxoEstoque fe
            JOIN produto p ON fe.id_produto = p.id
            JOIN tiposNotas tn ON fe.id_tipoNota = tn.id
            JOIN fluxosNotasEstoque fn ON fe.id_fluxo_nota = fn.id;

            CREATE VIEW IF NOT EXISTS vw_resumo_vendas_produto AS
            SELECT fe.id_produto, p.nome as produto_nome,
                   SUM(fe.quantidade) as total_vendido,
                   SUM(fe.valorUnidario * fe.quantidade) as receita_total,
                   SUM(fe.lucroTotal) as lucro_total,
                   COUNT(*) as qtd_transacoes
            FROM fluxoEstoque fe
            JOIN produto p ON fe.id_produto = p.id
            WHERE fe.id_tipoNota = 2
            GROUP BY fe.id_produto;

            CREATE VIEW IF NOT EXISTS vw_analise_sazonal AS
            SELECT ss.*, fe.id_produto, p.nome as produto_nome,
                   fe.quantidade, fe.valorUnidario, fe.lucroTotal as lucro_item,
                   tn.descricao as tipo_nota
            FROM snapshot_sazonal ss
            JOIN fluxosNotasEstoque fn ON ss.id_fluxo_nota = fn.id
            JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
            JOIN produto p ON fe.id_produto = p.id
            JOIN tiposNotas tn ON fn.id_tipoNota = tn.id;

            CREATE VIEW IF NOT EXISTS vw_pagamentos_nota AS
            SELECT fp.*, fm.descricao as forma_descricao,
                   fn.id_tipoNota, tn.descricao as tipo_nota
            FROM fluxoPagamentoNotas fp
            JOIN formaPagamento fm ON fp.id_forma_pagamento = fm.id
            JOIN fluxosNotasEstoque fn ON fp.id_fluxo_nota = fn.id
            JOIN tiposNotas tn ON fn.id_tipoNota = tn.id;
            """)

            conn.commit()


BancoDB.inicializar_banco()