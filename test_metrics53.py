import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        um.descricao as unidade_medida,
        COALESCE(um.fatorConjunto, 1) as fator,
        SUM(CASE WHEN f.id_tipoNota IN (1, 3, 5) THEN f.quantidade ELSE -f.quantidade END) as estoque_caixas,
        SUM(CASE WHEN f.id_tipoNota IN (1, 3, 5) THEN f.quantidade ELSE -f.quantidade END) * COALESCE(um.fatorConjunto, 12) as estoque_unidades
    FROM produto p
    JOIN fluxoEstoque f ON f.id_produto = p.id
    LEFT JOIN unidadeMedida um ON p.unidadeMedida = um.id
    GROUP BY p.id, p.nome
''')
for row in cursor.fetchall():
    print(row)
