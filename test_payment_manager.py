"""
Suíte de Testes para a Classe PaymentManager
==============================================
Testa:
  1. Cadastro de Pessoa via dict (cadastrar_pessoa)
  2. Cadastro de Empresa via dict (cadastrar_empresa)
  3. Registro de Pagamentos (registrar_pagamento)
  4. Regra de Titularidade Financeira de Empresa (get_extrato_empresa)
  5. Extrato de Pessoa e Entidade (get_extrato_pessoa / get_extrato_entidade)
  6. Resumo Financeiro Global (get_resumo_financeiro_global)
  7. Relatórios formatados em Markdown (RelatorioFinanceiroHelper)
"""
import sys
sys.path.insert(0, '.')

from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.paymentManager import PaymentManager, ExtratoFinanceiro, RelatorioFinanceiroHelper
from br.com.pdv.src.memory.inventoryManager import InventoryManager

def testar_payment_manager():
    print("=" * 75)
    print("INICIANDO SUÍTE DE TESTES DO PAYMENT MANAGER")
    print("=" * 75)

    # 1. Teste de Cadastro de Pessoa via dict
    print("\n1. Testando 'cadastrar_pessoa' via dict...")
    res_p = PaymentManager.cadastrar_pessoa({
        "nome": "CARLOS EDUARDO DE TESTE",
        "sexo": "MASCULINO",
        "is_cliente": True,
        "contatos": {"TELEFONE": "11988887777", "EMAIL": "carlos@teste.com"}
    })
    print(f"   Resultado: {res_p}")
    assert res_p["sucesso"] is True, f"Falha no cadastro de pessoa: {res_p}"
    id_pessoa = res_p["id_pessoa"]
    id_ent_pessoa = res_p["id_entidade"]

    # 2. Teste de Cadastro de Empresa via dict
    print("\n2. Testando 'cadastrar_empresa' via dict...")
    res_e = PaymentManager.cadastrar_empresa({
        "nome": "DISTRIBUIDORA ALFA LTDA DE TESTE",
        "is_fornecedor": True,
        "contatos": {"CNPJ": "12.345.678/0001-99", "TELEFONE": "1133334444"},
        "representantes": [{"id_pessoa": id_pessoa, "cargo": "SOCIO"}]
    })
    print(f"   Resultado: {res_e}")
    assert res_e["sucesso"] is True, f"Falha no cadastro de empresa: {res_e}"
    id_empresa = res_e["id_empresa"]
    id_ent_empresa = res_e["id_entidade"]

    # 3. Simula compra e venda no InventoryManager usando as entidades criadas
    print("\n3. Registrando Compra e Venda para gerar movimentações financeiras...")
    InventoryManager.carregarTudo()

    # Compra do Fornecedor (Empresa Alfa)
    compra = InventoryManager.insert_compra({
        "id_fornecedor": id_ent_empresa,
        "data": "2026-07-20",
        "produtos": [{"id": 1, "quantidade": 50.0, "valorUnidario": 10.0}]
    })
    id_nota_compra = compra.getDados()["id"]
    print(f"   Nota de Compra ID: {id_nota_compra} (Total R$ 500,00)")

    # Venda para o Cliente (Pessoa Carlos)
    venda = InventoryManager.insert_venda({
        "id_cliente": id_ent_pessoa,
        "data": "2026-07-22",
        "produtos": [{"id": 1, "quantidade": 20.0, "valorVenda": 15.0}]
    })
    id_nota_venda = venda.getDados()["id"]
    print(f"   Nota de Venda ID: {id_nota_venda} (Total R$ 300,00)")

    # 4. Teste de Registro de Pagamento via dict
    print("\n4. Testando 'registrar_pagamento' via dict...")
    pag_venda = PaymentManager.registrar_pagamento({
        "id_fluxo_nota": id_nota_venda,
        "id_forma_pagamento": 4,  # Pix
        "valor": 200.0,
        "data": "2026-07-23"
    })
    print(f"   Pagamento Venda: {pag_venda}")
    assert pag_venda["sucesso"] is True, f"Falha ao registrar pagamento da venda: {pag_venda}"

    pag_compra = PaymentManager.registrar_pagamento({
        "id_fluxo_nota": id_nota_compra,
        "id_forma_pagamento": 1,  # Dinheiro
        "valor": 300.0,
        "data": "2026-07-21"
    })
    print(f"   Pagamento Compra: {pag_compra}")
    assert pag_compra["sucesso"] is True, f"Falha ao registrar pagamento da compra: {pag_compra}"

    # 5. Teste da Regra de Titularidade Financeira da Empresa
    print("\n5. Testando Regra de Titularidade da Empresa (get_extrato_empresa)...")
    extrato_emp = PaymentManager.get_extrato_empresa(id_empresa)
    print(f"   Titular: {extrato_emp['nome_dono']} ({extrato_emp['tipo_dono']})")
    print(f"   Resumo Financeiro: {extrato_emp['resumo']}")

    assert extrato_emp["resumo"]["total_compras"] == 500.0, f"Esperado R$ 500 compras, obtido {extrato_emp['resumo']['total_compras']}"
    assert extrato_emp["resumo"]["pagamentos_efetuados"] == 300.0, f"Esperado R$ 300 pagos, obtido {extrato_emp['resumo']['pagamentos_efetuados']}"
    assert extrato_emp["resumo"]["contas_a_pagar"] == 200.0, f"Esperado R$ 200 pendente, obtido {extrato_emp['resumo']['contas_a_pagar']}"

    # 6. Teste de Extrato da Pessoa
    print("\n6. Testando Extrato da Pessoa (get_extrato_pessoa)...")
    extrato_pes = PaymentManager.get_extrato_pessoa(id_pessoa)
    print(f"   Titular: {extrato_pes['nome_dono']} ({extrato_pes['tipo_dono']})")
    print(f"   Resumo Financeiro: {extrato_pes['resumo']}")

    assert extrato_pes["resumo"]["total_vendas"] == 300.0, f"Esperado R$ 300 vendas, obtido {extrato_pes['resumo']['total_vendas']}"
    assert extrato_pes["resumo"]["pagamentos_recebidos"] == 200.0, f"Esperado R$ 200 recebidos, obtido {extrato_pes['resumo']['pagamentos_recebidos']}"
    assert extrato_pes["resumo"]["contas_a_receber"] == 100.0, f"Esperado R$ 100 pendente, obtido {extrato_pes['resumo']['contas_a_receber']}"

    # 7. Teste do Resumo Global
    print("\n7. Testando Resumo Global (get_resumo_financeiro_global)...")
    res_global = PaymentManager.get_resumo_financeiro_global()
    print(f"   Resumo Global: {res_global}")

    # 8. Teste dos Relatórios em Markdown
    print("\n8. Testando Gerador de Relatório Markdown...")
    md_emp = PaymentManager.gerar_relatorio_markdown_empresa(id_empresa)
    print("\n--- RELATÓRIO MARKDOWN DA EMPRESA ---")
    print(md_emp)

    md_global = PaymentManager.gerar_relatorio_markdown_global()
    print("\n--- RELATÓRIO MARKDOWN GLOBAL ---")
    print(md_global)

    print("\n" + "=" * 75)
    print("[OK] TODOS OS TESTES DO PAYMENT MANAGER PASSARAM COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    testar_payment_manager()
