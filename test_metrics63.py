import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

cursor.execute('''
    SELECT 
        indicador_clima,
        indicador_chuva,
        indicador_rio,
        AVG(temperatura_atual),
        MIN(temperatura_atual),
        MAX(temperatura_atual),
        COUNT(*)
    FROM snapshot_sazonal
    GROUP BY indicador_clima
''')
for r in cursor.fetchall():
    print(r)
