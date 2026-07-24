import sqlite3

def check_db():
    conn = sqlite3.connect("c:/workspace/PDV_Sazonal_Python/databaseSazonalizei.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- FORNECEDORES ---")
    cursor.execute("SELECT * FROM vw_entidade_completa WHERE fornecedor = 1")
    for r in cursor.fetchall():
        print(dict(r))
        
    print("\n--- PRODUTOS COM RECEITA ---")
    cursor.execute("SELECT * FROM produto WHERE receita = 1")
    for r in cursor.fetchall():
        print(dict(r))
        
    print("\n--- RECEITAS ---")
    cursor.execute("SELECT * FROM receita")
    for r in cursor.fetchall():
        print(dict(r))

if __name__ == '__main__':
    check_db()
