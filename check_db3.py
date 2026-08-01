import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r['name'] for r in cursor.fetchall()]
    print("Tables:", tables)
    
    if 'cliente' in tables:
        cursor.execute("PRAGMA table_info(cliente)")
        print("cliente columns:", [dict(c) for c in cursor.fetchall()])
        cursor.execute("SELECT * FROM cliente LIMIT 1")
        print("cliente data:", [dict(r) for r in cursor.fetchall()])
except Exception as e: print(e)
