import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        SUM(CASE WHEN f.id_tipoNota = 1 THEN f.quantidade ELSE 0 END) as compras,
        SUM(CASE WHEN f.id_tipoNota = 2 THEN f.quantidade ELSE 0 END) as vendas,
        SUM(CASE WHEN f.id_tipoNota = 4 THEN f.quantidade ELSE 0 END) as perdas
    FROM produto p
    LEFT JOIN fluxoEstoque f ON f.id_produto = p.id
    GROUP BY p.id, p.nome
''')
rows = cursor.fetchall()
for r in rows:
    pid, nome, compras, vendas, perdas = r
    # Let's check formulas:
    # 1. Compras - Vendas - Perdas
    f1 = compras - vendas - perdas
    # 2. Vendas - Compras
    f2 = vendas - compras
    # 3. Compras - Vendas * 1.63?
    # 4. What about in Cartelas? 1 Caixa = 12 Cartelas
    # Let's check:
    # If Vendas in cartelas = vendas * 12 or compras in caixas...
    print(f"ID {pid} - {nome}:")
    print(f"   Compras: {compras:.2f}, Vendas: {vendas:.2f}, Perdas: {perdas:.2f}")
    print(f"   Compras - Vendas - Perdas: {f1:.2f}")
    print(f"   (Compras - Vendas - Perdas) * 12: {f1 * 12:.2f}")
    print(f"   Compras - (Vendas * 12): {compras - vendas*12:.2f}")
    print(f"   (Compras / 12) - Vendas: {compras/12 - vendas:.2f}")
