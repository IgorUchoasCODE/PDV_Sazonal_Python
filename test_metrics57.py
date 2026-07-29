import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        p.receita
    FROM produto p
''')
produtos = cursor.fetchall()
for r in produtos:
    d = dict(r)
    pid = d['id']
    cursor.execute('SELECT id_ingrediente, qntdd FROM receita WHERE id_produto = ?', (pid,))
    ingredientes = cursor.fetchall()
    if ingredientes:
        print(f"COMPOSTO: ID {pid} - {d['nome']} | Ingredientes: {[dict(i) for i in ingredientes]}")
    else:
        print(f"SIMPLES: ID {pid} - {d['nome']}")
