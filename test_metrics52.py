import sqlite3, json
from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.inventoryManager import InventoryManager

InventoryManager.carregarTudo()
conn = BancoDB.obter_conexao()
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        p.id,
        p.nome,
        COALESCE(SUM(ABS(fe.quantidade)), 0) as qtd_vendida,
        COALESCE(SUM(fe.lucroTotal), 0) as lucro_total,
        (
            SELECT s.indicador_clima 
            FROM snapshot_sazonal s 
            JOIN fluxosNotasEstoque fn ON s.id_fluxo_nota = fn.id 
            JOIN fluxoEstoque fe2 ON fe2.id_fluxo_nota = fn.id 
            WHERE fe2.id_produto = p.id AND fn.id_tipoNota = 2
            GROUP BY s.indicador_clima 
            ORDER BY SUM(ABS(fe2.quantidade)) DESC 
            LIMIT 1
        ) as clima_pico
    FROM produto p
    LEFT JOIN fluxoEstoque fe ON fe.id_produto = p.id AND fe.id_tipoNota = 2
    GROUP BY p.id, p.nome
''')

for row in cursor.fetchall():
    pid = str(row['id'])
    nome = row['nome']
    pinfo = InventoryManager._mapaProdutos.get(pid, {})
    qtd_estoque = pinfo.get('quantidadeTotal', 0.0)
    print(f"ID {pid} | {nome} | estoque: {qtd_estoque}")
