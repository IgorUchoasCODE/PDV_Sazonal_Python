import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, diasDuraveis FROM produto')
for r in cursor.fetchall():
    print(dict(r))
