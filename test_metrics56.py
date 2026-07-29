import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('PRAGMA table_info(receita)')
for r in cursor.fetchall():
    print(r)
