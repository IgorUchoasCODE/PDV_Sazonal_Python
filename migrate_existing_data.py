"""
migrate_existing_data.py
========================
Corrige os dados EXISTENTES no banco (notas ids 1-49, produtos ids 1-30)
para seguir a regra:

  REGRA COMPOSTO:
  - Produto composto na nota de VENDA => valorUnidario = 0, lucroTotal = lucro real
  - Ingredientes do composto na mesma nota => valorUnidario = custo, lucroTotal = 0
  - id_notaOrigem da nota de venda = NULL se multiplos ingredientes, ou ID da compra se 1 ingrediente

  REGRA SIMPLES:
  - Nota de venda deve ter id_notaOrigem apontando para a nota de compra do produto
  - valorUnidario = preco de venda
  - lucroTotal = (preco_venda - custo) * qtd
"""

import sqlite3

DB_PATH = "databaseSazonalizei.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 60)
    print("MIGRACAO DOS DADOS EXISTENTES")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────
    # 1. CARTELA DE OVO TIPO A (id=3) e CARTELA BRANCO TIPO B (id=4)
    #    Sao compostos simples com 1 ingrediente.
    #    Receita: prod 3 => ingr 1 (30 unidades), prod 4 => ingr 2 (30 unidades)
    #    Notas de venda: 3,4,5 (prod 3) e 8,9,10 (prod 4)
    #    Custo do ingrediente: buscar a max compra de ingr 1 e 2
    # ──────────────────────────────────────────────────────────

    print("\n[1] Corrigindo Cartelas (produtos compostos simples, 1 ingrediente)...")

    # Custo mais caro das caixas de ovo (ingredientes)
    cur.execute("SELECT MAX(valorUnidario) as c FROM fluxoEstoque WHERE id_produto = 1 AND id_tipoNota = 1")
    custo_ingr1 = cur.fetchone()["c"] or 120.0  # caixa ovo branco tipo A

    cur.execute("SELECT MAX(valorUnidario) as c FROM fluxoEstoque WHERE id_produto = 2 AND id_tipoNota = 1")
    custo_ingr2 = cur.fetchone()["c"] or 108.0  # caixa ovo branco tipo B

    print(f"  Custo ingrediente 1 (caixa ovo A): R$ {custo_ingr1}")
    print(f"  Custo ingrediente 2 (caixa ovo B): R$ {custo_ingr2}")

    # Notas de venda das cartelas: 3,4,5 (prod 3) e 8,9,10 (prod 4)
    # Compra do prod 3 e 4 vieram via notas 1 e 2
    # id_notaOrigem = 1 para prod 3, = 2 para prod 4 (1 ingrediente => aponta compra do ingrediente)

    for id_nota_venda, id_produto, id_ingrediente, custo_ing, id_nota_compra_orig in [
        (3,  3, 1, custo_ingr1, 1),
        (4,  3, 1, custo_ingr1, 1),
        (5,  3, 1, custo_ingr1, 1),
        (8,  4, 2, custo_ingr2, 2),
        (9,  4, 2, custo_ingr2, 2),
        (10, 4, 2, custo_ingr2, 2),
    ]:
        # Buscar linha do produto composto nesta nota de venda
        cur.execute("""
            SELECT fe.id, fe.quantidade, fe.valorUnidario, fe.lucroTotal
            FROM fluxoEstoque fe
            WHERE fe.id_fluxo_nota = ? AND fe.id_produto = ? AND fe.id_tipoNota = 2
        """, (id_nota_venda, id_produto))
        row = cur.fetchone()

        if not row:
            print(f"  [AVISO] Nota {id_nota_venda} produto {id_produto} nao encontrada em fluxoEstoque")
            continue

        qtd_vendida = row["quantidade"]
        lucro_atual = row["lucroTotal"]

        # 1a. Produto composto: zera valorUnidario (nao tem custo, so lucro)
        cur.execute("""
            UPDATE fluxoEstoque
            SET valorUnidario = 0
            WHERE id = ?
        """, (row["id"],))
        print(f"  [OK] Nota {id_nota_venda}: produto {id_produto} => valorUnidario=0 (lucro mantido: {lucro_atual})")

        # 1b. Verifica se ingrediente ja esta registrado nesta nota
        cur.execute("""
            SELECT id FROM fluxoEstoque
            WHERE id_fluxo_nota = ? AND id_produto = ? AND id_tipoNota = 2
        """, (id_nota_venda, id_ingrediente))
        if cur.fetchone():
            print(f"    [JA EXISTE] Ingrediente {id_ingrediente} ja esta na nota {id_nota_venda}")
        else:
            # Busca a data da nota
            cur.execute("SELECT data_vencimento FROM fluxosNotasEstoque WHERE id = ?", (id_nota_venda,))
            data_nota = cur.fetchone()["data_vencimento"]

            # Insere ingrediente ao custo, lucro 0
            # Receita: qntdd = 30 (30 ovos por cartela)
            qntdd_receita = 30
            cur.execute("""
                INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data)
                VALUES (2, ?, ?, ?, ?, 0, ?)
            """, (id_nota_venda, id_ingrediente, qtd_vendida * qntdd_receita, custo_ing, data_nota))
            print(f"    [INSERIDO] Ingrediente {id_ingrediente} qtd={qtd_vendida * qntdd_receita} custo={custo_ing}")

        # 1c. Atualiza id_notaOrigem para apontar para a compra do ingrediente
        cur.execute("UPDATE fluxosNotasEstoque SET id_notaOrigem = ? WHERE id = ?", (id_nota_compra_orig, id_nota_venda))

    conn.commit()

    # ──────────────────────────────────────────────────────────
    # 2. SANDUICHES (ids 18, 22, 26, 30) — compostos com 3 ingredientes
    #    Notas de venda: 17, 21, 25, 29
    #    Ingredientes: pao(15/19/23/27), hamburguer(16/20/24/28), queijo(17/21/25/29)
    #    id_notaOrigem = NULL (multiplos fornecedores)
    # ──────────────────────────────────────────────────────────

    print("\n[2] Corrigindo Sanduiches (compostos multi-ingrediente)...")

    sandubas = [
        {
            "id_produto": 18,
            "id_nota_venda": 17,
            "ingredientes": [
                {"id_produto": 15, "qntdd": 1, "id_nota_compra": 14},  # pao
                {"id_produto": 16, "qntdd": 1, "id_nota_compra": 15},  # hamburguer
                {"id_produto": 17, "qntdd": 2, "id_nota_compra": 16},  # queijo
            ]
        },
        {
            "id_produto": 22,
            "id_nota_venda": 21,
            "ingredientes": [
                {"id_produto": 19, "qntdd": 1, "id_nota_compra": 18},
                {"id_produto": 20, "qntdd": 1, "id_nota_compra": 19},
                {"id_produto": 21, "qntdd": 2, "id_nota_compra": 20},
            ]
        },
        {
            "id_produto": 26,
            "id_nota_venda": 25,
            "ingredientes": [
                {"id_produto": 23, "qntdd": 1, "id_nota_compra": 22},
                {"id_produto": 24, "qntdd": 1, "id_nota_compra": 23},
                {"id_produto": 25, "qntdd": 2, "id_nota_compra": 24},
            ]
        },
        {
            "id_produto": 30,
            "id_nota_venda": 29,
            "ingredientes": [
                {"id_produto": 27, "qntdd": 1, "id_nota_compra": 26},
                {"id_produto": 28, "qntdd": 1, "id_nota_compra": 27},
                {"id_produto": 29, "qntdd": 2, "id_nota_compra": 28},
            ]
        },
    ]

    for s in sandubas:
        id_nota = s["id_nota_venda"]
        id_prod = s["id_produto"]

        # Busca linha do composto na nota de venda
        cur.execute("""
            SELECT fe.id, fe.quantidade, fe.valorUnidario, fe.lucroTotal, fn.data_vencimento
            FROM fluxoEstoque fe
            JOIN fluxosNotasEstoque fn ON fe.id_fluxo_nota = fn.id
            WHERE fe.id_fluxo_nota = ? AND fe.id_produto = ? AND fe.id_tipoNota = 2
        """, (id_nota, id_prod))
        row = cur.fetchone()

        if not row:
            print(f"  [AVISO] Nota {id_nota} produto {id_prod} nao encontrada")
            continue

        qtd_vendida = row["quantidade"]
        lucro_atual = row["lucroTotal"]
        data_nota   = row["data_vencimento"]

        # Zera valorUnidario do produto composto (lucro permanece)
        cur.execute("UPDATE fluxoEstoque SET valorUnidario = 0 WHERE id = ?", (row["id"],))
        print(f"  [OK] Nota {id_nota}: produto {id_prod} => valorUnidario=0 (lucro={lucro_atual})")

        # Garante id_notaOrigem = NULL (multiplos fornecedores)
        cur.execute("UPDATE fluxosNotasEstoque SET id_notaOrigem = NULL WHERE id = ?", (id_nota,))

        # Insere ingredientes ao custo, lucro 0 (se ainda nao existirem)
        for ingr in s["ingredientes"]:
            cur.execute("""
                SELECT id FROM fluxoEstoque
                WHERE id_fluxo_nota = ? AND id_produto = ? AND id_tipoNota = 2
            """, (id_nota, ingr["id_produto"]))
            if cur.fetchone():
                print(f"    [JA EXISTE] Ingrediente {ingr['id_produto']} na nota {id_nota}")
                continue

            # Custo mais caro do ingrediente nas compras
            cur.execute("SELECT MAX(valorUnidario) as c FROM fluxoEstoque WHERE id_produto = ? AND id_tipoNota = 1", (ingr["id_produto"],))
            custo_ing = cur.fetchone()["c"] or 0.0

            cur.execute("""
                INSERT INTO fluxoEstoque (id_tipoNota, id_fluxo_nota, id_produto, quantidade, valorUnidario, lucroTotal, data)
                VALUES (2, ?, ?, ?, ?, 0, ?)
            """, (id_nota, ingr["id_produto"], qtd_vendida * ingr["qntdd"], custo_ing, data_nota))
            print(f"    [INSERIDO] Ingrediente {ingr['id_produto']} qtd={qtd_vendida * ingr['qntdd']} custo={custo_ing}")

    conn.commit()

    # ──────────────────────────────────────────────────────────
    # 3. NOTAS DE VENDA SIMPLES sem id_notaOrigem
    #    Nota 13: venda de produtos simples (5,6,10,11) - multiplos produtos
    #    => cada produto simples vem de uma compra diferente, mas por ser 1 nota de venda
    #       coletiva, id_notaOrigem fica NULL (regra: so 1 produto = aponta compra)
    #
    #    Corrigir as vendas com valorUnidario preenchido mas lucroTotal = 0
    #    (produtos simples tinham custo mas lucro nao foi calculado)
    # ──────────────────────────────────────────────────────────

    print("\n[3] Corrigindo lucroTotal das vendas simples antigas (nota 13)...")

    cur.execute("""
        SELECT fe.id, fe.id_produto, fe.quantidade, fe.valorUnidario, fe.lucroTotal, p.receita
        FROM fluxoEstoque fe
        JOIN produto p ON fe.id_produto = p.id
        WHERE fe.id_fluxo_nota = 13 AND fe.id_tipoNota = 2 AND p.receita = 0
    """)
    rows = cur.fetchall()

    for row in rows:
        if row["lucroTotal"] == 0 and row["valorUnidario"] > 0:
            # Busca custo de compra mais caro deste produto
            cur.execute("SELECT MAX(valorUnidario) as c FROM fluxoEstoque WHERE id_produto = ? AND id_tipoNota = 1", (row["id_produto"],))
            custo = cur.fetchone()["c"] or 0.0
            lucro = round((row["valorUnidario"] - custo) * row["quantidade"], 2)

            if lucro != 0:
                cur.execute("UPDATE fluxoEstoque SET lucroTotal = ? WHERE id = ?", (lucro, row["id"]))
                print(f"  [OK] produto {row['id_produto']} => lucroTotal={lucro} (venda={row['valorUnidario']}, custo={custo})")

    conn.commit()

    # ──────────────────────────────────────────────────────────
    # 4. PRODUTOS SIMPLES com vendas isoladas (notas 44-49)
    #    Verificar se ja tem id_notaOrigem e lucroTotal
    # ──────────────────────────────────────────────────────────

    print("\n[4] Corrigindo notas de venda simples isoladas (44-49)...")

    cur.execute("""
        SELECT fn.id as id_nota, fn.id_notaOrigem, fe.id as id_fe, fe.id_produto, fe.quantidade,
               fe.valorUnidario, fe.lucroTotal, p.receita
        FROM fluxosNotasEstoque fn
        JOIN fluxoEstoque fe ON fe.id_fluxo_nota = fn.id
        JOIN produto p ON fe.id_produto = p.id
        WHERE fn.id IN (44,45,46,47,48,49) AND fn.id_tipoNota = 2
    """)
    rows_notas = cur.fetchall()

    for row in rows_notas:
        updated = False
        # Busca nota de compra deste produto (mais recente antes desta nota)
        cur.execute("""
            SELECT fn2.id FROM fluxosNotasEstoque fn2
            JOIN fluxoEstoque fe2 ON fe2.id_fluxo_nota = fn2.id
            WHERE fn2.id_tipoNota = 1 AND fe2.id_produto = ? AND fn2.id < ?
            ORDER BY fn2.id DESC LIMIT 1
        """, (row["id_produto"], row["id_nota"]))
        compra = cur.fetchone()

        if compra and not row["id_notaOrigem"]:
            cur.execute("UPDATE fluxosNotasEstoque SET id_notaOrigem = ? WHERE id = ?", (compra["id"], row["id_nota"]))
            print(f"  [OK] Nota {row['id_nota']} => id_notaOrigem={compra['id']}")
            updated = True

        # Corrige lucroTotal se estiver zerado
        if row["lucroTotal"] == 0 and row["valorUnidario"] > 0 and row["receita"] == 0:
            cur.execute("SELECT MAX(valorUnidario) as c FROM fluxoEstoque WHERE id_produto = ? AND id_tipoNota = 1", (row["id_produto"],))
            custo = cur.fetchone()["c"] or 0.0
            lucro = round((row["valorUnidario"] - custo) * row["quantidade"], 2)
            if lucro != 0:
                cur.execute("UPDATE fluxoEstoque SET lucroTotal = ? WHERE id = ?", (lucro, row["id_fe"]))
                print(f"  [OK] fe {row['id_fe']} produto {row['id_produto']} => lucroTotal={lucro}")
                updated = True

        if not updated:
            print(f"  [OK] Nota {row['id_nota']} produto {row['id_produto']} ja estava correto")

    conn.commit()

    # ──────────────────────────────────────────────────────────
    # 5. Relatorio de verificacao final
    # ──────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("VERIFICACAO FINAL")
    print("=" * 60)

    print("\n--- Compostos com vendas (valorUnidario deve ser 0) ---")
    cur.execute("""
        SELECT fe.id_fluxo_nota, p.nome, p.receita, fe.valorUnidario, fe.lucroTotal
        FROM fluxoEstoque fe
        JOIN produto p ON fe.id_produto = p.id
        WHERE p.receita = 1 AND fe.id_tipoNota = 2 AND fe.id_fluxo_nota <= 49
    """)
    for r in cur.fetchall():
        status = "OK" if r["valorUnidario"] == 0 else "ERRO"
        print(f"  [{status}] nota={r['id_fluxo_nota']} {r['nome']}: valorUni={r['valorUnidario']} lucro={r['lucroTotal']}")

    print("\n--- Notas de venda com id_notaOrigem ---")
    cur.execute("""
        SELECT id, id_tipoNota, id_notaOrigem
        FROM fluxosNotasEstoque
        WHERE id_tipoNota = 2 AND id <= 49
        ORDER BY id
    """)
    for r in cur.fetchall():
        print(f"  nota={r['id']} id_notaOrigem={r['id_notaOrigem']}")

    conn.close()
    print("\nMIGRACÃO CONCLUIDA!")


if __name__ == "__main__":
    main()
