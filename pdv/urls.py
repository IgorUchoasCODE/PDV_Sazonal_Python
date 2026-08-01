from django.urls import path
from . import views_produtos, views_estoque, views_gerais
from core import views as core_views

urlpatterns = [
    # Rotas gerais
    path('', views_gerais.dashboard_view, name='dashboard'),
    path('cadastro/', views_gerais.entidades_view, name='entidades'),
    path('fornecedores/', views_gerais.fornecedores_view, name='fornecedores'),
    path('clientes/', views_gerais.clientes_view, name='clientes'),
    path('relatorios/', views_gerais.relatorios_view, name='relatorios'),
    path('configuracoes/', views_gerais.configuracoes_view, name='configuracoes'),
    path('logout/', views_gerais.logout_view, name='logout'),
    path('pdv/', views_gerais.pdv_view, name='pdv'),
    path('financeiro/', views_gerais.financeiro_view, name='financeiro'),
    path('api/detalhes-pagamento/<int:id>/', views_gerais.api_detalhes_pagamento, name='api_detalhes_pagamento'),
    
    # Produtos
    path('produtos/', views_produtos.produtos_view, name='produtos'),
    path('api/cadastrar-produto/', views_produtos.api_cadastrar_produto, name='api_cadastrar_produto'),
    path('api/editar-produto/', views_produtos.api_editar_produto, name='api_editar_produto'),
    path('api/apagar-produto/', views_produtos.api_apagar_produto, name='api_apagar_produto'),
    
    # Estoque
    path('estoque/', views_estoque.estoque_view, name='estoque'),
    path('api/comprar/', views_estoque.api_comprar, name='api_comprar'),
    path('api/venda-fim-turno/', views_estoque.api_venda_fim_turno, name='api_venda_fim_turno'),
    path('api/nota/<int:nota_id>/', views_estoque.api_detalhes_nota, name='api_detalhes_nota'),
    path('api/nota/<int:nota_id>/editar/', views_estoque.api_editar_nota, name='api_editar_nota'),
    path('api/vendas-hoje/', views_estoque.api_vendas_hoje, name='api_vendas_hoje'),
    
    # APIs from core
    path('api/buscar-produtos/', core_views.api_buscar_produtos, name='api_buscar_produtos'),
    path('api/cadastrar-entidade/', core_views.api_cadastrar_entidade, name='api_cadastrar_entidade'),
    path('api/apagar-entidade/', core_views.api_apagar_entidade, name='api_apagar_entidade'),
    path('api/editar-entidade/', core_views.api_editar_entidade, name='api_editar_entidade'),
    path('api/compensar/', core_views.api_compensar, name='api_compensar'),
    path('api/registrar-pagamento/', core_views.api_registrar_pagamento, name='api_registrar_pagamento'),
    path('api/registrar-pagamento-entidade/', core_views.api_registrar_pagamento_entidade, name='api_registrar_pagamento_entidade'),
    path('api/pagamento-lote/', core_views.api_pagamento_lote, name='api_pagamento_lote'),
    path('api/extrato-entidade/<int:id_entidade>/', core_views.api_extrato_entidade, name='api_extrato_entidade'),

    # Vendas, Perdas e Devoluções
    path('api/vender/', core_views.api_vender, name='api_vender'),
    path('api/perder/', core_views.api_perder, name='api_perder'),
    path('api/devolver/', core_views.api_devolver, name='api_devolver'),
    path('api/atualizar-preco-produto/', core_views.api_atualizar_preco_produto, name='api_atualizar_preco_produto'),

    # PDV — Listagem de Notas e Perda Pós-Venda
    path('api/listar-vendas/', core_views.api_listar_vendas, name='api_listar_vendas'),
    path('api/listar-devolucoes/', core_views.api_listar_devolucoes, name='api_listar_devolucoes'),
    path('api/itens-nota/', core_views.api_itens_nota, name='api_itens_nota'),
    path('api/perder-pos-venda/', core_views.api_perder_pos_venda, name='api_perder_pos_venda'),
]
