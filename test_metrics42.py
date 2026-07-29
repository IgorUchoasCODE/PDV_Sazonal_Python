import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        COALESCE(SUM(ABS(fe.quantidade)), 0) as qtd_vendida,
        COALESCE(SUM(fe.lucroTotal), 0) as lucro_total,
        (
            SELECT s.indicador_clima 
            FROM snapshot_sazonal s 
            JOIN fluxosNotasEstoque fn ON s.id_fluxo_nota = fn.id 
            JOIN fluxoEstoque fe2 ON fe2.id_fluxo_nota = fn.id 
            WHERE fe2.id_produto = p.id AND fn.id_tipoNota = 2
            GROUP BY s.indicador_clima 
            ORDER BY SUM(ABS(fe2.quantidade)) DESC 
            LIMIT 1
        ) as clima_pico
    FROM produto p
    LEFT JOIN fluxoEstoque fe ON fe.id_produto = p.id AND fe.id_tipoNota = 2
    GROUP BY p.id, p.nome
''')
for r in cursor.fetchall():
    print(r)
