import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE name="vw_resumo_vendas_produto"')
print(cursor.fetchone()[0])
