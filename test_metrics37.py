from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

# Calculate per-product seasonal indicators
produtos_status = []
for pid_str, pdata in InventoryManager._mapaProdutos.items():
    produto = pdata.get('produto')
    nome = produto.nome if produto else f'Produto {pid_str}'
    qtd_estoque = pdata.get('quantidadeTotal', 0.0)
    vendas_total = pdata.get('valorTotalVendas', 0.0)
    
    tend_prod = InventoryManager.analisar_tendencias_sazonais(id_produto=int(pid_str))
    clima_top = tend_prod.get('indicadores', {}).get('clima_mais_vendas', 'AMENO')
    
    if qtd_estoque < 0:
        status_cor = 'vermelho'
        status_label = 'Alerta Urgente'
        status_icone = '[VERMELHO]'
        motivo = f'Estoque negativo ({qtd_estoque:.2f}). Risco imediato de ruptura.'
    elif vendas_total > 5000 and qtd_estoque > 0:
        status_cor = 'verde'
        status_label = 'Favoravel'
        status_icone = '[VERDE]'
        motivo = f'Alta demanda em clima {clima_top}. Faturamento: R$ {vendas_total:.2f}.'
    elif qtd_estoque == 0:
        status_cor = 'amarelo'
        status_label = 'Atencao'
        status_icone = '[AMARELO]'
        motivo = f'Sem estoque para atender o pico em clima {clima_top}.'
    else:
        status_cor = 'verde'
        status_label = 'Favoravel'
        status_icone = '[VERDE]'
        motivo = f'Demanda regular em clima {clima_top}.'
        
    produtos_status.append({
        'id': pid_str,
        'nome': nome,
        'estoque': qtd_estoque,
        'vendas': vendas_total,
        'status_cor': status_cor,
        'status_label': status_label,
        'status_icone': status_icone,
        'motivo': motivo,
        'clima_top': clima_top
    })

for item in produtos_status:
    print(item['nome'], '| Status:', item['status_label'], '| Motivo:', item['motivo'])
