import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT id, nome FROM produto')
for r in cursor.fetchall():
    print(r)
