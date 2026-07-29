from br.com.pdv.src.memory.inventoryManager import InventoryManager

InventoryManager.carregarTudo()
for k, v in InventoryManager._mapaProdutos.items():
    print(f"ID: {k}, Qty: {v['quantidadeTotal']}, Tipo: {v['id_tipo']}")
