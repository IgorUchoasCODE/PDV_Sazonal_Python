import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('''
    SELECT SUM(lucroTotal) FROM fluxoEstoque WHERE id_tipoNota = 2
''')
print("SUM(lucroTotal) SQL:", cursor.fetchone()[0])
