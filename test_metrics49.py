import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

print("--- RECEITA TABLE ---")
cursor.execute('SELECT * FROM receita')
for r in cursor.fetchall():
    print(r)
