import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()
cursor.execute('''
    SELECT 
        DATE(n.data) as dia,
        SUM(n.valorTotal) as valor_venda,
        SUM(n.lucroTotal) as lucro_venda,
        s.nivel_rio_atual,
        s.indicador_clima,
        s.indicador_rio
    FROM fluxosNotasEstoque n
    LEFT JOIN snapshot_sazonal s ON s.id = n.snapshot_sazonal_id
    WHERE n.id_tipoNota = 2
    GROUP BY DATE(n.data)
    ORDER BY DATE(n.data) ASC
''')
for row in cursor.fetchall():
    print(dict(row))
