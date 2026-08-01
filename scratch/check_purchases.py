import sqlite3
conn = sqlite3.connect('databaseSazonalizei.db')
c = conn.cursor()
c.execute("SELECT id_fluxo_nota, data, quantidade FROM fluxoEstoque WHERE id_tipoNota = 1 AND id_produto = (SELECT id FROM produto WHERE nome='CAIXA OVO BRANCO B') ORDER BY data DESC, id DESC;")
rows = c.fetchall()
for r in rows:
    print(r)
