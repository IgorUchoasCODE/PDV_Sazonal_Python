import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT SUM(lucroTotal) FROM fluxoEstoque WHERE id_tipoNota = 4')
print("Perdas Lucro:", cursor.fetchone()[0])
