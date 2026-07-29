import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()
cursor.execute('''
    SELECT 
        DATE(f.data) as dia,
        SUM(ABS(f.quantidade) * f.valorUnidario) as valor_venda,
        SUM(f.lucroTotal) as lucro_venda,
        MAX(s.nivel_rio_atual) as nivel_rio,
        MAX(s.temperatura_atual) as temperatura
    FROM fluxoEstoque f
    LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
    WHERE f.id_tipoNota = 2
    GROUP BY DATE(f.data)
    ORDER BY DATE(f.data) ASC
    LIMIT 10
''')
for row in cursor.fetchall():
    print(dict(row))
