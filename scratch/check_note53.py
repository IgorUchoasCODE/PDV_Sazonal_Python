import sqlite3
conn = sqlite3.connect('databaseSazonalizei.db')
c = conn.cursor()
c.execute("SELECT * FROM fluxoEstoque WHERE id_fluxo_nota = 53 AND id_tipoNota = 4;")
rows = c.fetchall()
for r in rows:
    print(r)
