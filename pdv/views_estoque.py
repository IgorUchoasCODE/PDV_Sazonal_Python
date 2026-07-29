from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.inventoryManager import InventoryManager
from br.com.pdv.src.memory.paymentManager import PaymentManager

def estoque_view(request):
    # Força a carga do inventário para refletir o estado atual
    InventoryManager.carregarTudo()
    
    # Prepara Lotes FIFO usando o helper para pegar a validade
    from core.helpers import get_lotes_fifo
    lotes_fifo = get_lotes_fifo()
    
    # Prepara Árvore de Notas (rastreabilidade FIFO)
    arvore_notas = []
    
    # Agrupar lote (compra) -> vendas que consumiram dele
    conn = BancoDB.obter_conexao()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    for lote in lotes_fifo:
        idx_lote = lote['idx_lote']
        # Buscar vendas que utilizaram este lote especificamente
        # No SQLite do InventoryManager o mapa relacional fica na tabela rel_lote_venda
        # Mas para simplificar se não houver rel_lote_venda, faremos uma simulação ou busca simples se houver
        vendas = []
        try:
            cursor.execute('''
                SELECT id_venda as id_nota_venda, data as data_venda, quantidade as qtd_abatida
                FROM rel_lote_venda r
                JOIN fluxoEstoque f ON f.id_fluxo_nota = r.id_venda
                WHERE r.idx_lote = ?
            ''', (idx_lote,))
            for r in cursor.fetchall():
                vendas.append(dict(r))
        except Exception:
            # Caso a tabela não exista ainda (não foi criada no InventoryManager)
            pass
            
        cursor.execute("SELECT nome FROM produto WHERE id = ?", (lote['id_produto'],))
        prod_row = cursor.fetchone()
        prod_nome = prod_row['nome'] if prod_row else "Produto Desconhecido"

        arvore_notas.append({
            'idx_lote': idx_lote,
            'id_nota': lote['id_nota'],
            'id_produto': lote['id_produto'],
            'produto_nome': prod_nome,
            'qtd_inicial': lote['qtd_inicial'],
            'qtd_disponivel': lote['qtd_disponivel'],
            'data_compra': lote['data_entrada'],
            'is_ativo': not lote.get('is_vencido', False) and float(lote['qtd_disponivel']) > 0,
            'vendas': vendas
        })
    
    # Produtos Simples e Compostos
    cursor.execute('''
        SELECT p.*, u.descricao as UnidadeMedida,
        (SELECT SUM(quantidade) FROM fluxoEstoque WHERE id_produto = p.id) as estoque
        FROM produto p
        LEFT JOIN unidadeMedida u ON p.unidadeMedida = u.id
    ''')
    produtos_db = cursor.fetchall()
    
    simples = []
    compostos = []
    catalogo = []
    
    for row in produtos_db:
        d = dict(row)
        d['estoque'] = d['estoque'] if d['estoque'] else 0
        catalogo.append(d)
        if d['receita']:
            compostos.append(d)
        else:
            simples.append(d)
            
    valor_total_estoque = sum(float(l['qtd_disponivel']) * float(l['custo_unitario']) for l in lotes_fifo if l['qtd_disponivel'])
            
    return render(request, 'estoque.html', {
        'lotes_fifo': lotes_fifo,
        'arvore_notas': arvore_notas,
        'simples': simples,
        'compostos': compostos,
        'catalogo': catalogo,
        'total_simples': len(simples),
        'total_compostos': len(compostos),
        'valor_total_estoque': valor_total_estoque
    })

@csrf_exempt
def api_comprar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Aciona a factory / manager
            nota = InventoryManager.insert_compra(data)
            if nota:
                return JsonResponse({'sucesso': True, 'mensagem': 'Compra inserida e lotes criados com sucesso!'})
            else:
                return JsonResponse({'sucesso': False, 'mensagem': 'Falha interna ao gerar nota.'})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})

@csrf_exempt
def api_venda_fim_turno(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Aciona a factory / manager
            nota = InventoryManager.insert_venda(data)
            if nota:
                return JsonResponse({'sucesso': True, 'mensagem': 'Venda registrada! Lotes FIFO abatidos com sucesso!'})
            else:
                return JsonResponse({'sucesso': False, 'mensagem': 'Estoque insuficiente ou falha ao gerar nota.'})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})
