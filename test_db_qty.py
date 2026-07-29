import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()
cursor.execute('SELECT id_tipoNota, quantidade FROM fluxoEstoque WHERE id_tipoNota=2 LIMIT 10')
for row in cursor.fetchall():
    print(dict(row))
