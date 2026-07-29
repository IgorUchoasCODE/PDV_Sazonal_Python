from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

faturamento = 0
lucro = 0
for pid, p in InventoryManager._mapaProdutos.items():
    faturamento += p.get('valorTotalVendas', 0)
    lucro += p.get('valorTotalLucro', 0)

print(f"Faturamento _mapaProdutos: {faturamento}")
print(f"Lucro _mapaProdutos: {lucro}")
