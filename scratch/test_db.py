import sqlite3
conn = sqlite3.connect('databaseSazonalizei.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
row = c.execute('SELECT sql FROM sqlite_master WHERE type="view" AND name="vw_produto_completo"').fetchone()
print(row['sql'] if row else "Not found")
