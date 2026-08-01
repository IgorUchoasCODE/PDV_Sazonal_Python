import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

query = '''
SELECT 
    fne.id as id_nota,
    COALESCE(emp.nome, pes.nome, 'Desconhecido') as fornecedor
FROM fluxosNotasEstoque fne
LEFT JOIN entidades ent ON fne.id_representante = ent.id
LEFT JOIN empresas emp ON ent.id_empresa = emp.id
LEFT JOIN pessoas pes ON ent.id_pessoa = pes.id
'''
cursor.execute(query)
print("Fornecedores:")
for r in cursor.fetchall():
    print(dict(r))
