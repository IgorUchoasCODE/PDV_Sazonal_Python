import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

print("--- INDICADOR RIO ---")
cursor.execute('''
    SELECT 
        COALESCE(s.indicador_rio, 'NORMAL') as rio,
        COUNT(*),
        MIN(s.nivel_rio_atual),
        MAX(s.nivel_rio_atual)
    FROM fluxoEstoque f
    LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
    GROUP BY s.indicador_rio
''')
for r in cursor.fetchall():
    print(r)

print("\n--- INDICADOR CHUVA ---")
cursor.execute('''
    SELECT 
        COALESCE(s.indicador_chuva, 'SECO') as chuva,
        COUNT(*)
    FROM fluxoEstoque f
    LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
    GROUP BY s.indicador_chuva
''')
for r in cursor.fetchall():
    print(r)
