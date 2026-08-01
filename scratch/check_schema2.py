import sqlite3
conn = sqlite3.connect('databaseSazonalizei.db')
c = conn.cursor()
c.execute("PRAGMA table_info(fluxosNotasEstoque);")
print("fluxosNotasEstoque:", c.fetchall())
c.execute("PRAGMA table_info(fluxoEstoque);")
print("fluxoEstoque:", c.fetchall())
c.execute("PRAGMA table_info(produto);")
print("produto:", c.fetchall())
