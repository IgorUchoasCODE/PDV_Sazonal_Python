from django.urls import path

from core import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.dashboard, name='dashboard'),
    path('produtos/', views.produtos, name='produtos'),
    path('estoque/', views.estoque, name='estoque'),
    path('fornecedores/', views.fornecedores, name='fornecedores'),
    path('clientes/', views.clientes, name='clientes'),
    path('cadastro/', views.entidades, name='entidades'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('pdv/', views.pdv, name='pdv'),
    path('financeiro/', views.financeiro, name='financeiro'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),

    path('api/resumo-sazonal/<int:produto_id>/', views.api_resumo_sazonal, name='api_resumo_sazonal'),
    path('api/cadastrar-produto/', views.api_cadastrar_produto, name='api_cadastrar_produto'),
    path('api/comprar/', views.api_comprar, name='api_comprar'),
    path('api/vender/', views.api_vender, name='api_vender'),
    path('api/cadastrar-entidade/', views.api_cadastrar_entidade, name='api_cadastrar_entidade'),
    path('api/registrar-pagamento/', views.api_registrar_pagamento, name='api_registrar_pagamento'),
    path('api/buscar-produtos/', views.api_buscar_produtos, name='api_buscar_produtos'),
]
