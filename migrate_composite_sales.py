"""
migrate_composite_sales.py
==========================
Reestrutura TODAS as notas de venda de produtos compostos:

ANTES (errado):
  fluxosNotasEstoque:
    nota X: tipo=2, cliente=C
  fluxoEstoque:
    nota X, produto_composto, venda=28, lucro=94.5
    nota X, ingrediente_1,    custo=1.5, lucro=0   <-- misturado!
    nota X, ingrediente_2,    custo=6.0, lucro=0
    nota X, ingrediente_3,    custo=0.8, lucro=0

DEPOIS (correto):
  fluxosNotasEstoque:
    nota X:  tipo=2, cliente=C, id_notaOrigem=NULL
    nota X1: tipo=2, cliente=C, id_notaOrigem=nota_compra_ingr1
    nota X2: tipo=2, cliente=C, id_notaOrigem=nota_compra_ingr2
    nota X3: tipo=2, cliente=C, id_notaOrigem=nota_compra_ingr3
  fluxoEstoque:
    nota X,  produto_composto, venda=28, lucro=94.5
    nota X1, ingrediente_1,   custo=1.5, lucro=0
    nota X2, ingrediente_2,   custo=6.0, lucro=0
    nota X3, ingrediente_3,   custo=0.8, lucro=0
  fluxoPagamentoNotas:
    nota X:  forma=1, valor=total_vendido
    nota X1: forma=1, valor=0   (rastreabilidade)
    nota X2: forma=1, valor=0
    nota X3: forma=1, valor=0
"""

import sqlite3
from datetime import date

DB_PATH = "databaseSazonalizei.db"


def buscar_nota_compra_do_ingrediente(cur, id_produto):
    """Retorna o id da nota de compra mais recente do ingrediente."""
    cur.execute("""
        SELECT fn.id
        FROM fluxosNotasEstoque fn
        JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
        WHERE fn.id_tipoNota = 1 AND fe.id_produto = ?
        ORDER BY fn.id DESC
        LIMIT 1
    """, (id_produto,))
    row = cur.fetchone()
    return row["id"] if row else None


def migrar_notas_compostas(conn, cur):
    """
    Para cada nota de venda que contém produto composto + ingredientes misturados,
    separa os ingredientes em notas próprias e cria os pagamentos.
    """

    # Buscar todas as notas de venda que têm produto composto (receita=1)
    cur.execute("""
        SELECT DISTINCT fe.id_fluxo_nota
        FROM fluxoEstoque fe
        JOIN produto p ON fe.id_produto = p.id
        WHERE fe.id_tipoNota = 2 AND p.receita = 1
        ORDER BY fe.id_fluxo_nota
    """)
    notas_com_composto = [r["id_fluxo_nota"] for r in cur.fetchall()]

    print(f"Notas com produto composto: {len(notas_com_composto)}")

    id_forma_pagamento = 1  # Pagamento padrao (dinheiro/a vista)
    data_hoje = str(date.today())

    total_notas_criadas = 0
    total_pagamentos_criados = 0

    for id_nota in notas_com_composto:
        # Busca a nota de venda (cabeçalho)
        cur.execute("SELECT * FROM fluxosNotasEstoque WHERE id = ?", (id_nota,))
        nota = cur.fetchone()
        id_cliente = nota["id_representante"]
        data_nota  = nota["data_vencimento"] or data_hoje

        # Busca TODOS os itens desta nota
        cur.execute("""
            SELECT fe.id, fe.id_produto, fe.quantidade, fe.valorUnidario, fe.lucroTotal, p.receita, p.nome
            FROM fluxoEstoque fe
            JOIN produto p ON fe.id_produto = p.id
            WHERE fe.id_fluxo_nota = ? AND fe.id_tipoNota = 2
            ORDER BY p.receita DESC  -- produto composto primeiro
        """, (id_nota,))
        itens = cur.fetchall()

        # Separa o produto composto dos ingredientes
        produto_composto = None
        ingredientes = []
        for item in itens:
            if item["receita"] == 1:
                produto_composto = item
            else:
                ingredientes.append(item)

        if not produto_composto:
            continue

        if not ingredientes:
            # Já está correto (nota só com o produto, sem ingredientes misturados)
            # Apenas garante que tem pagamento
            _garantir_pagamento(cur, conn, id_nota, produto_composto["quantidade"],
                                produto_composto["valorUnidario"], id_forma_pagamento, data_nota)
            total_pagamentos_criados += 1
            continue

        print(f"\n  [Nota {id_nota}] {produto_composto['nome']} (qtd={produto_composto['quantidade']})")

        # Remove ingredientes da nota original (ficarão em notas próprias)
        ids_fe_ingredientes = [item["id"] for item in ingredientes]
        cur.executemany("DELETE FROM fluxoEstoque WHERE id = ?",
                        [(i,) for i in ids_fe_ingredientes])

        notas_ingredientes = []

        for ingr in ingredientes:
            # Busca nota de compra do ingrediente (para id_notaOrigem)
            id_nota_compra_ingr = buscar_nota_compra_do_ingrediente(cur, ingr["id_produto"])

            # Verifica se já existe nota de venda separada para este ingrediente
            # (para evitar duplicatas em reexecuções)
            cur.execute("""
                SELECT fn.id FROM fluxosNotasEstoque fn
                JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
                WHERE fn.id_tipoNota = 2 AND fn.id_representante = ?
                  AND fe.id_produto = ? AND fn.id_notaOrigem = ?
                  AND fn.id != ?
            """, (id_cliente, ingr["id_produto"], id_nota_compra_ingr, id_nota))
            existente = cur.fetchone()

            if existente:
                id_nota_ingr = existente["id"]
                print(f"    [JA EXISTE] Nota {id_nota_ingr} para ingrediente {ingr['nome']}")
            else:
                # Cria nota de venda dedicada para este ingrediente
                cur.execute("""
                    INSERT INTO fluxosNotasEstoque
                    (id_tipoNota, id_representante, id_notaOrigem, data_vencimento)
                    VALUES (2, ?, ?, ?)
                """, (id_cliente, id_nota_compra_ingr, data_nota))
                conn.commit()
                id_nota_ingr = cur.lastrowid
                total_notas_criadas += 1

                # Insere o ingrediente nesta nova nota
                cur.execute("""
                    INSERT INTO fluxoEstoque
                    (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data)
                    VALUES (2, ?, ?, ?, ?, 0, ?)
                """, (id_nota_ingr, ingr["id_produto"], ingr["quantidade"], ingr["valorUnidario"], data_nota))
                conn.commit()

                print(f"    [NOVA NOTA {id_nota_ingr}] {ingr['nome']} qtd={ingr['quantidade']} custo={ingr['valorUnidario']} (compra_origem={id_nota_compra_ingr})")

            notas_ingredientes.append(id_nota_ingr)

        # Cria pagamentos para a nota do produto + todas as notas de ingredientes
        total_venda = round(produto_composto["quantidade"] * produto_composto["valorUnidario"], 2)

        # Pagamento da nota principal (produto composto) — valor real
        _garantir_pagamento(cur, conn, id_nota, produto_composto["quantidade"],
                            produto_composto["valorUnidario"], id_forma_pagamento, data_nota)
        total_pagamentos_criados += 1

        # Pagamentos das notas de ingredientes — valor 0 (rastreabilidade)
        for id_nota_ingr in notas_ingredientes:
            _garantir_pagamento(cur, conn, id_nota_ingr, 0, 0, id_forma_pagamento, data_nota)
            total_pagamentos_criados += 1

    conn.commit()
    return total_notas_criadas, total_pagamentos_criados


def _garantir_pagamento(cur, conn, id_nota, quantidade, valor_unit, id_forma, data):
    """Insere pagamento só se ainda não existe para esta nota."""
    cur.execute("SELECT id FROM fluxoPagamentoNotas WHERE id_fluxo_nota = ?", (id_nota,))
    if cur.fetchone():
        return  # já existe
    valor = round(quantidade * valor_unit, 2)
    cur.execute("""
        INSERT INTO fluxoPagamentoNotas (id_fluxo_nota, id_forma_pagamento, valor, data_pagamento)
        VALUES (?, ?, ?, ?)
    """, (id_nota, id_forma, valor, data))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    print("=" * 60)
    print("MIGRACAO: SEPARAR INGREDIENTES EM NOTAS PROPRIAS")
    print("=" * 60)

    n_notas, n_pagamentos = migrar_notas_compostas(conn, cur)

    # Relatório final
    cur.execute("SELECT COUNT(*) as c FROM fluxosNotasEstoque"); total_notas = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM fluxoEstoque");       total_itens = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM fluxoPagamentoNotas");total_pag   = cur.fetchone()["c"]

    print(f"\n{'=' * 60}")
    print(f"  Notas criadas para ingredientes: {n_notas}")
    print(f"  Pagamentos criados:              {n_pagamentos}")
    print(f"  Total notas no banco:            {total_notas}")
    print(f"  Total itens no banco:            {total_itens}")
    print(f"  Total pagamentos no banco:       {total_pag}")
    print(f"{'=' * 60}")

    # Verifica amostra de como ficou uma venda de composto
    print("\n--- Amostra: Sanduiche Artesanal X-Tudo (nota 17) ---")
    cur.execute("""
        SELECT fn.id, fn.id_tipoNota, fn.id_representante, fn.id_notaOrigem,
               fe.id_produto, p.nome, fe.quantidade, fe.valorUnidario, fe.lucroTotal
        FROM fluxosNotasEstoque fn
        JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
        JOIN produto p ON fe.id_produto = p.id
        WHERE fn.id = 17
    """)
    for r in cur.fetchall():
        print("  NOTA:", dict(r))

    cur.execute("""
        SELECT fn.id, fn.id_tipoNota, fn.id_representante, fn.id_notaOrigem,
               fe.id_produto, p.nome, fe.quantidade, fe.valorUnidario, fe.lucroTotal
        FROM fluxosNotasEstoque fn
        JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
        JOIN produto p ON fe.id_produto = p.id
        WHERE fn.id_representante = (SELECT id_representante FROM fluxosNotasEstoque WHERE id=17)
          AND fn.id_tipoNota = 2 AND fn.id > 17
          AND fe.id_produto IN (15, 16, 17)
        ORDER BY fn.id
    """)
    for r in cur.fetchall():
        print("  INGR:", dict(r))

    print("\n--- Pagamentos da venda do sanduiche ---")
    cur.execute("""
        SELECT * FROM fluxoPagamentoNotas
        WHERE id_fluxo_nota = 17
           OR id_fluxo_nota IN (
               SELECT fn.id FROM fluxosNotasEstoque fn
               JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
               WHERE fn.id_representante = (SELECT id_representante FROM fluxosNotasEstoque WHERE id=17)
                 AND fn.id_tipoNota = 2 AND fn.id > 17
                 AND fe.id_produto IN (15,16,17)
           )
    """)
    for r in cur.fetchall():
        print("  PAG:", dict(r))

    conn.close()
    print("\nMIGRACÃO CONCLUIDA!")


if __name__ == "__main__":
    main()
