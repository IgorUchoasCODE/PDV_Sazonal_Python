from enum import Enum
from br.com.pdv.src.BDD.bancodb import BancoDB

class QueryBase(Enum):
    def executar(self, *args):
        """
        Executa comandos DML (INSERT, UPDATE, DELETE).
        Retorna o ID gerado (para INSERT) ou o número de linhas afetadas.
        Garante que qualquer texto (string) enviado seja salvo em MAUSCULO.
        """
        # Converte todos os argumentos que forem do tipo texto (str) para MAUSCULO
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

    PESSOA = "INSERT INTO pessoas (nome, sexo) VALUES (?, ?)"
    EMPRESA = "INSERT INTO empresas (nome) VALUES (?)"
    ENTIDADE = "INSERT INTO entidades (id_pessoa, id_empresa, fornecedor, cliente, funcionario) VALUES (?, ?, ?, ?, ?)"
    ENTIDADE_CARGO = "INSERT INTO entidades_cargos (id_entidade, id_cargo) VALUES (?, ?)"
    REGISTRO = "INSERT INTO registro (id_tipos_registros, id_entidade, registro) VALUES (?, ?, ?)"
    FLUXO_NOTA_ESTOQUE = "INSERT INTO fluxosNotasEstoque (id_tipoNota, id_representante, id_notaOrigem, data_vencimento) VALUES (?, ?, ?, ?)"
    FLUXO_PAGAMENTO_NOTA = "INSERT INTO fluxoPagamentoNotas (id_fluxo_nota, id_forma_pagamento, valor, data_pagamento) VALUES (?, ?, ?, ?)"
    FLUXO_ESTOQUE = "INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data) VALUES (?, ?, ?, ?, ?, ?, ?)"
    TAXA_PAGAMENTO = "INSERT INTO taxasPagamento (id_formaPagamento, descricao, taxa) VALUES (?, ?, ?)"
    SNAPSHOT_SAZONAL = """INSERT INTO snapshot_sazonal 
        (id_fluxo_nota, data_registro, temperatura_atual, temperatura_min_semana, temperatura_max_semana,
         precipitacao_mm, precipitacao_previsao_semana, indicador_clima,
         nivel_rio_atual, nivel_rio_previsao_semana, indicador_rio,
         indicador_chuva, qtd_eventos_proximos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""


class SELECT(QueryBase):
    PRODUTO_POR_ID = "SELECT * FROM produto WHERE id = ?"
    PRODUTO_TODOS = "SELECT * FROM produto"
    
    UNIDADE_MEDIDA_TODOS = "SELECT * FROM unidadeMedida"
    UNIDADE_MEDIDA_POR_ID = "SELECT * FROM unidadeMedida WHERE id = ?"
    
    RECEITA_POR_PRODUTO = "SELECT * FROM receita WHERE id_produto = ?"

    PESSOA_POR_ID = "SELECT * FROM pessoas WHERE id = ?"
    PESSOA_TODOS = "SELECT * FROM pessoas"
    
    EMPRESA_POR_ID = "SELECT * FROM empresas WHERE id = ?"
    EMPRESA_TODOS = "SELECT * FROM empresas"
    
    ENTIDADE_POR_ID = "SELECT * FROM entidades WHERE id = ?"
    ENTIDADE_TODOS = "SELECT * FROM entidades"
    
    REGISTRO_POR_ENTIDADE = "SELECT * FROM registro WHERE id_entidade = ?"
    CARGO_POR_ENTIDADE = "SELECT * FROM entidades_cargos WHERE id_entidade = ?"
    
    FLUXO_NOTA_ESTOQUE_POR_ID = "SELECT * FROM fluxosNotasEstoque WHERE id = ?"
    FLUXO_NOTA_ESTOQUE_TODOS = "SELECT * FROM fluxosNotasEstoque"
    
    FLUXO_PAGAMENTO_POR_NOTA = "SELECT * FROM fluxoPagamentoNotas WHERE id_fluxo_nota = ?"
    FLUXO_ESTOQUE_POR_NOTA = "SELECT * FROM fluxoEstoque WHERE id_fluxo_nota = ?"
    
    TIPO_NOTA_TODOS = "SELECT * FROM tiposNotas"
    FORMA_PAGAMENTO_TODOS = "SELECT * FROM formaPagamento"
    TAXA_PAGAMENTO_TODOS = "SELECT * FROM taxasPagamento"
    SEXO_TODOS = "SELECT * FROM sexo"
    CARGO_TODOS = "SELECT * FROM cargos"
    TIPO_REGISTRO_TODOS = "SELECT * FROM tipos_registros"

    # Snapshot Sazonal
    SNAPSHOT_POR_NOTA = "SELECT * FROM snapshot_sazonal WHERE id_fluxo_nota = ?"
    SNAPSHOT_TODOS = "SELECT * FROM snapshot_sazonal"

    # Views integradas
    VW_PRODUTO_COMPLETO_TODOS = "SELECT * FROM vw_produto_completo"
    VW_PRODUTO_COMPLETO_POR_ID = "SELECT * FROM vw_produto_completo WHERE id = ?"
    VW_ENTIDADE_COMPLETA_TODOS = "SELECT * FROM vw_entidade_completa"
    VW_ENTIDADE_COMPLETA_POR_ID = "SELECT * FROM vw_entidade_completa WHERE id = ?"
    VW_FLUXO_ESTOQUE_COMPLETO = "SELECT * FROM vw_fluxo_estoque_completo"
    VW_FLUXO_ESTOQUE_POR_NOTA = "SELECT * FROM vw_fluxo_estoque_completo WHERE id_fluxo_nota = ?"
    VW_RESUMO_VENDAS = "SELECT * FROM vw_resumo_vendas_produto"
    VW_RESUMO_VENDAS_POR_PRODUTO = "SELECT * FROM vw_resumo_vendas_produto WHERE id_produto = ?"
    VW_ANALISE_SAZONAL = "SELECT * FROM vw_analise_sazonal"
    VW_ANALISE_SAZONAL_POR_PRODUTO = "SELECT * FROM vw_analise_sazonal WHERE id_produto = ?"
    VW_PAGAMENTOS_NOTA = "SELECT * FROM vw_pagamentos_nota WHERE id_fluxo_nota = ?"

    # Queries integradas para produto (molde sem valores e com valores)
    PRODUTO_MOLDE = "SELECT id, nome, diasDuraveis, unidade_descricao, fatorConjunto FROM vw_produto_completo WHERE id = ?"
    PRODUTO_MOLDES_TODOS = "SELECT id, nome, diasDuraveis, unidade_descricao, fatorConjunto FROM vw_produto_completo"

    # Estoque atual por produto (saldo de entradas - saídas)
    ESTOQUE_POR_PRODUTO = """SELECT fe.id_produto, p.nome,
        SUM(CASE WHEN fe.id_tipoNota = 1 THEN fe.quantidade ELSE 0 END) as total_entrada,
        SUM(CASE WHEN fe.id_tipoNota = 2 THEN fe.quantidade ELSE 0 END) as total_venda,
        SUM(CASE WHEN fe.id_tipoNota = 3 THEN fe.quantidade ELSE 0 END) as total_devolucao,
        SUM(CASE WHEN fe.id_tipoNota = 4 THEN fe.quantidade ELSE 0 END) as total_perda,
        SUM(CASE WHEN fe.id_tipoNota = 5 THEN fe.quantidade ELSE 0 END) as total_reposicao
        FROM fluxoEstoque fe
        JOIN produto p ON fe.id_produto = p.id
        WHERE fe.id_produto = ?
        GROUP BY fe.id_produto"""

    ESTOQUE_TODOS = """SELECT fe.id_produto, p.nome,
        SUM(CASE WHEN fe.id_tipoNota = 1 THEN fe.quantidade ELSE 0 END) as total_entrada,
        SUM(CASE WHEN fe.id_tipoNota = 2 THEN fe.quantidade ELSE 0 END) as total_venda,
        SUM(CASE WHEN fe.id_tipoNota = 3 THEN fe.quantidade ELSE 0 END) as total_devolucao,
        SUM(CASE WHEN fe.id_tipoNota = 4 THEN fe.quantidade ELSE 0 END) as total_perda,
        SUM(CASE WHEN fe.id_tipoNota = 5 THEN fe.quantidade ELSE 0 END) as total_reposicao
        FROM fluxoEstoque fe
        JOIN produto p ON fe.id_produto = p.id
        GROUP BY fe.id_produto"""

    ESTOQUE_COMPRA_PRODUTO_TODOS = """select
        fe.id_fluxo_nota,
        fe.id_produto,
        fe."valorUnidario",
        fe.quantidade,
        fe."data"
        from "fluxoEstoque" as fe
        WHERE "id_tipoNota" = 1;"""

    ESTOQUE_VENDA_PRODUTO_TODOS = """select
        fe.id_fluxo_nota,
        fe.id_produto,
        fe."valorUnidario",
        fe.quantidade,
        fe."data"
        from "fluxoEstoque" as fe
        WHERE "id_tipoNota" = 2;"""
    
    ESTOQUE_DEVOLUCAO_PRODUTO_TODOS = """select
        fe.id_fluxo_nota,
        fe.id_produto,
        fe."valorUnidario",
        fe.quantidade,
        fe."data"
        from "fluxoEstoque" as fe
        WHERE "id_tipoNota" = 3;"""

    ESTOQUE_PERDA_PRODUTO_TODOS = """select
        fe.id_fluxo_nota,
        fe.id_produto,
        fe."valorUnidario",
        fe.quantidade,
        fe."data"
        from "fluxoEstoque" as fe
        WHERE "id_tipoNota" = 4;"""

    ESTOQUE_REPOSICAO_PRODUTO_TODOS = """select
        fe.id_fluxo_nota,
        fe.id_produto,
        fe."valorUnidario",
        fe.quantidade,
        fe."data"
        from "fluxoEstoque" as fe
        WHERE "id_tipoNota" = 5;"""

    # Fornecedores e Clientes (via view entidade completa)
    FORNECEDORES_TODOS = "SELECT * FROM vw_entidade_completa WHERE fornecedor = 1"
    CLIENTES_TODOS = "SELECT * FROM vw_entidade_completa WHERE cliente = 1"


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

    PESSOA = "UPDATE pessoas SET nome = ?, sexo = ? WHERE id = ?"
    EMPRESA = "UPDATE empresas SET nome = ? WHERE id = ?"
    ENTIDADE = "UPDATE entidades SET id_pessoa = ?, id_empresa = ?, fornecedor = ?, cliente = ?, funcionario = ? WHERE id = ?"
    REGISTRO = "UPDATE registro SET id_tipos_registros = ?, registro = ? WHERE id = ?"
    ENTIDADE_CARGO = "UPDATE entidades_cargos SET id_cargo = ? WHERE id = ?"
    TAXA_PAGAMENTO = "UPDATE taxasPagamento SET id_formaPagamento = ?, descricao = ?, taxa = ? WHERE id = ?"
    SNAPSHOT_SAZONAL = """UPDATE snapshot_sazonal SET 
        temperatura_atual = ?, temperatura_min_semana = ?, temperatura_max_semana = ?,
        precipitacao_mm = ?, precipitacao_previsao_semana = ?, indicador_clima = ?,
        nivel_rio_atual = ?, nivel_rio_previsao_semana = ?, indicador_rio = ?,
        indicador_chuva = ?, qtd_eventos_proximos = ?
        WHERE id = ?"""


class DELETE(QueryBase):
    PRODUTO = "DELETE FROM produto WHERE id = ?"
    UNIDADE_MEDIDA = "DELETE FROM unidadeMedida WHERE id = ?"
    RECEITA_POR_PRODUTO = "DELETE FROM receita WHERE id_produto = ?"

    PESSOA = "DELETE FROM pessoas WHERE id = ?"
    EMPRESA = "DELETE FROM empresas WHERE id = ?"
    ENTIDADE = "DELETE FROM entidades WHERE id = ?"
    REGISTRO = "DELETE FROM registro WHERE id = ?"
    REGISTRO_POR_ENTIDADE = "DELETE FROM registro WHERE id_entidade = ?"
    ENTIDADE_CARGO = "DELETE FROM entidades_cargos WHERE id = ?"
    ENTIDADE_CARGO_POR_ENTIDADE = "DELETE FROM entidades_cargos WHERE id_entidade = ?"
    
    FLUXO_NOTA_ESTOQUE = "DELETE FROM fluxosNotasEstoque WHERE id = ?"
    FLUXO_PAGAMENTO_NOTA = "DELETE FROM fluxoPagamentoNotas WHERE id_fluxo_nota = ?"
    FLUXO_ESTOQUE = "DELETE FROM fluxoEstoque WHERE id_fluxo_nota = ?"
    TAXA_PAGAMENTO = "DELETE FROM taxasPagamento WHERE id = ?"
    SNAPSHOT_SAZONAL = "DELETE FROM snapshot_sazonal WHERE id = ?"
    SNAPSHOT_POR_NOTA = "DELETE FROM snapshot_sazonal WHERE id_fluxo_nota = ?"


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


if __name__ == "__main__":
    p =DB.SELECT.VW_PRODUTO_COMPLETO_POR_ID.buscar_um(3)
    print(p)
