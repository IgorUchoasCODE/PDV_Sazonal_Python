import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.factory import InventoryFlowManager
from br.com.pdv.src.memory.productClassFactory import productClassFactory
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida, UnidadeConjunto
from datetime import date

def rodar_teste_fluxo_completo():
    print("=" * 70)
    print("[+] INICIANDO TESTE DO FLUXO COMPLETO DO BANCO DE DADOS E MEMORIA")
    print("=" * 70)

    # 0. Garante inicializacao do banco
    BancoDB.inicializar_banco()

    # -------------------------------------------------------------------------
    # 1. CADASTRO DE PESSOA, EMPRESA, ENTIDADE (FORNECEDOR E CLIENTE) E REGISTROS
    # -------------------------------------------------------------------------
    print("\n--- 1. Cadastrando Pessoas, Empresas, Entidades e Registros ---")
    
    # Pessoa e Empresa para o Fornecedor
    id_pessoa_fornec = InventoryFlowManager.criar_pessoa("Carlos Alberto", sexo=1) # Masculino
    id_empresa_fornec = InventoryFlowManager.criar_empresa("Atacadão Distribuidora de Alimentos S.A.")
    
    # Entidade Fornecedor (Pessoa + Empresa)
    id_entidade_fornec = InventoryFlowManager.criar_entidade(
        id_pessoa=id_pessoa_fornec,
        id_empresa=id_empresa_fornec,
        fornecedor=True,
        cliente=False,
        funcionario=False
    )
    
    # Registros de contato do Fornecedor (Email = 1, Celular = 3)
    id_reg_email = InventoryFlowManager.adicionar_registro(id_entidade_fornec, tipo_registro=1, valor="contato@atacadao.com.br")
    id_reg_cel = InventoryFlowManager.adicionar_registro(id_entidade_fornec, tipo_registro=3, valor="(92) 99888-7766")
    
    print(f"[OK] Fornecedor cadastrado (ID Entidade: {id_entidade_fornec})")
    print(f"   - Email cadastrado (ID Registro: {id_reg_email}): contato@atacadao.com.br")
    print(f"   - Celular cadastrado (ID Registro: {id_reg_cel}): (92) 99888-7766")

    # Pessoa e Entidade para Cliente
    id_pessoa_cli = InventoryFlowManager.criar_pessoa("Maria das Gracas", sexo=2) # Feminino
    id_entidade_cli = InventoryFlowManager.criar_entidade(
        id_pessoa=id_pessoa_cli,
        id_empresa=None,
        fornecedor=False,
        cliente=True,
        funcionario=False
    )
    print(f"[OK] Cliente cadastrado (ID Entidade: {id_entidade_cli}) - Maria das Gracas")

    # -------------------------------------------------------------------------
    # 2. ADICIONAR UNIDADES DE CONJUNTO COM FATOR CONJUNTO
    # -------------------------------------------------------------------------
    print("\n--- 2. Cadastrando Unidades de Medida com Fator Conjunto ---")

    # Exemplo do prompt: caixa unidade conjunto e seu fator e 360
    id_um_ovos_360 = InventoryFlowManager.criar_unidade_medida("Caixa/Pacote (360 un.)", fatorConjunto=360)
    id_um_coca_12  = InventoryFlowManager.criar_unidade_medida("Fardo (12 un.)", fatorConjunto=12)
    id_um_agua_24  = InventoryFlowManager.criar_unidade_medida("Fardo (24 un.)", fatorConjunto=24)
    id_um_sabao_20 = InventoryFlowManager.criar_unidade_medida("Caixa (20 un.)", fatorConjunto=20)
    id_um_biscoito_50 = InventoryFlowManager.criar_unidade_medida("Caixa (50 un.)", fatorConjunto=50)

    print(f"[OK] Unidades de conjunto criadas com sucesso IDs: {[id_um_ovos_360, id_um_coca_12, id_um_agua_24, id_um_sabao_20, id_um_biscoito_50]}")

    # -------------------------------------------------------------------------
    # 3. CADASTRO DE 10 PRODUTOS (5 CONJUNTOS + 5 DEPENDENTES/UNIDADES)
    # -------------------------------------------------------------------------
    print("\n--- 3. Cadastrando 10 Produtos (5 Conjuntos e 5 Dependentes) ---")

    # 5 Produtos Unidade de Conjunto
    p1_id = InventoryFlowManager.criar_produto("Caixa de Ovos Branco A (360 un.)", diasDuraveis=30, unidadeMedida=id_um_ovos_360, varejo=180.00)
    p2_id = InventoryFlowManager.criar_produto("Fardo de Coca-Cola 350ml (12 un.)", diasDuraveis=180, unidadeMedida=id_um_coca_12, varejo=42.00)
    p3_id = InventoryFlowManager.criar_produto("Fardo de Agua Mineral 500ml (24 un.)", diasDuraveis=365, unidadeMedida=id_um_agua_24, varejo=28.00)
    p4_id = InventoryFlowManager.criar_produto("Caixa de Sabao em Po 1kg (20 un.)", diasDuraveis=730, unidadeMedida=id_um_sabao_20, varejo=160.00)
    p5_id = InventoryFlowManager.criar_produto("Caixa de Biscoito Recheado (50 un.)", diasDuraveis=120, unidadeMedida=id_um_biscoito_50, varejo=100.00)

    # 5 Produtos Dependentes / Unidades Avulsas (unidadeMedida = 1 "Unidade")
    p6_id = InventoryFlowManager.criar_produto("Ovo Branco Avulso (Unidade)", diasDuraveis=15, unidadeMedida=1, varejo=0.75)
    p7_id = InventoryFlowManager.criar_produto("Coca-Cola 350ml Lata (Unidade)", diasDuraveis=180, unidadeMedida=1, varejo=4.50)
    p8_id = InventoryFlowManager.criar_produto("Garrafa de Agua Mineral 500ml (Unidade)", diasDuraveis=365, unidadeMedida=1, varejo=2.00)
    p9_id = InventoryFlowManager.criar_produto("Caixa Sabao em Po 1kg Avulsa (Unidade)", diasDuraveis=730, unidadeMedida=1, varejo=9.50)
    p10_id = InventoryFlowManager.criar_produto("Pacote Biscoito Recheado Avulso (Unidade)", diasDuraveis=120, unidadeMedida=1, varejo=2.50)

    print("[OK] 10 Produtos inseridos no banco de dados com sucesso!")

    # Exemplo de teste com productClassFactory conforme productClassFactory.py
    print("\n--- Testando productClassFactory com molde e reconstrucao ---")
    molde_instrucoes = {
        "id": p1_id,
        "nome": "Caixa de Ovos Branco A (360 un.)",
        "diasDuraveis": 30,
        "unidadeMedida": "CONJUNTO/PACOTE (360 un.)",
        "fatorConjunto": 360
    }
    prod_objeto = productClassFactory.testar_e_fabricar(molde_instrucoes)
    prod_objeto.insertPropertValue(valorUnidario="140.00", quantidade="10")
    print(f"   Molde fabricado com sucesso: {prod_objeto.getDados(f=True)['nome']}")
    print(f"   Estoque formatado: {prod_objeto.getDados(f=True)['estoque']} fardos/caixas")

    # -------------------------------------------------------------------------
    # 4. ADICIONAR NOTA DE COMPRA (ENTRADA DE ESTOQUE)
    # -------------------------------------------------------------------------
    print("\n--- 4. Registrando Nota de Compra do Fornecedor ---")

    produtos_compra = [
        {"id_produto": p1_id, "quantidade": 10, "valorUnidario": 120.00}, # 10 caixas de 360 ovos a 120.00
        {"id_produto": p2_id, "quantidade": 50, "valorUnidario": 30.00},  # 50 fardos coca a 30.00
        {"id_produto": p3_id, "quantidade": 40, "valorUnidario": 18.00},  # 40 fardos agua a 18.00
        {"id_produto": p4_id, "quantidade": 15, "valorUnidario": 110.00}, # 15 caixas sabao a 110.00
        {"id_produto": p5_id, "quantidade": 20, "valorUnidario": 70.00},  # 20 caixas biscoito a 70.00
        {"id_produto": p6_id, "quantidade": 200, "valorUnidario": 0.40},  # 200 ovos avulsos
        {"id_produto": p7_id, "quantidade": 100, "valorUnidario": 2.80},  # 100 latas coca avulsas
        {"id_produto": p8_id, "quantidade": 120, "valorUnidario": 0.90},  # 120 aguas avulsas
        {"id_produto": p9_id, "quantidade": 50,  "valorUnidario": 6.50},  # 50 sabaos avulsos
        {"id_produto": p10_id, "quantidade": 150, "valorUnidario": 1.50} # 150 biscoitos avulsos
    ]

    res_compra = InventoryFlowManager.registrar_compra(
        id_representante=id_entidade_fornec,
        produtos=produtos_compra,
        data_vencimento=str(date.today())
    )

    print(f"[OK] Nota de Compra registrada com sucesso! ID da Nota: {res_compra['id_nota']}")

    # -------------------------------------------------------------------------
    # 5. REALIZAR VENDAS DOS PRODUTOS E REGISTRAR NOTAS DE PAGAMENTO
    # -------------------------------------------------------------------------
    print("\n--- 5. Registrando Venda dos Produtos e Pagamentos ---")

    produtos_venda = [
        {"id_produto": p1_id, "quantidade": 2, "valorUnidario": 180.00},  # 2 caixas de ovos
        {"id_produto": p2_id, "quantidade": 10, "valorUnidario": 42.00},  # 10 fardos coca
        {"id_produto": p6_id, "quantidade": 30, "valorUnidario": 0.75},   # 30 ovos avulsos
        {"id_produto": p7_id, "quantidade": 20, "valorUnidario": 4.50}    # 20 latas coca
    ]

    res_venda = InventoryFlowManager.registrar_venda(
        id_representante=id_entidade_cli,
        produtos=produtos_venda,
        data_vencimento=str(date.today())
    )
    id_nota_venda = res_venda['id_nota']
    print(f"[OK] Nota de Venda realizada com sucesso! ID da Nota: {id_nota_venda}")

    # Calcular o valor total da venda para registrar os pagamentos
    valor_total_venda = (2 * 180.00) + (10 * 42.00) + (30 * 0.75) + (20 * 4.50)
    print(f"   Valor Total da Venda: R$ {valor_total_venda:.2f}")

    # Registrar Pagamentos para essa venda (Ex: Parte em PIX = ID 2, Parte em CARTAO CREDIT0 = ID 4)
    id_pag1 = InventoryFlowManager.registrar_pagamento(
        id_fluxo_nota=id_nota_venda,
        id_forma_pagamento=2, # PIX
        valor=500.00,
        data_pagamento=str(date.today())
    )

    id_pag2 = InventoryFlowManager.registrar_pagamento(
        id_fluxo_nota=id_nota_venda,
        id_forma_pagamento=4, # CARTAO DE CREDITO
        valor=valor_total_venda - 500.00,
        data_pagamento=str(date.today())
    )

    print(f"[OK] Pagamentos registrados para a Nota de Venda #{id_nota_venda}:")
    print(f"   - Pagamento 1 (PIX): R$ 500.00 (ID: {id_pag1})")
    print(f"   - Pagamento 2 (Cartao de Credito): R$ {valor_total_venda - 500.00:.2f} (ID: {id_pag2})")

    # -------------------------------------------------------------------------
    # 6. CONSULTA FINAL E DEMONSTRACAO DO BANCO DE DADOS
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("[=] DEMONSTRACAO DO ESTADO FINAL DO BANCO DE DADOS")
    print("=" * 70)

    # Detalhes da Nota de Venda
    dados_nota = InventoryFlowManager.consultar_fluxo_nota(id_nota_venda)
    print(f"\n[*] Detalhes da Nota #{id_nota_venda} (Tipo: {dados_nota['nota']['id_tipoNota']}):")
    print("   Itens da Nota:")
    for item in dados_nota["itens"]:
        print(f"     - Produto: {item['produto_nome']} | Qtd: {item['quantidade']} | Valor Unid: R$ {item['valorUnidario']:.2f} | Lucro: R$ {item['lucroTotal']:.2f}")
    
    print("   Pagamentos vinculados:")
    for pag in dados_nota["pagamentos"]:
        print(f"     - Forma: {pag['forma_descricao']} | Valor: R$ {pag['valor']:.2f} | Data: {pag['data_pagamento']}")

    # Consultar Entidade do Fornecedor com Registros
    entidade_info = InventoryFlowManager.consultar_entidade(id_entidade_fornec)
    print(f"\n[*] Entidade Fornecedor #{id_entidade_fornec}:")
    print(f"   Pessoa: {entidade_info['entidade']['pessoa_nome']} | Empresa: {entidade_info['entidade']['empresa_nome']}")
    print("   Contatos Cadastrados:")
    for reg in entidade_info["registros"]:
        print(f"     - Tipo {reg['id_tipos_registros']}: {reg['registro']}")

    print("\n[SUCCESS] TODO O FLUXO FOI TESTADO E EXECUTADO COM SUCESSO NO SEU BANCO DE DADOS!")
    print("=" * 70)

if __name__ == "__main__":
    rodar_teste_fluxo_completo()
