import sqlite3
import datetime
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        id_produto, id_nota, qtd_inicial, qtd_disponivel, custo_unitario, data_entrada, p.diasDuraveis
    FROM fluxoEstoque fe
    JOIN produto p ON p.id = fe.id_produto
    WHERE id_tipoNota IN (1,3,5)
    LIMIT 5
''')
for r in cursor.fetchall():
    print(dict(r))
