from django.shortcuts import render
from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.inventoryManager import InventoryManager
import json

def dashboard_view(request):
    conn = BancoDB.obter_conexao()
    cursor = conn.cursor()
    
    # Busca dados para os cards
    cursor.execute('SELECT COUNT(*) as total FROM pessoas')
    total_clientes = dict(cursor.fetchone())['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM produto')
    total_produtos = dict(cursor.fetchone())['total']
    
    cursor.execute('''
        SELECT SUM(ABS(quantidade) * valorUnidario) as faturamento, SUM(lucroTotal) as lucro
        FROM fluxoEstoque WHERE id_tipoNota = 2
    ''')
    resumo_financeiro = dict(cursor.fetchone())
    faturamento_total = resumo_financeiro['faturamento'] or 0
    lucro_total = resumo_financeiro['lucro'] or 0
    
    cursor.execute('''
        SELECT 
            DATE(f.data) as dia,
            STRFTIME('%Y-%m', f.data) as mes_ano,
            SUM(CASE WHEN f.id_tipoNota = 2 THEN ABS(f.quantidade) * f.valorUnidario ELSE 0 END) as valor_venda,
            SUM(CASE WHEN f.id_tipoNota = 2 THEN f.lucroTotal ELSE 0 END) as lucro_venda,
            SUM(CASE WHEN f.id_tipoNota = 4 THEN ABS(f.quantidade) * f.valorUnidario ELSE 0 END) as valor_perda,
            MAX(s.nivel_rio_atual) as nivel_rio,
            MAX(s.temperatura_atual) as temperatura,
            COALESCE(MAX(s.indicador_clima), 'AMENO') as clima,
            COALESCE(MAX(s.indicador_rio), 'NORMAL') as indicador_rio,
            COALESCE(MAX(s.indicador_chuva), 'MODERADO') as indicador_chuva
        FROM fluxoEstoque f
        LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
        GROUP BY DATE(f.data)
        ORDER BY DATE(f.data) ASC
    ''')
    dados_grafico = []
    meses_totais = {}
    
    NOMES_MESES = {
        '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
        '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
        '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
    }

    for row in cursor.fetchall():
        m_ano = row['mes_ano']
        v_venda = row['valor_venda'] or 0
        v_perda = row['valor_perda'] or 0
        
        dados_grafico.append({
            'dia': row['dia'],
            'mes_ano': m_ano,
            'valor_venda': v_venda,
            'lucro_venda': row['lucro_venda'] or 0,
            'valor_perda': v_perda,
            'nivel_rio': row['nivel_rio'] or 0,
            'temperatura': row['temperatura'] or 0,
            'clima': row['clima'] or 'AMENO',
            'indicador_rio': row['indicador_rio'] or 'NORMAL',
            'indicador_chuva': row['indicador_chuva'] or 'MODERADO'
        })

        if m_ano:
            if m_ano not in meses_totais:
                meses_totais[m_ano] = {'vendas': 0.0, 'perdas': 0.0}
            meses_totais[m_ano]['vendas'] += v_venda
            meses_totais[m_ano]['perdas'] += v_perda

    # Identifica atalhos estatísticos
    mes_pico_faturamento = max(meses_totais, key=lambda k: meses_totais[k]['vendas']) if meses_totais else ''
    mes_baixa_faturamento = min(meses_totais, key=lambda k: meses_totais[k]['vendas']) if meses_totais else ''
    mes_maior_perda = max(meses_totais, key=lambda k: meses_totais[k]['perdas']) if meses_totais else ''

    meses_disponiveis = []
    for m in sorted(meses_totais.keys()):
        partes = m.split('-')
        if len(partes) == 2:
            ano, mes = partes
            nome_mes = NOMES_MESES.get(mes, mes)
            meses_disponiveis.append({
                'codigo': m,
                'nome': f"{nome_mes} {ano}"
            })
        
    # Tendências Sazonais
    try:
        InventoryManager.carregarTudo()
        tendencias = InventoryManager.analisar_tendencias_sazonais()
    except Exception:
        tendencias = {}


    # Análise de Indicativos Sazonais por Produto (Simples e Compostos)
    cursor.execute('''
        SELECT 
            p.id,
            p.nome,
            COALESCE(SUM(CASE WHEN fe.id_tipoNota IN (1, 3, 5) THEN fe.quantidade ELSE -fe.quantidade END), 0) as estoque_caixas,
            COALESCE(SUM(CASE WHEN fe.id_tipoNota = 2 THEN ABS(fe.quantidade) ELSE 0 END), 0) as qtd_vendida,
            (
                SELECT s.indicador_clima 
                FROM snapshot_sazonal s 
                JOIN fluxosNotasEstoque fn ON s.id_fluxo_nota = fn.id 
                JOIN fluxoEstoque fe2 ON fe2.id_fluxo_nota = fn.id 
                WHERE fe2.id_produto = p.id AND fn.id_tipoNota = 2
                GROUP BY s.indicador_clima 
                ORDER BY SUM(ABS(fe2.quantidade)) DESC 
                LIMIT 1
            ) as clima_pico
        FROM produto p
        LEFT JOIN fluxoEstoque fe ON fe.id_produto = p.id
        GROUP BY p.id, p.nome
    ''')
    
    produtos_raw = [dict(r) for r in cursor.fetchall()]
    produtos_map = {}
    for item in produtos_raw:
        produtos_map[item['id']] = {
            'id': item['id'],
            'nome': item['nome'],
            'estoque_caixas': item['estoque_caixas'] or 0.0,
            'qtd_vendida': item['qtd_vendida'] or 0.0,
            'clima_pico': item['clima_pico'] or 'AMENO',
            'is_composto': False,
            'ingredientes': []
        }

    # Carrega receitas para compostos
    cursor.execute('SELECT id_produto, id_ingrediente, qntdd FROM receita')
    for row in cursor.fetchall():
        r_dict = dict(row)
        id_comp = r_dict['id_produto']
        if id_comp in produtos_map:
            produtos_map[id_comp]['is_composto'] = True
            produtos_map[id_comp]['ingredientes'].append({
                'id_ingrediente': r_dict['id_ingrediente'],
                'qntdd': float(r_dict['qntdd'])
            })

    produtos_sazonais = []
    for pid, pdata in produtos_map.items():
        nome = pdata['nome']
        qtd_vendida = pdata['qtd_vendida']
        
        if pdata['is_composto']:
            # Produto Composto: Estoque baseado no insumo dos ingredientes
            qtd_produzivel = []
            ingr_nomes = []
            climas_ingr = []
            
            for ing in pdata['ingredientes']:
                ing_id = ing['id_ingrediente']
                qntdd = ing['qntdd']
                ing_info = produtos_map.get(ing_id)
                if ing_info:
                    ingr_nomes.append(ing_info['nome'].strip())
                    climas_ingr.append(ing_info['clima_pico'])
                    max_cartelas = (ing_info['estoque_caixas'] / qntdd) if qntdd > 0 else 0
                    qtd_produzivel.append(max_cartelas)
            
            estoque_cartelas = min(qtd_produzivel) if qtd_produzivel else 0.0
            estoque_caixas = estoque_cartelas / 12.0
            clima_pico = climas_ingr[0] if climas_ingr else 'AMENO'
            ref_ing = ", ".join(ingr_nomes)
            
            if estoque_cartelas > 0:
                status_badge = 'FAVORÁVEL'
                status_icone = '✅'
                status_class = 'status-favoravel'
                diagnostico = f'Produto Composto. Produzível ({estoque_cartelas:.0f} un) via {ref_ing}. Média sazonal: {clima_pico}.'
            else:
                status_badge = 'ATENÇÃO'
                status_icone = '⚠️'
                status_class = 'status-atencao'
                diagnostico = f'Sem insumo suficiente ({ref_ing}) para montagem.'
        else:
            # Produto Simples
            estoque_caixas = pdata['estoque_caixas']
            estoque_cartelas = estoque_caixas * 12.0
            clima_pico = pdata['clima_pico']
            
            if estoque_caixas < 0:
                status_badge = 'ALERTA URGENTE'
                status_icone = '🚨'
                status_class = 'status-urgente'
                diagnostico = f'Estoque negativo ({estoque_caixas:.2f} cx). Ruptura em alta demanda.'
            elif estoque_caixas == 0 and qtd_vendida > 0:
                status_badge = 'ATENÇÃO'
                status_icone = '⚠️'
                status_class = 'status-atencao'
                diagnostico = f'Estoque zerado! Pico de vendas histórico em clima {clima_pico}.'
            elif qtd_vendida == 0 and estoque_caixas == 0:
                status_badge = 'ATENÇÃO'
                status_icone = '🟡'
                status_class = 'status-atencao'
                diagnostico = f'Sem movimentação no catálogo. Recomendado lote inicial.'
            else:
                status_badge = 'FAVORÁVEL'
                status_icone = '✅'
                status_class = 'status-favoravel'
                diagnostico = f'Excelente estoque ({estoque_caixas:.2f} cx). Pico de vendas em clima {clima_pico}.'
                
        produtos_sazonais.append({
            'id': str(pid),
            'nome': nome,
            'is_composto': pdata['is_composto'],
            'estoque_caixas': estoque_caixas,
            'estoque_cartelas': estoque_cartelas,
            'qtd_vendida': qtd_vendida,
            'clima_pico': clima_pico,
            'status_badge': status_badge,
            'status_icone': status_icone,
            'status_class': status_class,
            'diagnostico': diagnostico
        })

    alertas_produtos = [p for p in produtos_sazonais if p['estoque_caixas'] <= 0]

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'total_produtos': total_produtos,
        'faturamento_total': faturamento_total,
        'lucro_total': lucro_total,
        'grafico_json': json.dumps(dados_grafico),
        'tendencias': tendencias,
        'alertas_produtos': alertas_produtos,
        'produtos_sazonais': produtos_sazonais,
        'meses_disponiveis': meses_disponiveis,
        'mes_pico_faturamento': mes_pico_faturamento,
        'mes_baixa_faturamento': mes_baixa_faturamento,
        'mes_maior_perda': mes_maior_perda
    })

def relatorios_view(request):
    conn = BancoDB.obter_conexao()
    cursor = conn.cursor()
    
    # Impacto do Rio (SECA vs NORMAL vs CHEIA) no Volume Total de Vendas
    cursor.execute('''
        SELECT 
            COALESCE(s.indicador_rio, 'DESCONHECIDO') as estado_rio,
            SUM(ABS(f.quantidade) * f.valorUnidario) as faturamento,
            SUM(f.lucroTotal) as lucro
        FROM fluxoEstoque f
        LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
        WHERE f.id_tipoNota = 2
        GROUP BY COALESCE(s.indicador_rio, 'DESCONHECIDO')
    ''')
    impacto_rio = []
    for row in cursor.fetchall():
        impacto_rio.append({
            'estado_rio': row['estado_rio'],
            'faturamento': row['faturamento'] or 0,
            'lucro': row['lucro'] or 0
        })
        
    return render(request, 'relatorios_sazonalizei.html', {
        'impacto_rio_json': json.dumps(impacto_rio)
    })

def entidades_view(request):
    return render(request, 'entidades.html', {})
def fornecedores_view(request):
    return render(request, 'fornecedores.html', {})
def clientes_view(request):
    return render(request, 'clientes.html', {})
def pdv_view(request):
    return render(request, 'pdv.html', {})
def financeiro_view(request):
    return render(request, 'financeiro.html', {})
def configuracoes_view(request):
    return render(request, 'configuracoes.html', {})
def logout_view(request):
    from django.shortcuts import redirect
    return redirect('dashboard')
