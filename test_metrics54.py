import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        COALESCE(SUM(CASE WHEN fe.id_tipoNota IN (1, 3, 5) THEN fe.quantidade ELSE -fe.quantidade END), 0) as estoque_caixas,
        COALESCE(SUM(CASE WHEN fe.id_tipoNota IN (1, 3, 5) THEN fe.quantidade ELSE -fe.quantidade END) * 12, 0) as estoque_cartelas,
        COALESCE(SUM(CASE WHEN fe.id_tipoNota = 2 THEN ABS(fe.quantidade) ELSE 0 END), 0) as qtd_vendida,
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
    LEFT JOIN fluxoEstoque fe ON fe.id_produto = p.id
    GROUP BY p.id, p.nome
''')
for r in cursor.fetchall():
    print(r)
