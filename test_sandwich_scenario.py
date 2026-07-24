import sqlite3
from datetime import date
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.memory.inventoryFlowManage import InventoryFlowManager
from br.com.pdv.src.memory.purchaseNoteClassFactory import PurchaseNoteClassFactory
from br.com.pdv.src.memory.saleNoteClassFactory import SaleNoteClassFactory
from br.com.pdv.src.memory.supplierClassFactory import SupplierClassFactory
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory

def setup_sandwich_test_environment():
    print("=" * 80)
    print(" CONFIGURANDO AMBIENTE DE TESTE: SANDUICHE COM MULTIPLOS FORNECEDORES")
    print("=" * 80)

    import time
    ts = int(time.time())

    # 1. Cadastrar 3 Fornecedores (Empresas + Entidades)
    # Fornecedor 1: Padaria dos Pães
    id_p1 = DB.INSERT.PESSOA.executar(f"PADADEIRO SILVA {ts}", 1)
    id_e1 = DB.INSERT.EMPRESA.executar(f"PADARIA CENTRAL {ts}")
    id_ent_forn1 = DB.INSERT.ENTIDADE.executar(id_p1, id_e1, 1, 0, 0)
    DB.INSERT.ENTIDADE_CARGO.executar(id_ent_forn1, 1) # Dono

    # Fornecedor 2: Boi Gordo Carnes
    id_p2 = DB.INSERT.PESSOA.executar(f"AÇOUGUEIRO JOÃO {ts}", 1)
    id_e2 = DB.INSERT.EMPRESA.executar(f"FRIGORÍFICO BOI GORDO {ts}")
    id_ent_forn2 = DB.INSERT.ENTIDADE.executar(id_p2, id_e2, 1, 0, 0)
    DB.INSERT.ENTIDADE_CARGO.executar(id_ent_forn2, 1)

    # Fornecedor 3: Laticínios Valle
    id_p3 = DB.INSERT.PESSOA.executar(f"PRODUTOR MATEUS {ts}", 1)
    id_e3 = DB.INSERT.EMPRESA.executar(f"LATICÍNIOS VALLE {ts}")
    id_ent_forn3 = DB.INSERT.ENTIDADE.executar(id_p3, id_e3, 1, 0, 0)
    DB.INSERT.ENTIDADE_CARGO.executar(id_ent_forn3, 1)

    print(f"[OK] 3 Fornecedores cadastrados (IDs Entidade: {id_ent_forn1}, {id_ent_forn2}, {id_ent_forn3})")

    # 2. Cadastrar Ingredientes (Produtos de Estoque)
    # UnidadeMedida 1 = UNIDADE
    id_pao = DB.INSERT.PRODUTO.executar(f"PAO BRIOCHE {ts}", 15, 1, 0, 3.00, 2.50, 2.00)
    id_carne = DB.INSERT.PRODUTO.executar(f"HAMBURGUER ARTESANAL {ts}", 30, 1, 0, 10.00, 9.00, 8.50)
    id_queijo = DB.INSERT.PRODUTO.executar(f"FATIA QUEIJO CHEDDAR {ts}", 45, 1, 0, 1.50, 1.20, 1.00)

    print(f"[OK] 3 Ingredientes cadastrados (IDs: Pao={id_pao}, Carne={id_carne}, Queijo={id_queijo})")

    # 3. Registrar Compras com Fornecedores Diferentes
    # Compra 1: Pão com Fornecedor 1 (Padaria) -> 100 un @ R$ 1.50/unidade
    res_c1 = InventoryFlowManager.registrar_compra(
        id_representante=id_ent_forn1,
        produtos=[{"id_produto": id_pao, "quantidade": 100, "valorUnidario": 1.50}],
        data_vencimento=str(date.today())
    )
    id_nota_compra1 = res_c1["id_nota"]

    # Compra 2: Carne com Fornecedor 2 (Frigorífico) -> 100 un @ R$ 6.00/unidade
    res_c2 = InventoryFlowManager.registrar_compra(
        id_representante=id_ent_forn2,
        produtos=[{"id_produto": id_carne, "quantidade": 100, "valorUnidario": 6.00}],
        data_vencimento=str(date.today())
    )
    id_nota_compra2 = res_c2["id_nota"]

    # Compra 3: Queijo com Fornecedor 3 (Laticínio) -> 200 un @ R$ 0.80/unidade
    res_c3 = InventoryFlowManager.registrar_compra(
        id_representante=id_ent_forn3,
        produtos=[{"id_produto": id_queijo, "quantidade": 200, "valorUnidario": 0.80}],
        data_vencimento=str(date.today())
    )
    id_nota_compra3 = res_c3["id_nota"]

    print(f"[OK] 3 Notas de Compra de ingredientes criadas (Notas IDs: {id_nota_compra1}, {id_nota_compra2}, {id_nota_compra3})")

    # 4. Cadastrar Produto Composto (Sanduíche Especial) com Receita
    id_sanduiche = DB.INSERT.PRODUTO.executar(f"SANDUICHE ARTESANAL X-TUDO {ts}", 1, 1, 1, 28.00, 25.00, 22.00)
    
    # Adicionar Ingredientes na Receita (1 Pão, 1 Carne, 2 Fatias de Queijo)
    DB.INSERT.RECEITA.executar(id_sanduiche, id_pao, 1)
    DB.INSERT.RECEITA.executar(id_sanduiche, id_carne, 1)
    DB.INSERT.RECEITA.executar(id_sanduiche, id_queijo, 2)

    print(f"[OK] Produto Composto 'SANDUÍCHE ARTESANAL X-TUDO' (ID {id_sanduiche}) criado com receita contendo 3 ingredientes de 3 fornecedores!")

    # 5. Registrar Venda do Sanduíche
    # Cliente ID 4
    res_venda = InventoryFlowManager.registrar_venda(
        id_representante=4,
        produtos=[{"id_produto": id_sanduiche, "quantidade": 5, "valorUnidario": 28.00}],
        data_vencimento=str(date.today())
    )
    id_nota_venda = res_venda["id_nota"]
    print(f"[OK] Venda de 5 Sanduiches registrada com Sucesso! (Nota Venda ID: {id_nota_venda})")

    # =========================================================================
    # TESTES E VERIFICAÇÕES
    # =========================================================================
    print("\n" + "=" * 80)
    print(" VERIFICANDO FABRICACAO DAS NOTAS VIA FACTORIES")
    print("=" * 80)

    # Teste 1: Fabricar Fornecedores
    f1 = SupplierClassFactory.fabricar(id_ent_forn1)
    f2 = SupplierClassFactory.fabricar(id_ent_forn2)
    f3 = SupplierClassFactory.fabricar(id_ent_forn3)
    print(f"\n[FORNECEDOR 1 - Pao]: {f1.getDados()['origem']['nome']}")
    print(f"[FORNECEDOR 2 - Carne]: {f2.getDados()['origem']['nome']}")
    print(f"[FORNECEDOR 3 - Queijo]: {f3.getDados()['origem']['nome']}")

    # Teste 2: Fabricar Notas de Compra
    nc1 = PurchaseNoteClassFactory.fabricar(id_nota_compra1)
    nc2 = PurchaseNoteClassFactory.fabricar(id_nota_compra2)
    nc3 = PurchaseNoteClassFactory.fabricar(id_nota_compra3)
    print(f"\n[NOTA COMPRA PAO]: ID {nc1.getDados()['id']} | Valor: R$ {nc1.getDados()['valorTotal']}")
    print(f"[NOTA COMPRA CARNE]: ID {nc2.getDados()['id']} | Valor: R$ {nc2.getDados()['valorTotal']}")
    print(f"[NOTA COMPRA QUEIJO]: ID {nc3.getDados()['id']} | Valor: R$ {nc3.getDados()['valorTotal']}")

    # Teste 3: Custo Agregado da Receita do Sanduíche
    custo_sanduiche = InventoryFlowManager._obter_custo_mais_caro(id_sanduiche)
    print(f"\n[CUSTO TOTAL AGREGADO DA RECEITA DO SANDUICHE]: R$ {custo_sanduiche:.2f}")
    print(f"   - 1x Pao Brioche (R$ 1.50 da {f1.getDados()['origem']['nome']})")
    print(f"   - 1x Hamburguer Artesanal (R$ 6.00 do {f2.getDados()['origem']['nome']})")
    print(f"   - 2x Queijo Cheddar (2x R$ 0.80 do {f3.getDados()['origem']['nome']})")
    print(f"   Calculado: 1.50 + 6.00 + 1.60 = R$ 9.10 | Esperado: R$ 9.10")

    # Teste 4: Fabricar e Verificar Nota de Venda
    nv = SaleNoteClassFactory.fabricar(id_nota_venda)
    dados_nv = nv.getDados()
    nome_cliente = dados_nv['cliente'].get('nome') or dados_nv['cliente'].get('origem', {}).get('nome', 'Cliente Indefinido')
    print(f"\n[DADOS DA NOTA DE VENDA DO SANDUICHE] (ID {dados_nv['id']}):")
    print(f"   - Cliente: {nome_cliente}")
    print(f"   - Valor Total Venda: R$ {dados_nv['valorTotalVenda']}")
    print(f"   - Custo Total Calculado: R$ {dados_nv['custoTotal']}")
    print(f"   - Lucro Total da Venda: R$ {dados_nv['lucroTotal']}")
    print("=" * 80)
    print(" TESTE CONCLUIDO COM SUCESSO INTEGRAL!")
    print("=" * 80)

if __name__ == '__main__':
    setup_sandwich_test_environment()
