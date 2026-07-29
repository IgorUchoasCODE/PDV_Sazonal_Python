import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('PRAGMA table_info(produto)')
for row in cursor.fetchall():
    print(row)
