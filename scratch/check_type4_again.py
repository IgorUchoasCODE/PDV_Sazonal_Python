import sqlite3
conn = sqlite3.connect('databaseSazonalizei.db')
c = conn.cursor()
c.execute("SELECT id_fluxo_nota, id_notaOrigem, data FROM fluxoEstoque WHERE id_tipoNota = 4")
for row in c.fetchall():
    print(row)
