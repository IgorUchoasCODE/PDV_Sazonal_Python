import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

print("--- DISTINCT SNAPSHOT SAZONAL VALUES ---")
cursor.execute('''
    SELECT 
        indicador_clima,
        indicador_chuva,
        indicador_rio,
        AVG(temperatura),
        MIN(temperatura),
        MAX(temperatura),
        COUNT(*)
    FROM snapshot_sazonal
    GROUP BY indicador_clima
''')
for r in cursor.fetchall():
    print(r)

print("\n--- SAMPLE ROWS FROM SNAPSHOT_SAZONAL ---")
cursor.execute('SELECT * FROM snapshot_sazonal LIMIT 10')
for r in cursor.fetchall():
    print(r)
