import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

cursor.execute('''
    SELECT 
        s.temperatura_atual,
        ABS(fe.quantidade) as vol
    FROM snapshot_sazonal s
    JOIN fluxosNotasEstoque fn ON s.id_fluxo_nota = fn.id
    JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
    WHERE fn.id_tipoNota = 2
''')

soma_weighted = 0.0
total_vol = 0.0
soma_simple = 0.0
count_sales = 0

for temp, vol in cursor.fetchall():
    if temp:
        soma_weighted += temp * vol
        total_vol += vol
        soma_simple += temp
        count_sales += 1

print(f"BOGUS METHOD (soma_weighted / count_sales): {soma_weighted / count_sales:.2f}°C")
print(f"CORRECT WEIGHTED AVERAGE (soma_weighted / total_vol): {soma_weighted / total_vol:.2f}°C")
print(f"CORRECT SIMPLE AVERAGE (soma_simple / count_sales): {soma_simple / count_sales:.2f}°C")
