from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

def produtos_view(request):
    conn = BancoDB.obter_conexao()
    cursor = conn.cursor()
    
    # Busca Unidades de Medida (apenas unidades base e sem ser proporções dinâmicas repetidas)
    cursor.execute("SELECT * FROM unidadeMedida WHERE fatorConjunto IS NULL OR fatorConjunto = 1")
    unidades = [dict(row) for row in cursor.fetchall()]
    
    # Busca Fornecedores
    cursor.execute('SELECT * FROM vw_entidade_completa WHERE fornecedor = 1')
    fornecedores = [dict(row) for row in cursor.fetchall()]
    
    # Busca Catálogo de Produtos
    cursor.execute('''
        SELECT p.*, u.descricao as desc_unidade,
        COALESCE((SELECT SUM(CASE WHEN id_tipoNota IN (1, 3, 5) THEN quantidade ELSE -quantidade END) FROM fluxoEstoque WHERE id_produto = p.id), 0) as estoque
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
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
            
            import random
            temp_id = random.randint(1000000, 9999999) # ID temporário para validação

            # Prepare instructions based on what the factory expects
            instrucoes = {
                "id": temp_id,
                "nome": data.get('nome'),
                "diasDuraveis": data.get('diasDuraveis', 30),
                "unidadeMedida": data.get('id_unidade', 1)
            }
            if data.get('receita'):
                # json keys are always strings, but Produto expects integer IDs
                instrucoes['receita'] = {int(k): v for k, v in data.get('receita').items()}
            elif data.get('is_conjunto'):
                instrucoes['fatorConjunto'] = data.get('fator_conjunto', 1)
                
            produto = ProductClassFactory.fabricar(instrucoes)
            prod_id = ProductClassFactory.salvar(produto)
            
            if prod_id > 0:
                return JsonResponse({'sucesso': True, 'id_produto': prod_id})
            else:
                return JsonResponse({'sucesso': False, 'mensagem': 'Erro ao salvar no banco de dados.'})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})

@csrf_exempt
def api_editar_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prod_id = data.get('id')
            if not prod_id:
                return JsonResponse({'sucesso': False, 'mensagem': 'ID do produto não informado.'})
                
            from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
            
            instrucoes = {
                "nome": data.get('nome'),
                "diasDuraveis": data.get('diasDuraveis')
            }
            
            produto = ProductClassFactory.alterar(prod_id, instrucoes)
            if produto:
                return JsonResponse({'sucesso': True})
            else:
                return JsonResponse({'sucesso': False, 'mensagem': 'Erro ao alterar o produto (verifique restrições).'})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})

@csrf_exempt
def api_apagar_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prod_id = data.get('id')
            if not prod_id:
                return JsonResponse({'sucesso': False, 'mensagem': 'ID do produto não informado.'})
                
            from br.com.pdv.src.BDD.bancodb import BancoDB
            
            # Verificação estrita de vínculos
            with BancoDB.obter_conexao() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as total FROM fluxoEstoque WHERE id_produto = ?", (prod_id,))
                row = cur.fetchone()
                total_em_notas = dict(row).get("total", 0) if row else 0
                
                if total_em_notas > 0:
                    return JsonResponse({'sucesso': False, 'mensagem': f'Produto não pode ser apagado pois possui {total_em_notas} registros em notas contábeis.'})
                    
                # Deleta a receita se for composto
                cur.execute("DELETE FROM receita WHERE id_produto = ?", (prod_id,))
                # Deleta o produto
                cur.execute("DELETE FROM produto WHERE id = ?", (prod_id,))
                conn.commit()
                
            return JsonResponse({'sucesso': True})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})
