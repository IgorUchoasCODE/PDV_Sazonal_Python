from django.urls import path
from . import views_produtos, views_estoque, views_gerais

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
    
    # Produtos
    path('produtos/', views_produtos.produtos_view, name='produtos'),
    path('api/cadastrar-produto/', views_produtos.api_cadastrar_produto, name='api_cadastrar_produto'),
    path('api/editar-produto/', views_produtos.api_editar_produto, name='api_editar_produto'),
    
    # Estoque
    path('estoque/', views_estoque.estoque_view, name='estoque'),
    path('api/comprar/', views_estoque.api_comprar, name='api_comprar'),
    path('api/venda-fim-turno/', views_estoque.api_venda_fim_turno, name='api_venda_fim_turno'),
]
