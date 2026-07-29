import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('''
    SELECT 
        id_produto, 
        quantidade, 
        valorUnidario, 
        lucroTotal 
    FROM fluxoEstoque 
    WHERE id_tipoNota = 2
    LIMIT 5
''')
for r in cursor.fetchall():
    print(r)
