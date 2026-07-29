import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('''
    SELECT 
        id_notaOrigem, 
        id_produto, 
        quantidade, 
        valorUnidario, 
        lucroTotal 
    FROM fluxoEstoque 
    WHERE id_tipoNota = 2 
    ORDER BY id_notaOrigem ASC
    LIMIT 5
''')
for r in cursor.fetchall():
    print(r)
