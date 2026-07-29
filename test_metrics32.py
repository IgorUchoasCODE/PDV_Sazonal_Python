import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT name, type FROM sqlite_master WHERE type="view" OR type="table"')
for row in cursor.fetchall():
    print(row)
