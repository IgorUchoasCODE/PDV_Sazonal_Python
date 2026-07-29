import sqlite3
from br.com.pdv.src.BDD.bancodb import BancoDB

conn = BancoDB.obter_conexao()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Carrega estoque e métricas sazonais dos produtos simples
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

produtos_map = {}
for row in cursor.fetchall():
    d = dict(row)
    produtos_map[d['id']] = {
        'id': d['id'],
        'nome': d['nome'],
        'estoque_caixas': d['estoque_caixas'] or 0.0,
        'qtd_vendida': d['qtd_vendida'] or 0.0,
        'clima_pico': d['clima_pico'] or 'AMENO',
        'is_composto': False,
        'ingredientes': []
    }

# 2. Verifica receitas de produtos compostos
cursor.execute('SELECT id_produto, id_ingrediente, qntdd FROM receita')
for row in cursor.fetchall():
    d = dict(row)
    id_comp = d['id_produto']
    id_ingr = d['id_ingrediente']
    qntdd = float(d['qntdd'])
    
    if id_comp in produtos_map:
        produtos_map[id_comp]['is_composto'] = True
        produtos_map[id_comp]['ingredientes'].append({
            'id_ingrediente': id_ingr,
            'qntdd': qntdd
        })

# 3. Processa estoque e diagnóstico final para todos
resultado_final = []
for pid, pdata in produtos_map.items():
    if pdata['is_composto']:
        # Produto Composto
        qtd_produzivel_cartelas = []
        ingr_nomes = []
        climas_ingr = []
        
        for ing in pdata['ingredientes']:
            ing_id = ing['id_ingrediente']
            qntdd = ing['qntdd']
            ing_data = produtos_map.get(ing_id)
            if ing_data:
                ingr_nomes.append(ing_data['nome'])
                climas_ingr.append(ing_data['clima_pico'])
                # Quantos deste composto dá para fazer?
                qtd_max = ing_data['estoque_caixas'] / qntdd if qntdd > 0 else 0
                qtd_produzivel_cartelas.append(qtd_max)
                
        estoque_cartelas = min(qtd_produzivel_cartelas) if qtd_produzivel_cartelas else 0.0
        estoque_caixas = estoque_cartelas / 12.0
        clima_pico = climas_ingr[0] if climas_ingr else 'AMENO'
        ing_ref = ", ".join(ingr_nomes)
        
        if estoque_cartelas > 0:
            status_badge = 'FAVORÁVEL'
            status_icone = '✅'
            status_class = 'status-favoravel'
            diagnostico = f'Produto Composto. Produzível ({estoque_cartelas:.0f} un) via {ing_ref}. Média sazonal: {clima_pico}.'
        else:
            status_badge = 'ATENÇÃO'
            status_icone = '⚠️'
            status_class = 'status-atencao'
            diagnostico = f'Sem insumo suficiente de {ing_ref} para montagem.'
            
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
        elif estoque_caixas == 0:
            status_badge = 'ATENÇÃO'
            status_icone = '⚠️'
            status_class = 'status-atencao'
            diagnostico = f'Estoque zerado. Demanda sazonal histórica em clima {clima_pico}.'
        else:
            status_badge = 'FAVORÁVEL'
            status_icone = '✅'
            status_class = 'status-favoravel'
            diagnostico = f'Excelente estoque ({estoque_caixas:.2f} cx). Pico de vendas em clima {clima_pico}.'

    resultado_final.append({
        'id': pid,
        'nome': pdata['nome'],
        'is_composto': pdata['is_composto'],
        'estoque_cartelas': estoque_cartelas,
        'estoque_caixas': estoque_caixas,
        'qtd_vendida': pdata['qtd_vendida'],
        'clima_pico': clima_pico,
        'status_badge': status_badge,
        'status_icone': status_icone,
        'status_class': status_class,
        'diagnostico': diagnostico
    })

for r in resultado_final:
    print(f"[{'COMPOSTO' if r['is_composto'] else 'SIMPLES'}] {r['nome']} | Est. Cartelas: {r['estoque_cartelas']:.0f} | Est. Caixas: {r['estoque_caixas']:.2f} | Clima: {r['clima_pico']}")
    print(f"   -> Diagnóstico: {r['diagnostico']}\n")
