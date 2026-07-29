from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

# Calculate per-product seasonal indicators
produtos_status = []
for pid_str, pdata in InventoryManager._mapaProdutos.items():
    produto = pdata.get('produto')
    nome = produto.nome if produto else f'Produto {pid_str}'
    qtd_estoque = pdata.get('quantidadeTotal', 0.0)
    vendas_total = pdata.get('valorTotalVendas', 0.0)
    
    # Let's get seasonal breakdown for this product
    tend_prod = InventoryManager.analisar_tendencias_sazonais(id_produto=int(pid_str))
    resumo = tend_prod.get('resumo', {})
    clima_top = tend_prod.get('indicadores', {}).get('clima_mais_vendas', 'AMENO')
    
    # Logic for status
    if qtd_estoque < 0:
        status_cor = 'vermelho'
        status_label = 'Alerta Urgente'
        status_icone = '🔴'
        motivo = f'Estoque negativo ({qtd_estoque:.2f}). Risco imediato de ruptura.'
    elif vendas_total > 5000 and qtd_estoque > 0:
        status_cor = 'verde'
        status_label = 'Favorável'
        status_icone = '🟢'
        motivo = f'Alta demanda em clima {clima_top}. Faturamento: R$ {vendas_total:.2f}.'
    elif qtd_estoque == 0:
        status_cor = 'amarelo'
        status_label = 'Atenção'
        status_icone = '🟡'
        motivo = f'Sem estoque para atender o pico em clima {clima_top}.'
    else:
        status_cor = 'verde'
        status_label = 'Favorável'
        status_icone = '🟢'
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
    print(item)
