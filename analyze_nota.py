import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sazonal_web.settings')
django.setup()
from br.com.pdv.src.BDD.bancodb import BancoDB

with BancoDB.obter_conexao() as conn:
    cur = conn.cursor()

    # Nota 933 header
    cur.execute('SELECT * FROM fluxosNotasEstoque WHERE id = 933')
    nota = cur.fetchone()
    print('NOTA 933:', dict(nota) if nota else 'NAO ENCONTRADA')

    # fluxoEstoque entries for nota 933
    cur.execute('''
        SELECT fe.*, p.nome as nome_produto
        FROM fluxoEstoque fe
        JOIN produto p ON p.id = fe.id_produto
        WHERE fe.id_fluxo_nota = 933
    ''')
    rows = cur.fetchall()
    print('\nFLUXO ESTOQUE nota 933:')
    for r in rows:
        d = dict(r)
        total_val = d['quantidade'] * d['valorUnidario']
        print(f"  prod={d['id_produto']} ({d['nome_produto']}) | qtd={d['quantidade']} | valorUnit={d['valorUnidario']} | total_val={total_val:.4f} | lucro={d['lucroTotal']}")

    # Produto 113
    cur.execute('SELECT * FROM produto WHERE id = 113')
    p = cur.fetchone()
    if p:
        pd = dict(p)
        print(f"\nPRODUTO 113: {pd['nome']} | varejo={pd['varejo']}")

    # Receita do produto 113
    cur.execute('SELECT r.*, p.nome as nome_ingr FROM receita r JOIN produto p ON p.id = r.id_ingrediente WHERE r.id_produto = 113')
    rec = cur.fetchall()
    print('\nRECEITA 113:')
    for r in rec:
        d = dict(r)
        print(f"  ingrediente={d['id_ingrediente']} ({d['nome_ingr']}) qntdd={d['qntdd']}")

    # Custo medio de cada ingrediente (da compra)
    print('\nCUSTO MEDIO DOS INGREDIENTES (de compras, tipo 1):')
    cur.execute('''
        SELECT fe.id_produto, p.nome, AVG(fe.valorUnidario) as custo_medio_compra, SUM(fe.quantidade) as total_comprado
        FROM fluxoEstoque fe
        JOIN produto p ON p.id = fe.id_produto
        WHERE fe.id_tipoNota = 1 AND fe.id_produto IN (110, 111, 112)
        GROUP BY fe.id_produto
    ''')
    for r in cur.fetchall():
        d = dict(r)
        print(f"  prod={d['id_produto']} ({d['nome']}) | custo_medio={d['custo_medio_compra']:.4f} | total_comprado={d['total_comprado']:.4f}")

    # Check nota de compra origem dos ingredientes usados na nota 933
    print('\nNOTA DE ORIGEM dos fluxos da nota 933:')
    cur.execute('SELECT fe.id_notaOrigem, fe.id_produto, fn.id_tipoNota FROM fluxoEstoque fe JOIN fluxosNotasEstoque fn ON fn.id = fe.id_notaOrigem WHERE fe.id_fluxo_nota = 933')
    for r in cur.fetchall():
        d = dict(r)
        print(f"  notaOrigem={d['id_notaOrigem']} | prod={d['id_produto']} | tipoNota={d['id_tipoNota']}")
