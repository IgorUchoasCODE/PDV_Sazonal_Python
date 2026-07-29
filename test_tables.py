import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
print([row[0] for row in cursor.fetchall()])
