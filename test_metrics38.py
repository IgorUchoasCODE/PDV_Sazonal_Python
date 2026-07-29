from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
for pid, pdata in InventoryManager._mapaProdutos.items():
    print(pid, type(pid), pdata.keys(), pdata.get('nome'))
