import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()
cursor.execute('''
    SELECT 
        id_produto,
        SUM(CASE WHEN id_tipoNota IN (1, 3, 5) THEN quantidade ELSE 0 END) as entradas,
        SUM(CASE WHEN id_tipoNota NOT IN (1, 3, 5) THEN quantidade ELSE 0 END) as saidas
    FROM fluxoEstoque
    GROUP BY id_produto
''')
for row in cursor.fetchall():
    print(dict(row))
