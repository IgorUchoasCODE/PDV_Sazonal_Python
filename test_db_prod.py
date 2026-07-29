import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()
cursor.execute('PRAGMA table_info(produto)')
for row in cursor.fetchall():
    print(dict(row))
