# -*- coding: utf-8 -*-
from functools import wraps

import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core import helpers


def _corpo_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return {}


# ─────────────────────────────────────────────────────────────────────────
# Autenticação simples baseada em sessão (sem django.contrib.auth)
# ─────────────────────────────────────────────────────────────────────────
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_autenticado'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.session.get('usuario_autenticado'):
        return redirect('dashboard')

    erro = None
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        senha = request.POST.get('senha', '')
        if usuario == settings.APP_USUARIO and senha == settings.APP_SENHA:
            request.session['usuario_autenticado'] = True
            request.session['usuario_nome'] = usuario
            return redirect('dashboard')
        erro = 'Usuário ou senha inválidos. Tente novamente.'

    return render(request, 'login.html', {'erro': erro})


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────
# Páginas principais
# ─────────────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    ctx = helpers.dashboard_context()
    ctx['pagina_atual'] = 'dashboard'
    return render(request, 'dashboard.html', ctx)


@login_required
def produtos(request):
    ctx = helpers.produtos_context()
    ctx['pagina_atual'] = 'produtos'
    return render(request, 'produtos.html', ctx)


@login_required
def estoque(request):
    ctx = helpers.estoque_context()
    ctx['pagina_atual'] = 'estoque'
    return render(request, 'estoque.html', ctx)


@login_required
def fornecedores(request):
    ctx = helpers.fornecedores_context()
    ctx['pagina_atual'] = 'fornecedores'
    return render(request, 'fornecedores.html', ctx)


@login_required
def clientes(request):
    ctx = helpers.clientes_context()
    ctx['pagina_atual'] = 'clientes'
    return render(request, 'clientes.html', ctx)


@login_required
def entidades(request):
    ctx = helpers.entidades_context()
    ctx['pagina_atual'] = 'entidades'
    return render(request, 'entidades.html', ctx)


@login_required
def relatorios(request):
    ctx = helpers.relatorios_context()
    ctx['pagina_atual'] = 'relatorios'
    return render(request, 'relatorios_sazonalizei.html', ctx)


@login_required
def pdv(request):
    ctx = helpers.pdv_context()
    ctx['pagina_atual'] = 'pdv'
    return render(request, 'pdv.html', ctx)


@login_required
def financeiro(request):
    ctx = helpers.financeiro_context()
    ctx['pagina_atual'] = 'financeiro'
    return render(request, 'financeiro.html', ctx)


@login_required
def configuracoes(request):
    ctx = {'pagina_atual': 'configuracoes'}
    return render(request, 'configuracoes.html', ctx)


# ─────────────────────────────────────────────────────────────────────────
# API leve usada pelo modal "Resumo Sazonal" do dashboard
# ─────────────────────────────────────────────────────────────────────────
@login_required
def api_resumo_sazonal(request, produto_id):
    catalogo = {p['id']: p for p in helpers.get_produtos_catalogo()}
    produto = catalogo.get(produto_id)
    if not produto:
        return JsonResponse({'sucesso': False, 'mensagem': 'Produto não encontrado.'})

    estoque = produto.get('estoque', 0)
    if estoque > 15:
        cor, status = 'green', 'PERÍODO FAVORÁVEL'
        motivo_bom = 'Estoque saudável e giro dentro do esperado para o período.'
        motivo_ruim = 'Nenhum alerta crítico identificado no momento.'
    elif estoque > 0:
        cor, status = 'amber', 'ATENÇÃO / GIRO'
        motivo_bom = 'Ainda há estoque disponível para atender a demanda atual.'
        motivo_ruim = 'Nível de estoque abaixo do ideal — considere repor em breve.'
    else:
        cor, status = 'red', 'PERÍODO NÃO FAVORÁVEL'
        motivo_bom = 'Sem indicadores favoráveis enquanto o estoque estiver zerado.'
        motivo_ruim = 'Produto sem estoque disponível — risco de perda de vendas.'

    return JsonResponse({
        'sucesso': True,
        'nome': produto['nome'],
        'cor': cor,
        'status': status,
        'estoque_atual': estoque,
        'motivo_benefico': motivo_bom,
        'motivo_desfavoravel': motivo_ruim,
        'clima_atual': 'Sem integração com API climática configurada.',
        'rio_atual': 'Sem integração com API fluviométrica configurada.',
    })


# ─────────────────────────────────────────────────────────────────────────
# API de gravação — chamadas pelo JavaScript dos templates existentes.
# Encaminham direto para o backend real (InventoryManager / PaymentManager).
# Sempre devolvem {"sucesso": bool, "mensagem": str, ...} em JSON.
# ─────────────────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def api_cadastrar_produto(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.BDD.queryEnum import DB
        nome = (dados.get('nome') or '').strip().upper()
        if not nome:
            return JsonResponse({'sucesso': False, 'mensagem': "O campo 'nome' é obrigatório."})
        id_produto = DB.INSERT.PRODUTO.executar(
            nome,
            int(dados.get('diasDuraveis', 365)),
            int(dados.get('id_unidade', 1)),
            bool(dados.get('is_conjunto', False)),
            float(dados.get('preco_venda', 0) or 0),
            float(dados.get('preco_atacado', 0) or 0),
            float(dados.get('preco_promocao', 0) or 0),
        )
        return JsonResponse({'sucesso': True, 'mensagem': f"Produto '{nome}' cadastrado.", 'id_produto': id_produto})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao cadastrar produto: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
def api_atualizar_preco_produto(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.BDD.queryEnum import DB
        id_produto = int(dados.get('id', 0))
        preco_venda = float(dados.get('preco_venda', 0))
        
        if id_produto <= 0 or preco_venda <= 0:
            return JsonResponse({'sucesso': False, 'mensagem': "Produto e preço são obrigatórios e maiores que zero."})
            
        from br.com.pdv.src.BDD.bancodb import BancoDB
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE produto SET varejo = ? WHERE id = ?", (preco_venda, id_produto))
            conn.commit()
            
        return JsonResponse({'sucesso': True, 'mensagem': "Preço atualizado com sucesso."})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao atualizar preço: {e}'})

@csrf_exempt
@require_http_methods(["POST"])
def api_comprar(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        nota = InventoryManager.insert_compra(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a compra. Confira fornecedor e produtos.'})
        return JsonResponse({'sucesso': True, 'mensagem': 'Compra registrada com sucesso.'})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar compra: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
def api_vender(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        nota = InventoryManager.insert_venda(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a venda. Confira cliente, produtos e estoque disponível.'})
        
        nota_dados = nota.getDados()
        id_nota = nota_dados.get("id")
        valor_total = nota_dados.get("valorTotalVenda", 0)
        
        pagamentos = dados.get("pagamentos", [])
        # Tratamento legado para suportar o formato antigo caso alguém ainda use
        if not pagamentos and "id_forma_pagamento" in dados and "valor_pagamento" in dados:
            pagamentos = [{"id_forma_pagamento": dados["id_forma_pagamento"], "valor": dados["valor_pagamento"]}]
            
        for p in pagamentos:
            v_pago = float(p.get("valor") or 0)
            id_forma = p.get("id_forma_pagamento")
            if v_pago > 0 and id_forma:
                PaymentManager.registrar_pagamento({
                    "id_fluxo_nota": id_nota,
                    "id_forma_pagamento": id_forma,
                    "valor": v_pago
                })
            
        return JsonResponse({
            'sucesso': True, 
            'mensagem': 'Venda registrada com sucesso.',
            'id_fluxo_nota': id_nota,
            'valor_total': valor_total
        })
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar venda: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
def api_perder(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        nota = InventoryManager.insert_perda(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a perda.'})
        return JsonResponse({'sucesso': True, 'mensagem': 'Perda registrada com sucesso.'})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar perda: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
def api_devolver(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        nota = InventoryManager.insert_devolucao(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a devolução.'})
            
        nota_dados = nota.getDados()
        id_nota = nota_dados.get("id")
        
        # Estorno
        pagamentos = dados.get("pagamentos", [])
        if not pagamentos and "id_forma_pagamento" in dados and "valor_pagamento" in dados:
            pagamentos = [{"id_forma_pagamento": dados["id_forma_pagamento"], "valor": dados["valor_pagamento"]}]
            
        for p in pagamentos:
            v_pago = float(p.get("valor") or 0)
            id_forma = p.get("id_forma_pagamento")
            if v_pago > 0 and id_forma:
                PaymentManager.registrar_pagamento({
                    "id_fluxo_nota": id_nota, 
                    "id_forma_pagamento": id_forma,
                    "valor": v_pago
                })
            
        return JsonResponse({'sucesso': True, 'mensagem': 'Devolução registrada com sucesso.', 'id_fluxo_nota': id_nota})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar devolução: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
def api_cadastrar_entidade(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        resultado = PaymentManager.cadastrar_entidade_completa(dados)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao cadastrar entidade: {e}'})

@csrf_exempt
@require_http_methods(["POST"])
def api_apagar_entidade(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        resultado = PaymentManager.apagar_entidade(dados.get("id"))
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao apagar entidade: {e}'})

@csrf_exempt
@require_http_methods(["POST"])
def api_editar_entidade(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        resultado = PaymentManager.editar_entidade(dados)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao editar entidade: {e}'})



@csrf_exempt
@require_http_methods(["POST"])
def api_registrar_pagamento(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        resultado = PaymentManager.registrar_pagamento(dados)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar pagamento: {e}'})

@csrf_exempt
@require_http_methods(["POST"])
def api_registrar_pagamento_entidade(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        id_entidade = dados.get("id_entidade")
        valor = dados.get("valor")
        id_forma = dados.get("id_forma_pagamento", 1)
        if not id_entidade or valor is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'id_entidade e valor são obrigatórios.'})
            
        resultado = PaymentManager.registrar_pagamento_por_entidade(id_entidade, valor, id_forma)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar pagamento: {e}'})

@csrf_exempt
@require_http_methods(["POST"])
def api_pagamento_lote(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        resultado = PaymentManager.registrar_pagamentos_lote(dados)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar pagamento em lote: {e}'})


@require_http_methods(["GET"])
def api_extrato_entidade(request, id_entidade):
    """Retorna o extrato financeiro de uma entidade específica para exibição no modal."""
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        import datetime

        extrato = PaymentManager.get_extrato_entidade(id_entidade)
        resumo = extrato.get("resumo", {})
        historico_pagamentos = extrato.get("historico_pagamentos", [])

        # Serializa datas
        pags_serializados = []
        for p in historico_pagamentos:
            p2 = dict(p)
            if hasattr(p2.get('data_pagamento'), 'isoformat'):
                p2['data_pagamento'] = p2['data_pagamento'].isoformat()
            pags_serializados.append(p2)

        return JsonResponse({
            "sucesso": True,
            "id_entidade": id_entidade,
            "resumo": resumo,
            "historico_pagamentos": pags_serializados[:20],
        })
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)})


def api_detalhes_pagamento(request, id):
    import datetime
    from django.http import HttpResponse, JsonResponse
    from br.com.pdv.src.BDD.bancodb import BancoDB
    
    def json_serial(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
        
    try:
        from br.com.pdv.src.memory.paymentManager import PaymentManager
        pagamentos = PaymentManager.obter_pagamentos_nota(id)
        
        with BancoDB.obter_conexao() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    fne.id, 
                    fne.id_tipoNota as tipo_id,
                    (SELECT indicador_clima FROM snapshot_sazonal WHERE id_fluxo_nota = fne.id LIMIT 1) as clima_atual,
                    (SELECT indicador_chuva FROM snapshot_sazonal WHERE id_fluxo_nota = fne.id LIMIT 1) as estacao_ano,
                    (SELECT evento_nome FROM snapshot_sazonal WHERE id_fluxo_nota = fne.id LIMIT 1) as evento_especial
                FROM fluxosNotasEstoque fne WHERE fne.id = ?
            """, (id,))
            nota_row = cur.fetchone()
            
        if nota_row:
            tipos = {1: "COMPRA", 2: "VENDA", 3: "DEVOLUÇÃO", 4: "PERDA", 5: "REPOSIÇÃO/COMPENSAÇÃO"}
            nota_row = dict(nota_row)
            
            from br.com.pdv.src.financeiro.notaPagamento import NotaPagamento
            for p in pagamentos:
                p['forma_pagamento_desc'] = NotaPagamento.FORMAS_PAGAMENTO_MAP.get(p.get('id_forma_pagamento', 1), "DINHEIRO")
                
            snapshot_sazonal = None
            if nota_row.get("clima_atual"):
                snapshot_sazonal = {
                    "clima_atual": nota_row.get("clima_atual"),
                    "estacao_ano": nota_row.get("estacao_ano"),
                    "evento_especial": nota_row.get("evento_especial")
                }
                
            dados = {
                "id_fluxo_nota": id,
                "nota_detalhes": {
                    "tipo": tipos.get(nota_row["tipo_id"], "DESCONHECIDO"),
                    "snapshot_sazonal": snapshot_sazonal
                },
                "pagamentos": pagamentos
            }
            dados_json = json.dumps({"sucesso": True, "dados": dados}, default=json_serial)
            return HttpResponse(dados_json, content_type="application/json")
            
        return JsonResponse({"sucesso": False, "mensagem": "Nota não encontrada."})
    except Exception as e:
        return JsonResponse({"sucesso": False, "mensagem": str(e)})


@require_http_methods(["GET"])
def api_buscar_produtos(request):
    termo = request.GET.get('q', '').strip().lower()
    tipo = request.GET.get('tipo', '').strip().lower()
    catalogo = helpers.get_produtos_catalogo()
    if termo:
        catalogo = [p for p in catalogo if termo in p['nome'].lower()]
    if tipo == 'simples':
        catalogo = [p for p in catalogo if not p.get('eh_composto')]
    return JsonResponse({'sucesso': True, 'produtos': catalogo})

@csrf_exempt
@require_http_methods(["POST"])
def api_compensar(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        nota = InventoryManager.insert_compensacao(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a reposição.'})
        return JsonResponse({'sucesso': True, 'mensagem': 'Reposição registrada com sucesso.'})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar reposição: {e}'})


# ─────────────────────────────────────────────────────────────────────────
# PDV — Perda Pós-Venda (fluxo encadeado: Devolução → Perda)
# ─────────────────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def api_perder_pos_venda(request):
    """
    Registra uma Perda Pós-Venda em duas etapas encadeadas:
      1. Cria uma Nota de Devolução referenciando a nota de devolução selecionada (ou a venda original)
      2. Cria uma Nota de Perda referenciando a devolução recém-criada

    Payload esperado:
    {
        "id_nota_devolucao": int,      # ID da devolução de origem
        "produtos": [...],             # itens a perder
        "data": "YYYY-MM-DD"           # opcional
    }
    """
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager

        id_nota_dev = dados.get("id_nota_devolucao")
        produtos = dados.get("produtos", [])
        data = dados.get("data", "")

        if not id_nota_dev:
            return JsonResponse({'sucesso': False, 'mensagem': "'id_nota_devolucao' é obrigatório."})
        if not produtos:
            return JsonResponse({'sucesso': False, 'mensagem': "'produtos' é obrigatório."})

        # Etapa 2 — Nota de Perda referenciando a devolução
        dados_perda = {
            "id_nota_origem": id_nota_dev,
            "produtos": produtos,
            "data": data,
        }
        nota_perda = InventoryManager.insert_perda(dados_perda)
        if nota_perda is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Falha ao criar a Nota de Perda.'})

        nota_perda_dados = nota_perda.getDados() if hasattr(nota_perda, 'getDados') else {}
        id_nota_perda = nota_perda_dados.get("id", "?")

        return JsonResponse({
            'sucesso': True,
            'mensagem': f'Perda pós-venda registrada. Nota de Perda #{id_nota_perda} criada referenciando devolução #{id_nota_dev}.',
            'id_nota_devolucao': id_nota_dev,
            'id_nota_perda': id_nota_perda,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar perda pós-venda: {e}'})


@require_http_methods(["GET"])
def api_listar_vendas(request):
    """Retorna lista de Notas de Venda (tipo 2) para seleção no PDV."""
    try:
        notas = helpers.get_notas_venda()
        return JsonResponse({'sucesso': True, 'notas': notas})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': str(e)})


@require_http_methods(["GET"])
def api_listar_devolucoes(request):
    """Retorna lista de Notas de Devolução (tipo 3) para seleção no PDV."""
    try:
        notas = helpers.get_notas_devolucao()
        return JsonResponse({'sucesso': True, 'notas': notas})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': str(e)})


@require_http_methods(["GET"])
def api_itens_nota(request):
    """Retorna os itens de uma nota específica dado ?id=<id_nota>."""
    id_nota = request.GET.get('id')
    if not id_nota:
        return JsonResponse({'sucesso': False, 'mensagem': "'id' é obrigatório."})
    try:
        itens = helpers.get_itens_nota(int(id_nota))
        return JsonResponse({'sucesso': True, 'itens': itens})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': str(e)})

