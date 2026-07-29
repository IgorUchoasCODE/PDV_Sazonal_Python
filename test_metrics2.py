from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
if len(InventoryManager._NotasVendas) > 0:
    nota = list(InventoryManager._NotasVendas)[0]
    print(dir(nota))
