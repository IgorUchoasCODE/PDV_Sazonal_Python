import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('''
    SELECT SUM(lucroTotal) 
    FROM fluxoEstoque 
    WHERE id_tipoNota = 2
''')
print("SQL SUM(lucroTotal):", cursor.fetchone()[0])

cursor.execute('''
    SELECT lucroTotal, quantidade, valorUnidario
    FROM fluxoEstoque 
    WHERE id_tipoNota = 2
    LIMIT 5
''')
for r in cursor.fetchall():
    print(r)
