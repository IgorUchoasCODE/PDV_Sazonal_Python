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
        
        ind_rio = row['indicador_rio'] or 'NORMAL'
        ind_chuva = row['indicador_chuva'] or 'MODERADO'

        dados_grafico.append({
            'dia': row['dia'],
            'mes_ano': m_ano,
            'valor_venda': v_venda,
            'lucro_venda': row['lucro_venda'] or 0,
            'valor_perda': v_perda,
            'nivel_rio': row['nivel_rio'] or 0,
            'temperatura': row['temperatura'] or 0,
            'clima': row['clima'] or 'AMENO',
            'indicador_rio': ind_rio,
            'indicador_chuva': ind_chuva
        })

        if m_ano:
            if m_ano not in meses_totais:
                meses_totais[m_ano] = {'vendas': 0.0, 'perdas': 0.0, 'cheia': 0, 'seca': 0, 'chuva': 0}
            meses_totais[m_ano]['vendas'] += v_venda
            meses_totais[m_ano]['perdas'] += v_perda
            if ind_rio == 'CHEIA': meses_totais[m_ano]['cheia'] += 1
            if ind_rio == 'SECA':  meses_totais[m_ano]['seca'] += 1
            if ind_chuva == 'CHUVOSO': meses_totais[m_ano]['chuva'] += 1

    # Identifica atalhos estatísticos
    mes_pico_faturamento = max(meses_totais, key=lambda k: meses_totais[k]['vendas']) if meses_totais else ''
    mes_baixa_faturamento = min(meses_totais, key=lambda k: meses_totais[k]['vendas']) if meses_totais else ''
    mes_maior_perda = max(meses_totais, key=lambda k: meses_totais[k]['perdas']) if meses_totais else ''
    
    mes_pico_cheia = max(meses_totais, key=lambda k: meses_totais[k]['cheia']) if meses_totais and any(m['cheia'] > 0 for m in meses_totais.values()) else ''
    mes_pico_seca = max(meses_totais, key=lambda k: meses_totais[k]['seca']) if meses_totais and any(m['seca'] > 0 for m in meses_totais.values()) else ''
    mes_pico_chuva = max(meses_totais, key=lambda k: meses_totais[k]['chuva']) if meses_totais and any(m['chuva'] > 0 for m in meses_totais.values()) else ''

    def get_mes_nome(m_str):
        if not m_str: return ''
        partes = m_str.split('-')
        if len(partes) == 2:
            return f"{NOMES_MESES.get(partes[1], partes[1])} {partes[0]}"
        return m_str

    mes_pico_label = get_mes_nome(mes_pico_faturamento)
    mes_baixa_label = get_mes_nome(mes_baixa_faturamento)
    mes_maior_perda_label = get_mes_nome(mes_maior_perda)
    
    mes_cheia_label = get_mes_nome(mes_pico_cheia)
    mes_seca_label = get_mes_nome(mes_pico_seca)
    mes_chuva_label = get_mes_nome(mes_pico_chuva)

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
        'mes_pico_label': mes_pico_label,
        'mes_baixa_faturamento': mes_baixa_faturamento,
        'mes_baixa_label': mes_baixa_label,
        'mes_maior_perda': mes_maior_perda,
        'mes_maior_perda_label': mes_maior_perda_label,
        'mes_cheia_label': mes_cheia_label,
        'mes_seca_label': mes_seca_label,
        'mes_chuva_label': mes_chuva_label
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
        
    # Inteligência Sazonal de Estoque e Compras
    cursor.execute('''
        SELECT 
            p.id, p.nome, p.diasDuraveis,
            (
                SELECT s1.indicador_clima || ' / ' || s1.indicador_rio 
                FROM fluxoEstoque f1 
                JOIN snapshot_sazonal s1 ON f1.id_fluxo_nota = s1.id_fluxo_nota 
                WHERE f1.id_produto = p.id AND f1.id_tipoNota = 1 
                GROUP BY s1.indicador_clima, s1.indicador_rio 
                ORDER BY AVG(f1.valorUnidario) ASC LIMIT 1
            ) as melhor_epoca_compra,
            (
                SELECT s2.indicador_clima || ' / ' || s2.indicador_rio || ' (Evt: ' || COALESCE(s2.evento_tipo, 'NENHUM') || ')'
                FROM fluxoEstoque f2 
                JOIN snapshot_sazonal s2 ON f2.id_fluxo_nota = s2.id_fluxo_nota 
                WHERE f2.id_produto = p.id AND f2.id_tipoNota = 2 
                GROUP BY s2.indicador_clima, s2.indicador_rio, s2.evento_tipo 
                ORDER BY SUM(ABS(f2.quantidade)) DESC LIMIT 1
            ) as pico_vendas
        FROM produto p
    ''')
    
    inteligencia_produtos = []
    for row in cursor.fetchall():
        melhor_compra = row['melhor_epoca_compra'] or "Sem dados"
        pico_vendas = row['pico_vendas'] or "Sem dados"
        durabilidade = row['diasDuraveis'] or 365
        
        # Gerar recomendação
        if melhor_compra != "Sem dados" and pico_vendas != "Sem dados":
            if durabilidade >= 180:
                rec = f"Alta durabilidade ({durabilidade} dias). Seguro comprar grandes lotes em {melhor_compra} para vender no pico de {pico_vendas}."
                risco = "Baixo"
            elif durabilidade < 30:
                rec = f"Baixa durabilidade ({durabilidade} dias). Compre apenas perto do pico de vendas ({pico_vendas}), mesmo que o custo seja maior."
                risco = "Alto"
            else:
                rec = f"Durabilidade média ({durabilidade} dias). Tente comprar em {melhor_compra}, se estiver próximo ao pico de {pico_vendas}."
                risco = "Médio"
        else:
            rec = "Dados insuficientes para gerar recomendação sazonal."
            risco = "Desconhecido"
            
        inteligencia_produtos.append({
            'nome': row['nome'],
            'melhor_compra': melhor_compra,
            'pico_vendas': pico_vendas,
            'durabilidade': f"{durabilidade} dias",
            'risco': risco,
            'recomendacao': rec
        })
        
    # Adicionar Perdas com Dados Sazonais para Cards
    cursor.execute('''
        SELECT 
            f.data, 
            ABS(f.quantidade) as qtd_perdida, 
            p.nome as produto, 
            (ABS(f.quantidade) * f.valorUnidario) as prejuizo,
            s.indicador_clima, 
            s.indicador_rio, 
            s.indicador_chuva,
            s.evento_nome,
            s.evento_tipo
        FROM fluxoEstoque f
        JOIN produto p ON f.id_produto = p.id
        LEFT JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
        WHERE f.id_tipoNota = 4
        ORDER BY f.data DESC
    ''')
    historico_perdas = [dict(row) for row in cursor.fetchall()]

    # Melhor Padrão de Venda
    cursor.execute('''
        SELECT 
            s.evento_nome,
            s.evento_tipo,
            s.indicador_clima,
            s.indicador_rio,
            COUNT(f.id) as qtd_operacoes,
            SUM(ABS(f.quantidade)) as volume_vendido,
            SUM(f.lucroTotal) as lucro_total
        FROM fluxoEstoque f
        JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
        WHERE f.id_tipoNota = 2
        GROUP BY s.evento_nome, s.evento_tipo, s.indicador_clima, s.indicador_rio
        ORDER BY lucro_total DESC
        LIMIT 1
    ''')
    row_venda = cursor.fetchone()
    padrao_venda = dict(row_venda) if row_venda else None

    # Melhor Padrão de Compra
    cursor.execute('''
        SELECT 
            s.evento_nome,
            s.evento_tipo,
            s.indicador_clima,
            s.indicador_rio,
            COUNT(f.id) as qtd_operacoes,
            SUM(ABS(f.quantidade)) as volume_comprado,
            AVG(f.valorUnidario) as custo_medio
        FROM fluxoEstoque f
        JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
        WHERE f.id_tipoNota = 1
        GROUP BY s.evento_nome, s.evento_tipo, s.indicador_clima, s.indicador_rio
        ORDER BY custo_medio ASC
        LIMIT 1
    ''')
    row_compra = cursor.fetchone()
    padrao_compra = dict(row_compra) if row_compra else None

    # Análise de Comportamento por Evento
    cursor.execute('''
        SELECT 
            s.evento_nome, 
            s.evento_tipo, 
            SUM(CASE WHEN f.id_tipoNota = 1 THEN ABS(f.quantidade) ELSE 0 END) as vol_compras,
            SUM(CASE WHEN f.id_tipoNota = 2 THEN ABS(f.quantidade) ELSE 0 END) as vol_vendas,
            SUM(CASE WHEN f.id_tipoNota = 4 THEN ABS(f.quantidade) ELSE 0 END) as vol_perdas,
            SUM(CASE WHEN f.id_tipoNota = 2 THEN f.lucroTotal ELSE 0 END) as lucro_gerado
        FROM fluxoEstoque f
        JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
        WHERE s.evento_nome IS NOT NULL
        GROUP BY s.evento_nome, s.evento_tipo
        ORDER BY vol_vendas DESC
    ''')
    analise_eventos = [dict(row) for row in cursor.fetchall()]

    # Adicionar Eventos Privados (Sympla)
    try:
        from br.com.pdv.src.apis.eventos.eventos_api import EventosAPI
        api = EventosAPI()
        eventos_sympla = api.obter_eventos_privados()
        for ev in eventos_sympla:
            analise_eventos.append({
                'evento_nome': ev.nome,
                'evento_tipo': 'PRIVADO (Sympla)',
                'vol_compras': 0,
                'vol_vendas': 0,
                'vol_perdas': 0,
                'lucro_gerado': 0
            })
    except Exception as e:
        print(f"Erro ao buscar Sympla: {e}")

    # Melhores Padrões de Venda por Produto (Margem Saudável)
    cursor.execute('''
        SELECT 
            p.nome as produto,
            s.evento_nome,
            s.evento_tipo,
            s.indicador_clima,
            s.indicador_rio,
            SUM(ABS(f.quantidade)) as volume_vendas,
            SUM(f.lucroTotal) as lucro_total,
            (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 as margem_percentual
        FROM fluxoEstoque f
        JOIN produto p ON f.id_produto = p.id
        JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
        WHERE f.id_tipoNota = 2
        GROUP BY p.nome, s.evento_nome, s.evento_tipo, s.indicador_clima, s.indicador_rio
        HAVING volume_vendas >= 2
        ORDER BY 
            (CASE WHEN margem_percentual >= 18 AND margem_percentual <= 30 THEN 1 ELSE 0 END) DESC, 
            lucro_total DESC
    ''')
    melhores_vendas_produtos = [dict(row) for row in cursor.fetchall()]

    # 🔮 Previsões e Estratégias (Próximos 60 Dias)
    estrategias_futuras = []
    try:
        from datetime import datetime, timedelta
        from br.com.pdv.src.apis.eventos.eventos_api import EventosAPI
        from br.com.pdv.src.apis.gerenciadorSazonal import GerenciadorSazonal
        
        hoje = datetime.now()
        fim = hoje + timedelta(days=60)
        api_eventos = EventosAPI()
        todos_ev = api_eventos.obter_todos_eventos(50)
        futuros = [e for e in todos_ev if e.data_inicio and hoje <= datetime.strptime(e.data_inicio[:10], '%Y-%m-%d') <= fim]
        
        # Priorizar eventos PRIVADOS (Sympla, etc.)
        futuros.sort(key=lambda x: 0 if x.tipo.upper() == 'PRIVADO' else 1)
        
        sazonal_preditivo = GerenciadorSazonal()
        produtos_sugeridos = set()
        
        for f in futuros[:8]:
            data_ev = f.data_inicio[:10]
            indicadores = sazonal_preditivo.obter_indicadores_por_data(data_ev)
            clima = indicadores.get('clima_atual', 'AMENO')
            rio = indicadores.get('nivel_rio_atual', 'NORMAL')
            tipo_ev = f.tipo.upper()
            
            # Melhor para vender (Equilibrando Margem Saudável, Volume e Lucro Total)
            venda_exata = True
            venda_similar = False
            
            # 1. Busca Exata
            cursor.execute('''
                SELECT p.id as id_produto, p.nome as produto, SUM(ABS(f.quantidade)) as vol, SUM(f.lucroTotal) as lucro,
                       (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 as margem
                FROM fluxoEstoque f
                JOIN produto p ON f.id_produto = p.id
                JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
                WHERE f.id_tipoNota = 2 AND s.evento_nome = ? AND s.indicador_clima = ? AND s.indicador_rio = ?
                GROUP BY p.nome, p.id
                HAVING vol >= 2
                ORDER BY (CASE WHEN (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 >= 18 AND (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 <= 30 THEN 1 ELSE 0 END) DESC, (lucro * vol) DESC LIMIT 10
            ''', (f.nome, clima, rio))
            candidatos_exatos = cursor.fetchall()
            venda = next((c for c in candidatos_exatos if c['produto'] not in produtos_sugeridos), None)

            if not venda:
                # 2. Busca Similar (Tipo de Evento)
                venda_exata = False
                venda_similar = True
                cursor.execute('''
                    SELECT p.id as id_produto, p.nome as produto, SUM(ABS(f.quantidade)) as vol, SUM(f.lucroTotal) as lucro,
                           (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 as margem
                    FROM fluxoEstoque f
                    JOIN produto p ON f.id_produto = p.id
                    JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
                    WHERE f.id_tipoNota = 2 AND s.evento_tipo = ? AND s.indicador_clima = ? AND s.indicador_rio = ?
                    GROUP BY p.nome, p.id
                    HAVING vol >= 2
                    ORDER BY (CASE WHEN (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 >= 18 AND (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 <= 30 THEN 1 ELSE 0 END) DESC, (lucro * vol) DESC LIMIT 10
                ''', (tipo_ev, clima, rio))
                candidatos_similares = cursor.fetchall()
                venda = next((c for c in candidatos_similares if c['produto'] not in produtos_sugeridos), None)

            if not venda:
                # 3. Fallback Global Sazonal
                venda_similar = False
                cursor.execute('''
                    SELECT p.id as id_produto, p.nome as produto, SUM(ABS(f.quantidade)) as vol, SUM(f.lucroTotal) as lucro,
                           (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 as margem
                    FROM fluxoEstoque f
                    JOIN produto p ON f.id_produto = p.id
                    JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
                    WHERE f.id_tipoNota = 2 AND s.evento_nome IS NOT NULL
                    GROUP BY p.nome, p.id
                    HAVING vol >= 2
                    ORDER BY (CASE WHEN (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 >= 18 AND (SUM(f.lucroTotal) / NULLIF(SUM(ABS(f.quantidade) * f.valorUnidario), 0)) * 100 <= 30 THEN 1 ELSE 0 END) DESC, (lucro * vol) DESC LIMIT 20
                ''')
                candidatos_globais = cursor.fetchall()
                venda = next((c for c in candidatos_globais if c['produto'] not in produtos_sugeridos), None)
                if not venda and candidatos_globais:
                    venda = candidatos_globais[0]
            
            if venda:
                produtos_sugeridos.add(venda['produto'])
            
            # Melhor para comprar (O mesmo produto que foi sugerido vender)
            compra = None
            compra_exata = True
            compra_similar = False
            
            if venda:
                id_prod = venda['id_produto']
                cursor.execute('''
                    SELECT AVG(f.valorUnidario) as custo
                    FROM fluxoEstoque f
                    JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
                    WHERE f.id_tipoNota = 1 AND f.id_produto = ? AND s.evento_nome = ? AND s.indicador_clima = ? AND s.indicador_rio = ?
                ''', (id_prod, f.nome, clima, rio))
                compra = cursor.fetchone()

                if not compra or compra['custo'] is None:
                    compra_exata = False
                    compra_similar = True
                    cursor.execute('''
                        SELECT AVG(f.valorUnidario) as custo
                        FROM fluxoEstoque f
                        JOIN snapshot_sazonal s ON f.id_notaOrigem = s.id_fluxo_nota
                        WHERE f.id_tipoNota = 1 AND f.id_produto = ? AND s.evento_tipo = ? AND s.indicador_clima = ? AND s.indicador_rio = ?
                    ''', (id_prod, tipo_ev, clima, rio))
                    compra = cursor.fetchone()

                if not compra or compra['custo'] is None:
                    compra_similar = False
                    cursor.execute('''
                        SELECT AVG(f.valorUnidario) as custo
                        FROM fluxoEstoque f
                        WHERE f.id_tipoNota = 1 AND f.id_produto = ?
                    ''', (id_prod,))
                    compra = cursor.fetchone()
            
            estrategias_futuras.append({
                'evento_nome': f.nome,
                'evento_tipo': tipo_ev,
                'data': data_ev,
                'clima': clima,
                'rio': rio,
                'sugestao_venda': dict(venda) if venda else None,
                'venda_exata': venda_exata,
                'venda_similar': venda_similar,
                'sugestao_compra': {'produto': venda['produto'], 'custo': compra['custo']} if (venda and compra and compra['custo'] is not None) else None,
                'compra_exata': compra_exata,
                'compra_similar': compra_similar
            })
    except Exception as e:
        print(f"Erro ao processar estratégias futuras: {e}")

    return render(request, 'relatorios_sazonalizei.html', {
        'impacto_rio_json': json.dumps(impacto_rio),
        'inteligencia_produtos': inteligencia_produtos,
        'historico_perdas': historico_perdas,
        'padrao_venda': padrao_venda,
        'padrao_compra': padrao_compra,
        'analise_eventos': analise_eventos,
        'melhores_vendas_produtos': melhores_vendas_produtos,
        'estrategias_futuras': estrategias_futuras
    })

def entidades_view(request):
    from core.helpers import entidades_context
    return render(request, 'entidades.html', entidades_context())

def api_detalhes_pagamento(request, id):
    from django.http import HttpResponse
    import json
    import datetime
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
            
            # Map forms for payments
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
            
        return HttpResponse(json.dumps({"sucesso": False, "mensagem": "Nota não encontrada."}), content_type="application/json")
    except Exception as e:
        return HttpResponse(json.dumps({"sucesso": False, "mensagem": str(e)}), content_type="application/json")

def fornecedores_view(request):
    from core.helpers import get_fornecedores
    from br.com.pdv.src.BDD.bancodb import BancoDB
    import sqlite3
    
    fornecedores_raw = get_fornecedores()
    arvore_fornecedores = []
    
    conn = BancoDB.obter_conexao()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    for f in fornecedores_raw:
        extrato_resumo = f.get('extrato', {}).get('resumo', {})
        node = {
            'id': f['id_entidade'],
            'nome': f.get('empresa_nome') or f.get('pessoa_nome') or f"Fornecedor {f['id_entidade']}",
            'resumo': extrato_resumo,
            'compras': [],
            'lista_perdas': []
        }
        
        historico_notas = f.get('extrato', {}).get('historico_notas', [])
        historico_pagamentos = f.get('extrato', {}).get('historico_pagamentos', [])
        
        notas_compra = [n for n in historico_notas if n['id_tipoNota'] == 1]
        
        tem_perdas = False
        for nc in notas_compra:
            id_compra = nc['id_fluxo_nota']
            pags = [p for p in historico_pagamentos if p['id_fluxo_nota'] == id_compra]
            
            cursor.execute('''
                SELECT 
                    f.id_fluxo_nota as id_nota, 
                    f.data, 
                    ABS(f.quantidade) as quantidade, 
                    f.id_tipoNota, 
                    (ABS(f.quantidade) * f.valorUnidario) as valor,
                    p.id as id_produto,
                    p.nome as produto_nome,
                    f.id_notaOrigem as nota_origem,
                    fn_origem.data as data_origem
                FROM fluxoEstoque f
                LEFT JOIN produto p ON f.id_produto = p.id
                LEFT JOIN fluxoEstoque fn_origem ON f.id_notaOrigem = fn_origem.id_fluxo_nota AND fn_origem.id_tipoNota = 1
                WHERE f.id_notaOrigem = ? AND f.id_tipoNota IN (3, 4, 5)
                GROUP BY f.id, f.id_fluxo_nota
            ''', (id_compra,))
            flutuacoes = [dict(row) for row in cursor.fetchall()]
            
            for fl in flutuacoes:
                if hasattr(fl['data'], 'strftime'):
                    fl['data'] = fl['data'].strftime('%Y-%m-%d')
                if hasattr(fl.get('data_origem'), 'strftime'):
                    fl['data_origem'] = fl['data_origem'].strftime('%Y-%m-%d')
                if fl.get('id_tipoNota') == 4:
                    tem_perdas = True
                    node['lista_perdas'].append(fl)
            
            compra_node = {
                'id_nota': id_compra,
                'data_vencimento': nc.get('data_vencimento') or 'N/A',
                'total_nota': nc.get('total_nota', 0),
                'pagamentos': pags,
                'flutuacoes': flutuacoes
            }
            node['compras'].append(compra_node)
            
        node['tem_perdas'] = tem_perdas
        arvore_fornecedores.append(node)
        
    import json
    mapa_perdas = {}
    for node in arvore_fornecedores:
        mapa_perdas[node['id']] = node.get('lista_perdas', [])
        
    from br.com.pdv.src.memory.paymentManager import PaymentManager
    saldo_caixa = PaymentManager.get_resumo_financeiro_global().get('saldo_liquido_caixa', 0.0)
        
    return render(request, 'fornecedores.html', {
        'arvore_fornecedores': arvore_fornecedores,
        'saldo_caixa': saldo_caixa,
        'mapa_perdas_json': json.dumps(mapa_perdas)
    })
def clientes_view(request):
    from core.helpers import get_clientes
    from br.com.pdv.src.BDD.bancodb import BancoDB
    import sqlite3
    
    clientes_raw = get_clientes()
    arvore_clientes = []
    
    conn = BancoDB.obter_conexao()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    for c in clientes_raw:
        extrato_resumo = c.get('extrato', {}).get('resumo', {})
        node = {
            'id': c['id_entidade'],
            'nome': c.get('pessoa_nome') or c.get('empresa_nome') or f"Cliente {c['id_entidade']}",
            'resumo': extrato_resumo,
            'vendas': [],
            'lista_devolucoes': [],
            'lista_perdas': []
        }
        
        historico_notas = c.get('extrato', {}).get('historico_notas', [])
        historico_pagamentos = c.get('extrato', {}).get('historico_pagamentos', [])
        
        notas_venda = [n for n in historico_notas if n['id_tipoNota'] == 2]
        
        tem_devolucoes_ou_perdas = False
        for nv in notas_venda:
            id_venda = nv['id_fluxo_nota']
            pags = [p for p in historico_pagamentos if p['id_fluxo_nota'] == id_venda]
            
            cursor.execute('''
                SELECT 
                    f.id_fluxo_nota as id_nota, 
                    f.data, 
                    ABS(f.quantidade) as quantidade, 
                    f.id_tipoNota, 
                    (ABS(f.quantidade) * f.valorUnidario) as valor,
                    p.id as id_produto,
                    p.nome as produto_nome,
                    f.id_notaOrigem as nota_origem,
                    fn_origem.data as data_origem
                FROM fluxoEstoque f
                LEFT JOIN produto p ON f.id_produto = p.id
                LEFT JOIN fluxoEstoque fn_origem ON f.id_notaOrigem = fn_origem.id_fluxo_nota AND fn_origem.id_tipoNota = 2
                WHERE f.id_notaOrigem = ? AND f.id_tipoNota IN (3, 4, 5)
                GROUP BY f.id, f.id_fluxo_nota
            ''', (id_venda,))
            flutuacoes = [dict(row) for row in cursor.fetchall()]
            
            for fl in flutuacoes:
                if hasattr(fl['data'], 'strftime'):
                    fl['data'] = fl['data'].strftime('%Y-%m-%d')
                if hasattr(fl.get('data_origem'), 'strftime'):
                    fl['data_origem'] = fl['data_origem'].strftime('%Y-%m-%d')
                
                if fl.get('id_tipoNota') == 3:
                    tem_devolucoes_ou_perdas = True
                    node['lista_devolucoes'].append(fl)
                elif fl.get('id_tipoNota') in (4, 5):
                    tem_devolucoes_ou_perdas = True
                    node['lista_perdas'].append(fl)
            
            venda_node = {
                'id_nota': id_venda,
                'data_vencimento': nv.get('data_vencimento') or 'N/A',
                'total_nota': nv.get('total_nota', 0),
                'pagamentos': pags,
                'flutuacoes': flutuacoes
            }
            node['vendas'].append(venda_node)
            
        node['tem_devolucoes_ou_perdas'] = tem_devolucoes_ou_perdas
        arvore_clientes.append(node)
        
    return render(request, 'clientes.html', {
        'arvore_clientes': arvore_clientes,
        'pagina_atual': 'clientes'
    })
def pdv_view(request):
    from core.helpers import pdv_context
    ctx = pdv_context()
    ctx['pagina_atual'] = 'pdv'
    return render(request, 'pdv.html', ctx)

def financeiro_view(request):
    from core.helpers import financeiro_context
    return render(request, 'financeiro.html', financeiro_context())
def configuracoes_view(request):
    return render(request, 'configuracoes.html', {})
def logout_view(request):
    from django.shortcuts import redirect
    return redirect('dashboard')
