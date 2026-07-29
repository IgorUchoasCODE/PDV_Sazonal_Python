import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('PRAGMA table_info(snapshot_sazonal)')
for r in cursor.fetchall():
    print(r)
