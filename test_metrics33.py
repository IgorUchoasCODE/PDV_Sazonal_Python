import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE name="vw_entidade_completa"')
print(cursor.fetchone()[0])
