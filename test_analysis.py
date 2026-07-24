import sqlite3

def analyze_db():
    conn = sqlite3.connect("c:/workspace/PDV_Sazonal_Python/databaseSazonalizei.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fe.id_tipoNota, tn.descricao, fe.id_produto, fe.quantidade, fe.valorUnidario, fe.lucroTotal
        FROM fluxoEstoque fe
        JOIN tiposNotas tn ON fe.id_tipoNota = tn.id
        WHERE fe.id_tipoNota IN (3, 4, 5)
    """)
    rows = cursor.fetchall()
    print("Tipo Nota | Produto | Qtd | Valor Uni | Lucro Total")
    for r in rows:
        print(f"{r[1]} ({r[0]}) | {r[2]} | {r[3]} | {r[4]} | {r[5]}")

if __name__ == '__main__':
    analyze_db()
