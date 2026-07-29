from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

total_vendas = 0
total_lucro = 0
for nota in InventoryManager._NotasVendas:
    dados = nota.getDados()
    total_vendas += dados['valorTotal']
    total_lucro += dados['lucroTotal']

print(f"Total Vendas via InventoryManager: {total_vendas}")
print(f"Total Lucro via InventoryManager: {total_lucro}")
