"""
PDV Sazonal — Interface de Linha de Comando (CLI)
Menu interativo no terminal com todas as funcionalidades do sistema.
Executar: python -m br.com.pdv.src.interfaceGrafica.cli
"""
from br.com.pdv.src.memory.inventoryFlowManage import InventoryFlowManager as IFM
from br.com.pdv.src.BDD.queryEnum import DB
from datetime import date


# ========== UTILITÁRIOS DE EXIBIÇÃO ==========

def limpar():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def cabecalho(titulo: str):
    print(f"\n{'═' * 50}")
    print(f"  {titulo}")
    print(f"{'═' * 50}")


def subcabecalho(titulo: str):
    print(f"\n  ── {titulo} ──")


def exibir_tabela(dados: list, colunas: list = None):
    """Exibe uma lista de dicts como tabela formatada."""
    if not dados:
        print("  (nenhum registro encontrado)")
        return

    if colunas is None:
        colunas = list(dados[0].keys())

    # Calcula larguras
    larguras = {}
    for col in colunas:
        larguras[col] = max(len(str(col)), max(len(str(d.get(col, ""))) for d in dados))

    # Header
    header = " │ ".join(str(col).ljust(larguras[col]) for col in colunas)
    separador = "─┼─".join("─" * larguras[col] for col in colunas)
    print(f"  {header}")
    print(f"  {separador}")

    # Rows
    for d in dados:
        row = " │ ".join(str(d.get(col, "")).ljust(larguras[col]) for col in colunas)
        print(f"  {row}")


def input_int(msg: str, default=None) -> int:
    while True:
        valor = input(msg).strip()
        if valor == "" and default is not None:
            return default
        try:
            return int(valor)
        except ValueError:
            print("  ⚠ Informe um número inteiro válido.")


def input_float(msg: str, default=None) -> float:
    while True:
        valor = input(msg).strip()
        if valor == "" and default is not None:
            return default
        try:
            return float(valor)
        except ValueError:
            print("  ⚠ Informe um número válido.")


def input_str(msg: str, default="") -> str:
    valor = input(msg).strip()
    return valor if valor else default


def input_bool(msg: str, default=False) -> bool:
    valor = input(f"{msg} (s/n): ").strip().lower()
    if valor in ("s", "sim", "1", "true"):
        return True
    if valor in ("n", "nao", "não", "0", "false"):
        return False
    return default


def pausar():
    input("\n  Pressione ENTER para continuar...")


# ========== MENU PRINCIPAL ==========

def menu_principal():
    while True:
        cabecalho("PDV SAZONAL - MENU PRINCIPAL")
        print("  1. Cadastros")
        print("  2. Notas (Compra/Venda/Devolução/Perda/Compensação)")
        print("  3. Estoque")
        print("  4. Análise Sazonal")
        print("  5. Consultas")
        print("  6. Pagamentos")
        print("  0. Sair")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            menu_cadastros()
        elif opcao == "2":
            menu_notas()
        elif opcao == "3":
            menu_estoque()
        elif opcao == "4":
            menu_sazonal()
        elif opcao == "5":
            menu_consultas()
        elif opcao == "6":
            menu_pagamentos()
        elif opcao == "0":
            print("\n  Até logo! 👋")
            break
        else:
            print("  ⚠ Opção inválida.")


# ========== MENU CADASTROS ==========

def menu_cadastros():
    while True:
        cabecalho("CADASTROS")
        print("  1. Cadastrar Produto")
        print("  2. Cadastrar Pessoa")
        print("  3. Cadastrar Empresa")
        print("  4. Cadastrar Entidade (vincular pessoa/empresa)")
        print("  5. Adicionar Registro (contato)")
        print("  6. Atribuir Cargo")
        print("  7. Listar Produtos")
        print("  8. Listar Entidades")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            cadastrar_produto()
        elif opcao == "2":
            cadastrar_pessoa()
        elif opcao == "3":
            cadastrar_empresa()
        elif opcao == "4":
            cadastrar_entidade()
        elif opcao == "5":
            adicionar_registro()
        elif opcao == "6":
            atribuir_cargo()
        elif opcao == "7":
            listar_produtos()
        elif opcao == "8":
            listar_entidades()
        elif opcao == "0":
            break


def cadastrar_produto():
    subcabecalho("NOVO PRODUTO")

    # Exibe unidades disponíveis
    unidades = DB.SELECT.UNIDADE_MEDIDA_TODOS.buscar()
    print("  Unidades de Medida:")
    for u in unidades:
        print(f"    {u['id']}. {u['descricao']}")

    nome = input_str("  Nome: ")
    if not nome:
        print("  ⚠ Nome obrigatório.")
        return

    dias = input_int("  Dias duráveis [365]: ", 365)
    unidade = input_int("  Unidade de Medida (ID) [1]: ", 1)
    receita = input_bool("  É receita?", False)
    varejo = input_float("  Preço Varejo [0]: ", 0)
    atacado = input_float("  Preço Atacado [0]: ", 0)
    promocao = input_float("  Preço Promoção [0]: ", 0)

    try:
        id_novo = IFM.criar_produto(nome, dias, unidade, receita, varejo, atacado, promocao)
        print(f"\n  ✅ Produto cadastrado com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def cadastrar_pessoa():
    subcabecalho("NOVA PESSOA")

    sexos = IFM.listar_sexos()
    print("  Sexo:")
    for s in sexos:
        print(f"    {s['id']}. {s['descricao']}")

    nome = input_str("  Nome: ")
    if not nome:
        print("  ⚠ Nome obrigatório.")
        return
    sexo = input_int("  Sexo (ID) [3]: ", 3)

    try:
        id_novo = IFM.criar_pessoa(nome, sexo)
        print(f"\n  ✅ Pessoa cadastrada com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def cadastrar_empresa():
    subcabecalho("NOVA EMPRESA")
    nome = input_str("  Nome: ")
    if not nome:
        print("  ⚠ Nome obrigatório.")
        return

    try:
        id_novo = IFM.criar_empresa(nome)
        print(f"\n  ✅ Empresa cadastrada com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def cadastrar_entidade():
    subcabecalho("NOVA ENTIDADE")
    print("  Uma entidade vincula pessoa e/ou empresa com papéis (fornecedor/cliente/funcionário)")

    id_pessoa = input_int("  ID Pessoa (0 para nenhum) [0]: ", 0) or None
    id_empresa = input_int("  ID Empresa (0 para nenhum) [0]: ", 0) or None
    fornecedor = input_bool("  É fornecedor?", False)
    cliente = input_bool("  É cliente?", False)
    funcionario = input_bool("  É funcionário?", False)

    try:
        id_novo = IFM.criar_entidade(id_pessoa, id_empresa, fornecedor, cliente, funcionario)
        print(f"\n  ✅ Entidade cadastrada com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def adicionar_registro():
    subcabecalho("ADICIONAR REGISTRO/CONTATO")

    tipos = IFM.listar_tipos_registro()
    print("  Tipos de Registro:")
    for t in tipos:
        print(f"    {t['id']}. {t['descricao']}")

    id_entidade = input_int("  ID Entidade: ")
    tipo = input_int("  Tipo (ID): ")
    valor = input_str("  Valor (ex: email, telefone): ")

    try:
        id_novo = IFM.adicionar_registro(id_entidade, tipo, valor)
        print(f"\n  ✅ Registro adicionado com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def atribuir_cargo():
    subcabecalho("ATRIBUIR CARGO")

    cargos = IFM.listar_cargos()
    print("  Cargos:")
    for c in cargos:
        print(f"    {c['id']}. {c['descricao']}")

    id_entidade = input_int("  ID Entidade: ")
    id_cargo = input_int("  ID Cargo: ")

    try:
        id_novo = IFM.atribuir_cargo(id_entidade, id_cargo)
        print(f"\n  ✅ Cargo atribuído com ID: {id_novo}")
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def listar_produtos():
    subcabecalho("PRODUTOS CADASTRADOS")
    produtos = IFM.obter_todos_produtos()
    colunas = ["id", "nome", "diasDuraveis", "unidade_descricao", "varejo", "atacado", "promocao"]
    exibir_tabela(produtos, colunas)
    pausar()


def listar_entidades():
    subcabecalho("ENTIDADES CADASTRADAS")
    entidades = DB.SELECT.VW_ENTIDADE_COMPLETA_TODOS.buscar()
    colunas = ["id", "pessoa_nome", "empresa_nome", "fornecedor", "cliente", "funcionario"]
    exibir_tabela(entidades, colunas)
    pausar()


# ========== MENU NOTAS ==========

def menu_notas():
    while True:
        cabecalho("NOTAS DE FLUXO")
        print("  1. Registrar Compra")
        print("  2. Registrar Venda")
        print("  3. Registrar Devolução")
        print("  4. Registrar Perda")
        print("  5. Registrar Compensação")
        print("  6. Consultar Nota")
        print("  7. Listar Todas as Notas")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            registrar_nota_fluxo("COMPRA")
        elif opcao == "2":
            registrar_nota_fluxo("VENDA")
        elif opcao == "3":
            registrar_nota_fluxo("DEVOLUCAO")
        elif opcao == "4":
            registrar_nota_fluxo("PERDA")
        elif opcao == "5":
            registrar_nota_fluxo("COMPENSACAO")
        elif opcao == "6":
            consultar_nota()
        elif opcao == "7":
            listar_notas()
        elif opcao == "0":
            break


def registrar_nota_fluxo(tipo: str):
    subcabecalho(f"NOVA NOTA - {tipo}")

    # Exibe entidades disponíveis
    if tipo == "COMPRA":
        print("  Fornecedores:")
        fornecedores = IFM.consultar_fornecedores()
        exibir_tabela(fornecedores, ["id", "pessoa_nome", "empresa_nome"])
    else:
        print("  Clientes:")
        clientes = IFM.consultar_clientes()
        exibir_tabela(clientes, ["id", "pessoa_nome", "empresa_nome"])

    id_representante = input_int("  ID Representante (entidade): ")

    id_nota_origem = None
    if tipo in ("DEVOLUCAO", "PERDA", "COMPENSACAO"):
        id_nota_origem = input_int("  ID Nota de Origem: ")

    data_vencimento = input_str(f"  Data Vencimento (YYYY-MM-DD) [{date.today()}]: ") or None

    # Adicionar produtos
    produtos = []
    print("\n  Adicione produtos (digite 0 para finalizar):")

    # Exibe produtos disponíveis
    listar_produtos_resumo()

    while True:
        id_produto = input_int("  ID Produto (0 = finalizar): ", 0)
        if id_produto == 0:
            break

        quantidade = input_float("  Quantidade: ")
        valor_unitario = input_float("  Valor Unitário: ")

        produtos.append({
            "id_produto": id_produto,
            "quantidade": quantidade,
            "valorUnidario": valor_unitario,
            "lucroTotal": 0
        })
        print(f"    ✓ Produto {id_produto} adicionado.")

    if not produtos:
        print("  ⚠ Nenhum produto adicionado. Nota cancelada.")
        pausar()
        return

    try:
        if tipo == "COMPRA":
            resultado = IFM.registrar_compra(id_representante, produtos, id_nota_origem, data_vencimento)
        elif tipo == "VENDA":
            resultado = IFM.registrar_venda(id_representante, produtos, id_nota_origem, data_vencimento)
        elif tipo == "DEVOLUCAO":
            resultado = IFM.registrar_devolucao(id_representante, id_nota_origem, produtos)
        elif tipo == "PERDA":
            tipo_origem = input_str("  Tipo Origem (DEVOLUCAO/ESTOQUE) [ESTOQUE]: ", "ESTOQUE")
            resultado = IFM.registrar_perda(id_representante, id_nota_origem, tipo_origem, produtos)
        elif tipo == "COMPENSACAO":
            resultado = IFM.registrar_compensacao(id_representante, id_nota_origem, produtos)
        else:
            print("  ⚠ Tipo inválido.")
            pausar()
            return

        print(f"\n  ✅ Nota registrada!")
        print(f"  ID Nota: {resultado['id_nota']}")
        print(f"  Tipo: {resultado['tipo']}")
        print(f"  Itens: {len(resultado['itens'])}")

    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
    pausar()


def listar_produtos_resumo():
    produtos = IFM.obter_todos_produtos()
    if produtos:
        colunas = ["id", "nome", "varejo"]
        exibir_tabela(produtos[:20], colunas)


def consultar_nota():
    subcabecalho("CONSULTAR NOTA")
    id_nota = input_int("  ID da Nota: ")

    resultado = IFM.consultar_fluxo_nota(id_nota)
    if not resultado:
        print("  ⚠ Nota não encontrada.")
        pausar()
        return

    nota = resultado["nota"]
    print(f"\n  Nota #{nota['id']} | Tipo: {nota['id_tipoNota']} | Representante: {nota['id_representante']}")
    if nota.get("data_vencimento"):
        print(f"  Vencimento: {nota['data_vencimento']}")
    if nota.get("id_notaOrigem"):
        print(f"  Nota Origem: #{nota['id_notaOrigem']}")

    subcabecalho("Itens")
    if resultado["itens"]:
        exibir_tabela(resultado["itens"], ["id", "produto_nome", "quantidade", "valorUnidario", "lucroTotal", "data"])

    subcabecalho("Pagamentos")
    if resultado["pagamentos"]:
        exibir_tabela(resultado["pagamentos"], ["id", "forma_descricao", "valor", "data_pagamento"])
    else:
        print("  (sem pagamentos registrados)")

    pausar()


def listar_notas():
    subcabecalho("TODAS AS NOTAS")
    notas = DB.SELECT.FLUXO_NOTA_ESTOQUE_TODOS.buscar()
    if notas:
        exibir_tabela(notas, ["id", "id_tipoNota", "id_representante", "id_notaOrigem", "data_vencimento"])
    else:
        print("  (nenhuma nota encontrada)")
    pausar()


# ========== MENU ESTOQUE ==========

def menu_estoque():
    while True:
        cabecalho("ESTOQUE")
        print("  1. Consultar Estoque Geral")
        print("  2. Consultar Produto Específico")
        print("  3. Resumo de Vendas")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            subcabecalho("ESTOQUE GERAL")
            estoque = IFM.consultar_estoque()
            if estoque:
                exibir_tabela(estoque, ["id_produto", "nome", "total_entrada", "total_venda", "total_devolucao", "total_perda", "total_reposicao"])
            else:
                print("  (sem movimentações)")
            pausar()

        elif opcao == "2":
            id_produto = input_int("  ID Produto: ")
            estoque = IFM.consultar_estoque(id_produto)
            if estoque:
                exibir_tabela(estoque, ["id_produto", "nome", "total_entrada", "total_venda", "total_devolucao", "total_perda", "total_reposicao"])
            else:
                print("  (sem movimentações para este produto)")
            pausar()

        elif opcao == "3":
            subcabecalho("RESUMO DE VENDAS")
            resumo = IFM.consultar_resumo_vendas()
            if resumo:
                exibir_tabela(resumo, ["id_produto", "produto_nome", "total_vendido", "receita_total", "lucro_total", "qtd_transacoes"])
            else:
                print("  (sem vendas registradas)")
            pausar()

        elif opcao == "0":
            break


# ========== MENU SAZONAL ==========

def menu_sazonal():
    while True:
        cabecalho("ANÁLISE SAZONAL")
        print("  1. Registrar Snapshot (clima + rios + eventos)")
        print("  2. Ver Análise Sazonal Geral")
        print("  3. Ver Análise por Produto")
        print("  4. Consultar Clima Atual (API)")
        print("  5. Consultar Nível dos Rios (API)")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            registrar_snapshot()
        elif opcao == "2":
            subcabecalho("ANÁLISE SAZONAL GERAL")
            analise = IFM.consultar_analise_sazonal()
            if analise:
                exibir_tabela(analise, ["data_registro", "produto_nome", "quantidade",
                                         "indicador_clima", "indicador_rio", "indicador_chuva",
                                         "qtd_eventos_proximos", "lucro_item"])
            else:
                print("  (sem dados sazonais)")
            pausar()
        elif opcao == "3":
            id_produto = input_int("  ID Produto: ")
            analise = IFM.consultar_analise_sazonal(id_produto)
            if analise:
                exibir_tabela(analise, ["data_registro", "produto_nome", "quantidade",
                                         "indicador_clima", "indicador_rio", "indicador_chuva",
                                         "qtd_eventos_proximos", "lucro_item"])
            else:
                print("  (sem dados sazonais para este produto)")
            pausar()
        elif opcao == "4":
            consultar_clima_api()
        elif opcao == "5":
            consultar_rios_api()
        elif opcao == "0":
            break


def registrar_snapshot():
    subcabecalho("REGISTRAR SNAPSHOT SAZONAL")
    id_nota = input_int("  ID da Nota de Fluxo: ")

    print("\n  Buscando dados meteorológicos...")
    dados_clima = None
    dados_rios = None
    qtd_eventos = 0

    try:
        from br.com.pdv.src.apis.meteorologia.clima import ClimaAPI
        dados_clima = ClimaAPI.obter_previsao_tempo("Manaus")
        if dados_clima:
            print(f"  ✓ Clima: {dados_clima['atual']['temperatura']}°C")
    except Exception as e:
        print(f"  ⚠ Erro ao buscar clima: {e}")

    try:
        from br.com.pdv.src.apis.meteorologia.clima import ClimaAPI
        dados_rios = ClimaAPI.obter_nivel_rios()
        if dados_rios:
            print(f"  ✓ Rios: {len(dados_rios.get('rios', {}))} rios consultados")
    except Exception as e:
        print(f"  ⚠ Erro ao buscar rios: {e}")

    try:
        from br.com.pdv.src.apis.eventos.eventos_api import EventosAPI
        api_eventos = EventosAPI()
        eventos_proximos = api_eventos.obter_eventos_proximos(7)
        qtd_eventos = len(eventos_proximos)
        print(f"  ✓ Eventos próximos: {qtd_eventos}")
    except Exception as e:
        print(f"  ⚠ Erro ao buscar eventos: {e}")

    try:
        id_snap = IFM.registrar_snapshot_sazonal(id_nota, dados_clima, dados_rios, qtd_eventos)
        print(f"\n  ✅ Snapshot registrado com ID: {id_snap}")
    except Exception as e:
        print(f"\n  ❌ Erro ao salvar snapshot: {e}")
    pausar()


def consultar_clima_api():
    subcabecalho("CLIMA ATUAL (API)")
    cidade = input_str("  Cidade [Manaus]: ", "Manaus")

    try:
        from br.com.pdv.src.apis.meteorologia.clima import ClimaAPI
        dados = ClimaAPI.obter_previsao_tempo(cidade)
        if dados:
            atual = dados["atual"]
            print(f"\n  🌡  Temperatura: {atual['temperatura']}°C")
            print(f"  🌡  Sensação: {atual['sensacaoTermica']}°C")
            print(f"  💧 Umidade: {atual['umidadeRelativa']}%")
            print(f"  🌧  Precipitação: {atual['precipitacao_mm']} mm")
            print(f"  💨 Vento: {atual['velocidadeVento_kmh']} km/h")

            print(f"\n  Previsão 7 dias:")
            for dia in dados["previsao7dias"]:
                print(f"    {dia['data']}: Min {dia['temperaturaMinima']}°C / Max {dia['temperaturaMaxima']}°C | Chuva: {dia['precipitacao_mm']}mm")
        else:
            print("  ⚠ Não foi possível obter dados climáticos.")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
    pausar()


def consultar_rios_api():
    subcabecalho("NÍVEL DOS RIOS (API)")

    try:
        from br.com.pdv.src.apis.meteorologia.clima import ClimaAPI
        dados = ClimaAPI.obter_nivel_rios()
        if dados:
            for nome_rio, info in dados["rios"].items():
                if "erro" in info:
                    print(f"  {nome_rio}: {info['erro']}")
                    continue
                print(f"\n  🌊 {nome_rio}:")
                for dia in info.get("previsao7dias", [])[:3]:
                    print(f"    {dia['data']}: Vazão {dia['vazao_m3s']} m³/s")
        else:
            print("  ⚠ Não foi possível obter dados dos rios.")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
    pausar()


# ========== MENU CONSULTAS ==========

def menu_consultas():
    while True:
        cabecalho("CONSULTAS")
        print("  1. Fornecedores")
        print("  2. Clientes")
        print("  3. Detalhes de Entidade")
        print("  4. Formas de Pagamento")
        print("  5. Tipos de Nota")
        print("  6. Cargos")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            subcabecalho("FORNECEDORES")
            dados = IFM.consultar_fornecedores()
            exibir_tabela(dados, ["id", "pessoa_nome", "empresa_nome"])
            pausar()
        elif opcao == "2":
            subcabecalho("CLIENTES")
            dados = IFM.consultar_clientes()
            exibir_tabela(dados, ["id", "pessoa_nome", "empresa_nome"])
            pausar()
        elif opcao == "3":
            id_ent = input_int("  ID Entidade: ")
            dados = IFM.consultar_entidade(id_ent)
            if dados:
                ent = dados["entidade"]
                print(f"\n  Entidade #{ent['id']}")
                print(f"  Pessoa: {ent.get('pessoa_nome', '-')}")
                print(f"  Empresa: {ent.get('empresa_nome', '-')}")
                print(f"  Fornecedor: {'Sim' if ent.get('fornecedor') else 'Não'}")
                print(f"  Cliente: {'Sim' if ent.get('cliente') else 'Não'}")

                if dados["registros"]:
                    subcabecalho("Registros")
                    exibir_tabela(dados["registros"], ["id", "id_tipos_registros", "registro"])
                if dados["cargos"]:
                    subcabecalho("Cargos")
                    exibir_tabela(dados["cargos"], ["id", "id_cargo"])
            else:
                print("  ⚠ Entidade não encontrada.")
            pausar()
        elif opcao == "4":
            subcabecalho("FORMAS DE PAGAMENTO")
            exibir_tabela(IFM.listar_formas_pagamento(), ["id", "descricao"])
            pausar()
        elif opcao == "5":
            subcabecalho("TIPOS DE NOTA")
            exibir_tabela(IFM.listar_tipos_nota(), ["id", "descricao"])
            pausar()
        elif opcao == "6":
            subcabecalho("CARGOS")
            exibir_tabela(IFM.listar_cargos(), ["id", "descricao"])
            pausar()
        elif opcao == "0":
            break


# ========== MENU PAGAMENTOS ==========

def menu_pagamentos():
    while True:
        cabecalho("PAGAMENTOS")
        print("  1. Registrar Pagamento")
        print("  2. Ver Pagamentos de uma Nota")
        print("  0. Voltar")

        opcao = input_str("\n  Opção: ")

        if opcao == "1":
            subcabecalho("REGISTRAR PAGAMENTO")

            formas = IFM.listar_formas_pagamento()
            print("  Formas de Pagamento:")
            for f in formas:
                print(f"    {f['id']}. {f['descricao']}")

            id_nota = input_int("  ID da Nota: ")
            id_forma = input_int("  Forma de Pagamento (ID): ")
            valor = input_float("  Valor: ")
            data_pag = input_str(f"  Data Pagamento [{date.today()}]: ", str(date.today()))

            try:
                id_pag = IFM.registrar_pagamento(id_nota, id_forma, valor, data_pag)
                print(f"\n  ✅ Pagamento registrado com ID: {id_pag}")
            except Exception as e:
                print(f"\n  ❌ Erro: {e}")
            pausar()

        elif opcao == "2":
            id_nota = input_int("  ID da Nota: ")
            pagamentos = DB.SELECT.VW_PAGAMENTOS_NOTA.buscar(id_nota)
            if pagamentos:
                exibir_tabela(pagamentos, ["id", "forma_descricao", "valor", "data_pagamento"])
            else:
                print("  (sem pagamentos)")
            pausar()

        elif opcao == "0":
            break


# ========== ENTRY POINT ==========

if __name__ == "__main__":
    menu_principal()
