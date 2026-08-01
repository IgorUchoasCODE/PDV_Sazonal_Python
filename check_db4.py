import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(entidades)")
    print("entidades columns:", [dict(c) for c in cursor.fetchall()])
    cursor.execute("SELECT * FROM entidades LIMIT 5")
    print("entidades data:", [dict(r) for r in cursor.fetchall()])
    
    cursor.execute("PRAGMA table_info(pessoas)")
    print("pessoas columns:", [dict(c) for c in cursor.fetchall()])
    
    cursor.execute("PRAGMA table_info(empresas)")
    print("empresas columns:", [dict(c) for c in cursor.fetchall()])
except Exception as e: print(e)
