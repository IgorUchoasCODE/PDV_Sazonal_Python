from br.com.pdv.src.memory.inventoryManager import InventoryManager

InventoryManager.carregarTudo()
print("1st call:", {k: v['quantidadeTotal'] for k, v in InventoryManager._mapaProdutos.items()})

InventoryManager.carregarTudo()
print("2nd call:", {k: v['quantidadeTotal'] for k, v in InventoryManager._mapaProdutos.items()})

InventoryManager.carregarTudo()
print("3rd call:", {k: v['quantidadeTotal'] for k, v in InventoryManager._mapaProdutos.items()})
