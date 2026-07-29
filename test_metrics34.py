import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE name="vw_analise_sazonal"')
print("vw_analise_sazonal:", cursor.fetchone())

cursor.execute('''
    SELECT 
        f.id_produto,
        p.nome,
        s.indicador_clima,
        s.indicador_chuva,
        s.indicador_rio,
        SUM(ABS(f.quantidade)) as qtd_total,
        SUM(f.lucroTotal) as lucro_total
    FROM fluxoEstoque f
    JOIN produto p ON f.id_produto = p.id
    LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
    WHERE f.id_tipoNota = 2
    GROUP BY f.id_produto, s.indicador_clima
''')
for r in cursor.fetchall()[:10]:
    print(r)
