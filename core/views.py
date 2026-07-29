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
@login_required
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


@login_required
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_vender(request):
    dados = _corpo_json(request)
    try:
        from br.com.pdv.src.memory.inventoryManager import InventoryManager
        nota = InventoryManager.insert_venda(dados)
        if nota is None:
            return JsonResponse({'sucesso': False, 'mensagem': 'Não foi possível registrar a venda. Confira cliente, produtos e estoque disponível.'})
        return JsonResponse({'sucesso': True, 'mensagem': 'Venda registrada com sucesso.'})
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao registrar venda: {e}'})


@login_required
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


@login_required
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


@login_required
@require_http_methods(["GET"])
def api_buscar_produtos(request):
    termo = request.GET.get('q', '').strip().lower()
    catalogo = helpers.get_produtos_catalogo()
    if termo:
        catalogo = [p for p in catalogo if termo in p['nome'].lower()]
    return JsonResponse({'sucesso': True, 'produtos': catalogo})
