"""
Teste de Criação e Vínculo de Entidades (As 3 Entidades)
=========================================================
Verifica se o sistema cria e diferencia corretamente as 3 entidades:
  1. Entidade Pessoa Pura (id_pessoa = X, id_empresa = NULL)
  2. Entidade Empresa Pura (id_pessoa = NULL, id_empresa = Y)
  3. Entidade de Vínculo Pessoa+Empresa (id_pessoa = X, id_empresa = Y, id_cargo = Z)
     com suporte às 3 opções ativas ao mesmo tempo (cliente=1, fornecedor=1, funcionario=1).
"""
import sys
sys.path.insert(0, '.')

from br.com.pdv.src.memory.paymentManager import PaymentManager

def testar_tres_entidades():
    print("=" * 75)
    print("TESTE DE CRIAÇÃO E DIFERENCIAÇÃO DAS 3 ENTIDADES")
    print("=" * 75)

    # 1. Cadastra Pessoa Pura (Entidade #1)
    print("\n1. Cadastrando Pessoa Pura (João Silva)...")
    res_p = PaymentManager.cadastrar_pessoa({
        "nome": "JOAO SILVA TESTE ENTIDADE",
        "sexo": "MASCULINO",
        "is_cliente": True,
        "is_fornecedor": False,
        "is_funcionario": False
    })
    print(f"   Resultado Pessoa Pura: {res_p}")
    assert res_p["sucesso"] is True
    id_pessoa = res_p["id_pessoa"]
    id_entidade_pessoa = res_p["id_entidade"]

    # 2. Cadastra Empresa Pura (Entidade #2)
    print("\n2. Cadastrando Empresa Pura (Empresa Betânia LTDA)...")
    res_e = PaymentManager.cadastrar_empresa({
        "nome": "EMPRESA BETANIA LTDA TESTE",
        "is_cliente": False,
        "is_fornecedor": True,
        "is_funcionario": False
    })
    print(f"   Resultado Empresa Pura: {res_e}")
    assert res_e["sucesso"] is True
    id_empresa = res_e["id_empresa"]
    id_entidade_empresa = res_e["id_entidade_empresa"]

    # 3. Cria a 3ª Entidade: Vínculo Pessoa + Empresa + Cargo + As 3 opções ativas
    print("\n3. Criando a 3ª Entidade: Vínculo João Silva + Empresa Betânia + Cargo (Gerente) + 3 Opções Ativas...")
    res_v = PaymentManager.vincular_pessoa_empresa({
        "id_pessoa": id_pessoa,
        "id_empresa": id_empresa,
        "cargo": "GERENTE",  # Cargo = Gerente
        "is_cliente": True,      # Opção 1
        "is_fornecedor": True,   # Opção 2
        "is_funcionario": True   # Opção 3 (as 3 ativas ao mesmo tempo!)
    })
    print(f"   Resultado Entidade Vínculo: {res_v}")
    assert res_v["sucesso"] is True
    id_entidade_vinculo = res_v["id_entidade"]

    # 4. Verifica a existência e independência das 3 Entidades distintas
    print("\n4. Verificando a existência e separação das 3 Entidades no banco...")
    print(f"   - ID Entidade Pessoa Pura  : {id_entidade_pessoa}")
    print(f"   - ID Entidade Empresa Pura : {id_entidade_empresa}")
    print(f"   - ID Entidade de Vínculo   : {id_entidade_vinculo}")

    assert id_entidade_pessoa != id_entidade_empresa, "Entidades não devem ser iguais!"
    assert id_entidade_pessoa != id_entidade_vinculo, "Entidade de vínculo deve ser diferente da entidade pura de pessoa!"
    assert id_entidade_empresa != id_entidade_vinculo, "Entidade de vínculo deve ser diferente da entidade pura de empresa!"

    # 5. Consulta a lista detalhada de entidades
    print("\n5. Consultando 'obter_entidades_detalhadas'...")
    todas_entidades = PaymentManager.obter_entidades_detalhadas()
    
    ent_p_info = next(e for e in todas_entidades if e["id_entidade"] == id_entidade_pessoa)
    ent_e_info = next(e for e in todas_entidades if e["id_entidade"] == id_entidade_empresa)
    ent_v_info = next(e for e in todas_entidades if e["id_entidade"] == id_entidade_vinculo)

    print(f"\n   [Entidade #1 Pessoa Pura]  : Tipo={ent_p_info['tipo_entidade']} | Nome={ent_p_info['pessoa_nome']}")
    print(f"   [Entidade #2 Empresa Pura] : Tipo={ent_e_info['tipo_entidade']} | Nome={ent_e_info['empresa_nome']}")
    print(f"   [Entidade #3 Vínculo]      : Tipo={ent_v_info['tipo_entidade']} | Pessoa={ent_v_info['pessoa_nome']} | Empresa={ent_v_info['empresa_nome']} | Cargos={ent_v_info['cargos']}")
    print(f"   [Papéis da Entidade #3]    : Cliente={ent_v_info['is_cliente']} | Fornecedor={ent_v_info['is_fornecedor']} | Funcionário={ent_v_info['is_funcionario']}")

    assert ent_p_info["tipo_entidade"] == "PESSOA_PURA"
    assert ent_e_info["tipo_entidade"] == "EMPRESA_PURA"
    assert ent_v_info["tipo_entidade"] == "VINCULO_PESSOA_EMPRESA"
    assert ent_v_info["is_cliente"] is True and ent_v_info["is_fornecedor"] is True and ent_v_info["is_funcionario"] is True, "A entidade de vínculo deve ter as 3 opções ativas ao mesmo tempo!"
    assert len(ent_v_info["cargos"]) > 0 and ent_v_info["cargos"][0]["descricao"] == "Gerente", f"Esperado cargo Gerente, obtido: {ent_v_info['cargos']}"

    print("\n" + "=" * 75)
    print("[OK] TESTE DAS 3 ENTIDADES E CARGOS CONCLUÍDO COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    testar_tres_entidades()
