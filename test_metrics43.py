import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

print("--- TIPOS DE NOTAS ---")
cursor.execute('SELECT * FROM tiposNotas')
for r in cursor.fetchall():
    print(r)

print("\n--- USER QUERY OUTPUT ---")
cursor.execute('''
    SELECT 
        p.nome AS Produto, 
        SUM(CASE WHEN f.id_tipoNota IN (1, 3, 5) THEN f.quantidade ELSE -f.quantidade END) * 12 AS Cartelas_Disponiveis
    FROM fluxoEstoque f
    JOIN produto p ON f.id_produto = p.id
    GROUP BY p.nome
    ORDER BY p.nome
''')
for r in cursor.fetchall():
    print(r)

print("\n--- SIMPLE SUM(quantidade) BY TIPO NOTA ---")
cursor.execute('''
    SELECT p.nome, f.id_tipoNota, SUM(f.quantidade)
    FROM fluxoEstoque f
    JOIN produto p ON f.id_produto = p.id
    GROUP BY p.nome, f.id_tipoNota
''')
for r in cursor.fetchall():
    print(r)
