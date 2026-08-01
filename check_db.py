import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("== TABELA fornecedor ==")
try:
    cursor.execute('PRAGMA table_info(fornecedor)')
    for r in cursor.fetchall(): print(dict(r))
except Exception as e: print(e)

print("== TABELA notas_compra ou similar ==")
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%nota%'")
    for r in cursor.fetchall():
        print(dict(r))
        cursor.execute(f"PRAGMA table_info({r['name']})")
        for c in cursor.fetchall(): print(dict(c))
except Exception as e: print(e)
