from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

# Calculate totals directly from InventoryManager's loaded notes
total_vendas = 0
total_lucro = 0
for nota in InventoryManager._NotasVendas:
    total_vendas += nota.valorTotal
    total_lucro += nota.lucroTotal

print(f"Total Vendas via InventoryManager: {total_vendas}")
print(f"Total Lucro via InventoryManager: {total_lucro}")
