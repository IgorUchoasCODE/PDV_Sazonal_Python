from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
if len(InventoryManager._mapaEstoque) > 0:
    first_key = list(InventoryManager._mapaEstoque.keys())[0]
    print(InventoryManager._mapaEstoque[first_key])
else:
    print('Estoque vazio')
