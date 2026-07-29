import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        p.receita,
        u.descricao as unidade
    FROM produto p
    LEFT JOIN unidadeMedida u ON p.unidadeMedida = u.id
''')
for r in cursor.fetchall():
    d = dict(r)
    pid = d['id']
    # Check if this product has a recipe (ingredients)
    cursor.execute('SELECT id_ingrediente, quantidade FROM receita WHERE id_produto_composto = ?', (pid,))
    ingredientes = cursor.fetchall()
    if ingredientes:
        print(f"COMPOSTO: ID {pid} - {d['nome']} | Ingredientes: {[dict(i) for i in ingredientes]}")
    else:
        print(f"SIMPLES: ID {pid} - {d['nome']}")
