from br.com.pdv.src.memory.inventoryManager import InventoryManager
import inspect

# Let's run mapearProdutos and trace product 1
InventoryManager.carregarTudo()

# Let's inspect how NotasVendas or _Notas define prod for product 1
notas = InventoryManager._ordenarTodasAsNotas()
qtd_acumulada = 0.0
for n in notas:
    d = n.getDados()
    tipo = d.get('id_tipoNota') or n.__class__.__name__
    prods = d.get('produtos', {})
    for k, p in prods.items():
        if str(p.get('id')) == '1':
            if 'Compra' in str(type(n)):
                qtd = p.get('quantidadeEntrada', 0.0)
                qtd_acumulada += qtd
                print(f"[COMPRA {d.get('id')}] +{qtd:.4f} -> Total: {qtd_acumulada:.4f}")
            elif 'Venda' in str(type(n)):
                qtd = p.get('vendas', p.get('quantidadeEntrada', 0.0))
                qtd_acumulada -= qtd
                print(f"[VENDA {d.get('id')}] -{qtd:.4f} (vendas={p.get('vendas')}, qtdEntrada={p.get('quantidadeEntrada')}) -> Total: {qtd_acumulada:.4f}")
