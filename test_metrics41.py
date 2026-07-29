import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT * FROM vw_resumo_vendas_produto')
for r in cursor.fetchall():
    print(r)
