from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

def produtos_view(request):
    conn = BancoDB.obter_conexao()
    cursor = conn.cursor()
    
    # Busca Unidades de Medida
    cursor.execute('SELECT * FROM unidadeMedida')
    unidades = [dict(row) for row in cursor.fetchall()]
    
    # Busca Fornecedores
    cursor.execute('SELECT * FROM vw_entidade_completa WHERE fornecedor = 1')
    fornecedores = [dict(row) for row in cursor.fetchall()]
    
    # Busca Catálogo de Produtos
    cursor.execute('''
        SELECT p.*, u.descricao as UnidadeMedida,
        (SELECT SUM(quantidade) FROM fluxoEstoque WHERE id_produto = p.id) as estoque
        FROM produto p
        LEFT JOIN unidadeMedida u ON p.unidadeMedida = u.id
    ''')
    catalogo = []
    for row in cursor.fetchall():
        d = dict(row)
        d['estoque'] = d['estoque'] if d['estoque'] else 0
        catalogo.append(d)
        
    return render(request, 'produtos.html', {
        'unidades': unidades,
        'fornecedores': fornecedores,
        'catalogo': catalogo
    })

@csrf_exempt
def api_cadastrar_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome = data.get('nome')
            dias_duraveis = data.get('diasDuraveis', 365)
            id_unidade = data.get('id_unidade', 1)
            is_conjunto = data.get('is_conjunto', False)
            fator = data.get('fator_conjunto', 1) if is_conjunto else None
            
            # TODO: Here we can expand to insert with Business Rules via an API class
            # For now, using direct BancoDB if no Manager exists for Product Creation
            conn = BancoDB.obter_conexao()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO produto (nome, diasDuraveis, unidadeMedida)
                VALUES (?, ?, ?)
            ''', (nome, dias_duraveis, id_unidade))
            prod_id = cursor.lastrowid
            conn.commit()
            
            return JsonResponse({'sucesso': True, 'id_produto': prod_id})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})

@csrf_exempt
def api_editar_produto(request):
    # Implementação futura se necessário
    return JsonResponse({'sucesso': True})
