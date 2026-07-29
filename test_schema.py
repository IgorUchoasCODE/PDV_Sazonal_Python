import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE name="fluxoEstoque";')
print(cursor.fetchone()[0])
