from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.inventoryManager import InventoryManager
from br.com.pdv.src.memory.paymentManager import PaymentManager
from br.com.pdv.src.memory.productClassFactory import productClassFactory
from br.com.pdv.src.financeiro.Real import MoedaReal

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
        
        # Buscar vinculadas (Venda=2, Devolução=3, Perda=4) que consumiram desse lote
        cursor.execute('''
            SELECT id_fluxo_nota as id_nota_venda, data as data_venda, quantidade as qtd_abatida, id_tipoNota
            FROM fluxoEstoque
            WHERE id_notaOrigem = ? AND id_produto = ? AND id_tipoNota IN (2, 3, 4)
        ''', (lote['id_nota'], lote['id_produto']))
        vendas = []
        for v in cursor.fetchall():
            vd = dict(v)
            if hasattr(vd['data_venda'], 'strftime'):
                vd['data_venda'] = vd['data_venda'].strftime('%d/%m/%Y')
            elif isinstance(vd['data_venda'], str) and '-' in vd['data_venda']:
                p = vd['data_venda'].split(' ')[0].split('-')
                if len(p) >= 3:
                    vd['data_venda'] = f"{p[2]}/{p[1]}/{p[0]}"
            vendas.append(vd)
            
        cursor.execute("SELECT nome FROM produto WHERE id = ?", (lote['id_produto'],))
        prod_row = cursor.fetchone()
        prod_nome = prod_row['nome'] if prod_row else "Produto Desconhecido"

        # Buscar Fornecedor
        cursor.execute('''
            SELECT COALESCE(emp.nome, pes.nome, 'Não Informado') as fornecedor
            FROM fluxosNotasEstoque fne
            LEFT JOIN entidades ent ON fne.id_representante = ent.id
            LEFT JOIN empresas emp ON ent.id_empresa = emp.id
            LEFT JOIN pessoas pes ON ent.id_pessoa = pes.id
            WHERE fne.id = ?
        ''', (lote['id_nota'],))
        forn_row = cursor.fetchone()
        fornecedor = forn_row['fornecedor'] if forn_row else 'Não Informado'

        # Formatar Data Entrada (YYYY-MM-DD para DD/MM/YYYY)
        dt_entrada = lote['data_entrada']
        if hasattr(dt_entrada, 'strftime'):
            dt_entrada = dt_entrada.strftime('%d/%m/%Y')
        elif isinstance(dt_entrada, str) and '-' in dt_entrada:
            partes = dt_entrada.split(' ')[0].split('-') # em caso de conter hora
            if len(partes) >= 3:
                dt_entrada = f"{partes[2]}/{partes[1]}/{partes[0]}"
        
        # Calcular total já vendido
        total_vendido = sum(float(v.get('qtd_abatida', 0)) for v in vendas)

        lote_dict = {
            'idx_lote': idx_lote,
            'id_nota': lote['id_nota'],
            'id_produto': lote['id_produto'],
            'produto_nome': prod_nome,
            'fornecedor': fornecedor,
            'qtd_inicial': lote['qtd_inicial'],
            'qtd_disponivel': lote['qtd_disponivel'],
            'qtd_vendida': total_vendido,
            'custo_unitario': lote.get('custo_unitario', 0),
            'valor_total': float(lote['qtd_disponivel']) * float(lote.get('custo_unitario', 0)),
            'data_compra_fmt': dt_entrada,
            'data_registro': dt_entrada, # Mesmo que entrada
            'is_ativo': not lote.get('is_vencido', False) and float(lote['qtd_disponivel']) > 0,
            'vendas': vendas
        }
        lote_dict['json_data'] = json.dumps(lote_dict)
        arvore_notas.append(lote_dict)
    
    # Produtos Simples e Compostos
    cursor.execute('''
        SELECT p.*, u.descricao as desc_unidade,
        COALESCE((SELECT SUM(CASE WHEN id_tipoNota IN (1, 3, 5) THEN quantidade ELSE -quantidade END) FROM fluxoEstoque WHERE id_produto = p.id), 0) as estoque
        FROM produto p
        LEFT JOIN unidadeMedida u ON p.unidadeMedida = u.id
    ''')
    produtos_db = cursor.fetchall()
    
    simples = []
    compostos = []
    catalogo = []

    # Carregar receitas da tabela receita (já que d['receita'] é apenas um booleano na tabela produto)
    cursor.execute('SELECT id_produto, id_ingrediente, qntdd FROM receita')
    receitas_map = {}
    for r_row in cursor.fetchall():
        pid = str(r_row['id_produto'])
        if pid not in receitas_map:
            receitas_map[pid] = {}
        receitas_map[pid][str(r_row['id_ingrediente'])] = float(r_row['qntdd'])

    # Calcular preco medio de venda e carregar custo medio
    cursor.execute('''
        SELECT id_produto, AVG(valorUnidario) as preco_medio 
        FROM fluxoEstoque 
        WHERE id_tipoNota = 2 AND valorUnidario > 0
        GROUP BY id_produto
    ''')
    preco_medio_map = {row['id_produto']: row['preco_medio'] for row in cursor.fetchall()}

    estoque_map = {}
    for row in produtos_db:
        estoque_map[row['id']] = float(row['estoque']) if row['estoque'] else 0.0

    for row in produtos_db:
        d = dict(row)
        # Usa o estoque real calculado no banco (já subtraindo as saídas)
        d['estoque'] = float(d['estoque']) if d['estoque'] else 0.0
        d['estoque_fmt'] = round(d['estoque'], 2)
        
        varejo = float(d.get('varejo') or 0)
        
        # preco_medio is ALREADY in Reais from db
        preco_medio_real = preco_medio_map.get(d['id'], 0.0)
        d['valor_venda_calculado'] = varejo if varejo > 0 else preco_medio_real
        d['valor_venda_fmt'] = round(d['valor_venda_calculado'], 2)
        
        # Calcular custo_medio dos lotes ativos via mapaEstoque
        total_custo = 0.0
        total_qtd = 0.0
        id_str = str(d['id'])
        if id_str in InventoryManager._mapaProdutos:
            lotes_ativos = InventoryManager._mapaProdutos[id_str].get("lotes", [])
            for idx_lote in lotes_ativos:
                lote = InventoryManager._mapaEstoque.get(idx_lote)
                # Somar apenas os lotes de compra (tipo 1) e saldo restante (Reposições tbm ajudam se necessário, mas 1 é COMPRA)
                if lote and lote.get("id_tipo") in (1, 5) and lote.get("qtd_disponivel", 0) > 0:
                    total_custo += lote["custo_unitario"] * lote["qtd_disponivel"]
                    total_qtd += lote["qtd_disponivel"]
        
        if total_qtd > 0:
            d['custo_medio'] = total_custo / total_qtd
        else:
            d['custo_medio'] = InventoryManager._get_custo_medio(id_str)

        d['durabilidade'] = d.get('diasDuraveis') or 0
        
        # Obter o dicionário de receita real a partir do mapa carregado
        d['receita_dict'] = receitas_map.get(str(d['id']), {})
        
        # Boolean explicito se é composto ou simples
        d['is_composto'] = bool(d['receita'])

        if d['is_composto']:
            max_produzir = float('inf')
            detalhes_receita = []
            for ing_id, ing_qtd in d['receita_dict'].items():
                ing_estoque = estoque_map.get(int(ing_id), 0.0)
                ing_qtd = float(ing_qtd)
                if ing_qtd > 0:
                    produz = ing_estoque / ing_qtd
                    if produz < max_produzir:
                        max_produzir = produz
                # Busca nome do ingrediente
                ing_nome = next((p['nome'] for p in produtos_db if str(p['id']) == str(ing_id)), f"Insumo {ing_id}")
                detalhes_receita.append({'nome': ing_nome, 'qtd': ing_qtd, 'estoque': ing_estoque})
            
            d['max_produzir'] = 0 if max_produzir == float('inf') else round(max_produzir, 2)
            d['detalhes_receita'] = detalhes_receita
            compostos.append(d)
        else:
            simples.append(d)
            catalogo.append(d)

    # Ordenar catalogo: alfabeticamente
    catalogo.sort(key=lambda x: x['nome'])

    valor_total_estoque = sum(float(l['qtd_disponivel']) * float(l['custo_unitario']) for l in lotes_fifo if l['qtd_disponivel'])
            
    from br.com.pdv.src.apis.gerenciadorSazonal import GerenciadorSazonal
    sazonal = GerenciadorSazonal.obter_indicadores_sazonais()

    return render(request, 'estoque.html', {
        'lotes_fifo': lotes_fifo,
        'arvore_notas': arvore_notas,
        'simples': simples,
        'compostos': compostos,
        'catalogo': catalogo,
        'total_simples': len(simples),
        'total_compostos': len(compostos),
        'valor_total_estoque': valor_total_estoque,
        'sazonal': sazonal
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

def api_vendas_hoje(request):
    """Retorna as vendas do dia para a coluna Hoje no modal de fechamento."""
    from datetime import date
    data_str = request.GET.get('data', str(date.today()))
    try:
        conn = BancoDB.obter_conexao()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fe.id_produto,
                   SUM(fe.quantidade) as qtd_total,
                   SUM(fe.quantidade * fe.valorUnidario) as valor_total
            FROM fluxoEstoque fe
            JOIN fluxosNotasEstoque fn ON fe.id_nota = fn.id
            WHERE fe.id_tipoNota = 2
              AND date(fn.dataRegistro) = ?
            GROUP BY fe.id_produto
        ''', (data_str,))
        vendas = [{'id_produto': r['id_produto'],
                   'qtd_total': float(r['qtd_total'] or 0),
                   'valor_total': float(r['valor_total'] or 0)} for r in cursor.fetchall()]
        return JsonResponse({'vendas': vendas})
    except Exception as e:
        return JsonResponse({'vendas': [], 'erro': str(e)})

@csrf_exempt
def api_editar_nota(request, nota_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            itens = data.get('itens', [])
            
            if not itens:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum item para editar.'})

            conn = BancoDB.obter_conexao()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Descobrir o tipo da nota
            cursor.execute('SELECT id_tipoNota FROM fluxosNotasEstoque WHERE id = ?', (nota_id,))
            nota = cursor.fetchone()
            if not nota:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nota não encontrada no sistema.'})

            tipo_nota = nota['id_tipoNota']

            # Se for Compra (1) ou Compensação/Ajuste de Entrada (5), verificar vínculos (saídas associadas)
            if tipo_nota in [1, 5]:
                cursor.execute('SELECT COUNT(id) as total FROM fluxoEstoque WHERE id_notaOrigem = ?', (nota_id,))
                vinculos = cursor.fetchone()
                if vinculos and vinculos['total'] > 0:
                    return JsonResponse({'sucesso': False, 'mensagem': 'Não é possível editar nota de entrada pois já existem baixas vinculadas a este lote.'})

            # Atualizar fluxoEstoque
            for item in itens:
                id_produto = item.get('id_produto')
                quantidade = item.get('quantidade')
                valor_unidario = item.get('valorUnidario')
                
                # Para atualizar o lucro, precisaríamos da lógica FIFO. Como carregarTudo() refaz a árvore,
                # o campo lucroTotal será recalculado e atualizado no banco durante o mapearProdutos() 
                # (Se mapearProdutos salvar no BD, caso contrário ele fica apenas em memória, o que é o padrão do sistema).
                
                cursor.execute('''
                    UPDATE fluxoEstoque 
                    SET quantidade = ?, valorUnidario = ?
                    WHERE id_fluxo_nota = ? AND id_produto = ?
                ''', (quantidade, valor_unidario, nota_id, id_produto))
            
            conn.commit()

            # Recarregar o motor em memória destruindo e reconstruindo o cache FIFO
            InventoryManager._NotasCompras.clear()
            InventoryManager._NotasVendas.clear()
            InventoryManager._NotasDevolucoes.clear()
            InventoryManager._NotasPerdas.clear()
            InventoryManager._NotasCompensacao.clear()
            InventoryManager._mapaProdutos.clear()
            InventoryManager._mapaEstoque.clear()
            InventoryManager._contadorLote = 0
            InventoryManager.carregarTudo()

            return JsonResponse({'sucesso': True, 'mensagem': 'Nota editada e recalculo do FIFO efetuado com sucesso!'})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Falha ao editar nota: {str(e)}'})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})

def api_detalhes_nota(request, nota_id):
    conn = BancoDB.obter_conexao()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Busca cabeçalho da nota
    cursor.execute('''
        SELECT fne.id, fne.id_tipoNota, fne.data_vencimento,
               COALESCE(emp.nome, pes.nome, 'Não Informado') as entidade_nome
        FROM fluxosNotasEstoque fne
        LEFT JOIN entidades ent ON fne.id_representante = ent.id
        LEFT JOIN empresas emp ON ent.id_empresa = emp.id
        LEFT JOIN pessoas pes ON ent.id_pessoa = pes.id
        WHERE fne.id = ?
    ''', (nota_id,))
    nota = cursor.fetchone()
    if not nota:
        return JsonResponse({"error": "Nota não encontrada"}, status=404)
        
    nota_dict = dict(nota)
    
    data_formatada = 'N/A'
    dt = nota_dict.get("data_vencimento")
    if hasattr(dt, 'strftime'):
        data_formatada = dt.strftime('%d/%m/%Y')
    elif isinstance(dt, str):
        if '-' in dt:
            p = dt.split(' ')[0].split('-')
            if len(p) >= 3:
                data_formatada = f"{p[2]}/{p[1]}/{p[0]}"
        else:
            data_formatada = dt
            
    # Mapear o tipo da nota
    tipos = {1: "Compra", 2: "Venda", 3: "Devolução", 4: "Perda", 5: "Ajuste", 6: "Produção"}
    tipo_str = tipos.get(nota_dict.get("id_tipoNota"), "Desconhecido")
    
    # Busca os itens vendidos nesta nota
    cursor.execute('''
        SELECT f.id_produto, p.nome as produto_nome, f.quantidade, f.valorUnidario, f.lucroTotal
        FROM fluxoEstoque f
        JOIN produto p ON f.id_produto = p.id
        WHERE f.id_fluxo_nota = ?
    ''', (nota_id,))
    itens = [dict(row) for row in cursor.fetchall()]
    
    return JsonResponse({
        "id": nota_dict["id"],
        "tipo": tipo_str,
        "data": data_formatada,
        "cliente": nota_dict["entidade_nome"],
        "itens": itens
    })
@csrf_exempt
def api_venda_fim_turno(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            baixas = data.get('baixas', [])
            
            if not baixas:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum dado enviado.'})

            vendas = []
            perdas = []

            for b in baixas:
                if b['tipo'] == 'venda':
                    vendas.append({
                        "id": b['id_produto'],
                        "quantidade": b['quantidade'],
                        "valorVenda": b['valorVenda']
                    })
                elif b['tipo'] == 'perda':
                    perdas.append({
                        "id": b['id_produto'],
                        "quantidade": b['quantidade']
                    })

            mensagens = []
            sucesso_geral = True

            # Processa as Vendas
            if vendas:
                # Usa entidade 1 (Cliente Padrão) conforme solicitado
                dados_venda = {
                    "id_cliente": 1,
                    "data": data.get('data'),
                    "produtos": vendas
                }
                nota_venda = InventoryManager.insert_venda(dados_venda)
                if nota_venda:
                    id_venda = nota_venda.getDados().get("id")
                    mensagens.append(f"Vendas registradas (ID #{id_venda}).")
                    
                    # Vamos retornar o ID da venda e o valor total no JSON de sucesso
                    # para que o frontend consiga processar o pagamento múltiplo.
                    valor_venda = nota_venda.getDados().get("valorTotalVenda")
                    
                else:
                    sucesso_geral = False
                    mensagens.append("Falha ao registrar Vendas (Verifique o estoque).")

            # Processa as Perdas
            if perdas:
                # Perda Geral (sem id_nota_origem) consumindo do FIFO
                dados_perda = {
                    "origem": "ESTOQUE",
                    "data": data.get('data'),
                    "produtos": perdas
                }
                nota_perda = InventoryManager.insert_perda(dados_perda)
                if nota_perda:
                    id_perda = nota_perda.getDados().get("id")
                    mensagens.append(f"Perdas registradas (ID #{id_perda}).")
                else:
                    sucesso_geral = False
                    mensagens.append("Falha ao registrar Perdas (Verifique o estoque).")

            if sucesso_geral:
                # Adicionando id_venda e valor_total na resposta para suportar fluxo de pagamento
                resp = {'sucesso': True, 'mensagem': ' '.join(mensagens)}
                if 'id_venda' in locals():
                    resp['id_venda'] = id_venda
                    resp['valor_venda'] = valor_venda
                return JsonResponse(resp)
            else:
                return JsonResponse({'sucesso': False, 'mensagem': ' '.join(mensagens)})
                
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)})
    return JsonResponse({'sucesso': False, 'mensagem': 'Invalid Method'})
