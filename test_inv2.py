from br.com.pdv.src.memory.inventoryManager import InventoryManager

InventoryManager.carregarTudo()
for k, v in InventoryManager._mapaProdutos.items():
    print(f"ID: {k}, keys: {v.keys()}, Qty: {v.get('quantidadeTotal')}")
