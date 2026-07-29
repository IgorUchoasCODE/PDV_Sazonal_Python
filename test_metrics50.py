import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT id_produto, id_tipoNota, COUNT(*), SUM(quantidade) FROM fluxoEstoque WHERE id_produto IN (6,7,8,9,10) GROUP BY id_produto, id_tipoNota')
for r in cursor.fetchall():
    print(r)
