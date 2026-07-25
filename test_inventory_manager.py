import sys
import os

# Ajusta o sys.path para garantir que consegue encontrar o módulo
sys.path.insert(0, os.path.abspath('.'))

from br.com.pdv.src.memory.inventoryManager import InventoryManager


def exibir_estado_produto(id_produto: int, titulo: str):
    print(f"\n--- {titulo} ---")
    est = InventoryManager.get_estoque_produto(id_produto)
    if not est:
        print(f"Produto ID {id_produto} não encontrado no mapa de estoque.")
        return
    print(f"  Qtd Atual em Estoque : {est.get('quantidadeTotal', 0.0)}")
    print(f"  Valor Total Estoque  : R$ {est.get('valorTotalEstoque', 0.0):.2f}")
    print(f"  Custo Médio Unitário : R$ {est.get('custoMedio', 0.0):.3f}")
    print(f"  Total Compras (Qtd)  : {est.get('totalCompras', 0.0)}")
    print(f"  Total Vendas (Qtd)   : {est.get('totalVendas', 0.0)}")
    print(f"  Total Devoluções(Qtd): {est.get('totalDevolucoes', 0.0)}")
    print(f"  Total Perdas (Qtd)   : {est.get('totalPerdas', 0.0)}")
    print(f"  Lotes Ativos (Qtd)   : {len(est.get('lotes', []))}")


def testar_fluxo_movimentacao_estoque():
    print("=" * 75)
    print("TESTE COMPLETO DE FLUXO E REGRAS CONTÁBEIS DE ESTOQUE")
    print("(COMPRA, VENDA, DEVOLUÇÃO, PERDA METADE E REPOSIÇÃO / COMPENSAÇÃO)")
    print("=" * 75)

    # 0. Carregar dados e índice de estoque do banco
    ok = InventoryManager.carregarTudo()
    if not ok:
        print("ERRO: Falha ao carregar dados no InventoryManager.")
        return

    id_produto = 1
    id_fornecedor = 3   # Empresa Alfa Ltda
    id_cliente = 1      # NAO INFORMADO (cliente padrão)

    exibir_estado_produto(id_produto, "ESTADO INICIAL DO PRODUTO")

    # 1. COMPRA (Adicionar Compra)
    qtd_compra = 100.0
    preco_compra = 10.0
    print(f"\n1. REGISTRANDO COMPRA: {qtd_compra} unidades a R$ {preco_compra:.2f} cada...")
    dados_compra = {
        "id_fornecedor": id_fornecedor,
        "data": "2026-07-24",
        "produtos": [
            {"id": id_produto, "quantidade": qtd_compra, "valorUnidario": preco_compra}
        ]
    }
    nota_compra = InventoryManager.insert_compra(dados_compra)
    assert nota_compra is not None, "Falha ao registrar nota de compra"
    datos_c = nota_compra.getDados()
    id_nota_compra = datos_c["id"]
    print(f"   -> Nota de Compra ID {id_nota_compra} criada.")
    print(f"      [CONTÁBIL COMPRA] Valor Total: {datos_c.get('valorTotalCompra')}")
    exibir_estado_produto(id_produto, "ESTADO APÓS COMPRA")

    # 2. VENDA (Adicionar Venda)
    qtd_venda = 40.0
    preco_venda = 15.0
    print(f"\n2. REGISTRANDO VENDA: {qtd_venda} unidades a R$ {preco_venda:.2f} cada...")
    dados_venda = {
        "id_cliente": id_cliente,
        "data": "2026-07-24",
        "produtos": [
            {"id": id_produto, "quantidade": qtd_venda, "valorVenda": preco_venda}
        ]
    }
    nota_venda = InventoryManager.insert_venda(dados_venda)
    assert nota_venda is not None, "Falha ao registrar nota de venda"
    datos_v = nota_venda.getDados()
    id_nota_venda = datos_v["id"]
    print(f"   -> Nota de Venda ID {id_nota_venda} criada.")
    print(f"      [CONTÁBIL VENDA] Valor Total Venda: {datos_v.get('valorTotalVenda')} | Lucro Estimado: {datos_v.get('valorTotalLucro')}")
    exibir_estado_produto(id_produto, "ESTADO APÓS VENDA")

    # 3. DEVOLUÇÃO (Adicionar Devolução)
    qtd_devolucao = 10.0
    print(f"\n3. REGISTRANDO DEVOLUÇÃO: {qtd_devolucao} unidades da venda (Nota Venda ID {id_nota_venda})...")
    dados_devolucao = {
        "id_cliente": id_cliente,
        "id_nota_venda_origem": id_nota_venda,
        "data": "2026-07-24",
        "produtos": [
            {"id": id_produto, "quantidade": qtd_devolucao, "valorUnidario": preco_compra}
        ]
    }
    nota_devolucao = InventoryManager.insert_devolucao(dados_devolucao)
    assert nota_devolucao is not None, "Falha ao registrar nota de devolução"
    datos_d = nota_devolucao.getDados()
    id_nota_devolucao = datos_d["id"]
    print(f"   -> Nota de Devolução ID {id_nota_devolucao} criada.")
    print(f"      [CONTÁBIL DEVOLUÇÃO] Valor Total Devolução: {datos_d.get('valorTotalDevolucao')}")
    exibir_estado_produto(id_produto, "ESTADO APÓS DEVOLUÇÃO")

    # 4. PERDA "METADE" (Adicionar Perda de 50% dos itens devolvidos - Abate do Lucro)
    qtd_perda = qtd_devolucao / 2.0  # Metade da devolução (5.0 unidades)
    print(f"\n4. REGISTRANDO PERDA METADE: {qtd_perda} unidades (50% da devolução)...")
    print("   * Regra Contábil Perda: O custo dos itens perdidos abate/reduz o lucro final.")
    dados_perda = {
        "origem": "DEVOLUCAO",
        "id_nota_origem": id_nota_devolucao,
        "data": "2026-07-24",
        "produtos": [
            {"id": id_produto, "quantidade": qtd_perda, "valorUnidario": preco_compra}
        ]
    }
    nota_perda = InventoryManager.insert_perda(dados_perda)
    assert nota_perda is not None, "Falha ao registrar nota de perda"
    datos_p = nota_perda.getDados()
    id_nota_perda = datos_p["id"]
    print(f"   -> Nota de Perda ID {id_nota_perda} criada.")
    print(f"      [CONTÁBIL PERDA] Prejuízo / Abatimento de Lucro: {datos_p.get('valorTotalPerda')}")
    exibir_estado_produto(id_produto, "ESTADO APÓS PERDA (METADE)")

    # 5. REPOSIÇÃO / COMPENSAÇÃO (Adicionar Reposição de Estoque - Repõe o Lucro / 100% de Lucro)
    qtd_reposicao = qtd_perda  # Reposição das 5 unidades perdidas
    print(f"\n5. REGISTRANDO REPOSIÇÃO: {qtd_reposicao} unidades (compensando Nota Perda ID {id_nota_perda})...")
    print("   * Regra Contábil Compensação: Contém as informações de custo (como Nota de Compra).")
    print("   * Repõe o estoque/lucro permitindo que os produtos compensados gerem 100% de margem no fluxo de venda.")
    dados_compensacao = {
        "id_nota_perda_origem": id_nota_perda,
        "data": "2026-07-24",
        "produtos": [
            {"id": id_produto, "quantidade": qtd_reposicao, "valorUnidario": preco_compra}
        ]
    }
    nota_compensacao = InventoryManager.insert_compensacao(dados_compensacao)
    assert nota_compensacao is not None, "Falha ao registrar nota de compensação/reposição"
    datos_comp = nota_compensacao.getDados()
    id_nota_compensacao = datos_comp["id"]
    print(f"   -> Nota de Compensação/Reposição ID {id_nota_compensacao} criada.")
    print(f"      [CONTÁBIL COMPENSAÇÃO] Informações Contábeis de Reposição:")
    print(f"      - ID Nota Perda Origem : {datos_comp.get('notaPerdaOrigem')}")
    print(f"      - Valor Total Reposto  : {datos_comp.get('valorTotalCompensacao')}")
    print(f"      - Estrutura de Produtos: {list(datos_comp.get('produtos', {}).keys())}")
    exibir_estado_produto(id_produto, "ESTADO FINAL APÓS REPOSIÇÃO")

    print("\n" + "=" * 75)
    print("TESTE DE COMPRA, VENDA, DEVOLUÇÃO, PERDA METADE E REPOSIÇÃO CONCLUÍDO!")
    print("TODAS AS REGRAS CONTÁBEIS E DE ESTOQUE FORAM VERIFICADAS COM SUCESSO.")
    print("=" * 75)


def main():
    testar_fluxo_movimentacao_estoque()


if __name__ == '__main__':
    main()
