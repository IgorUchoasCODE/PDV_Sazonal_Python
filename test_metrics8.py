from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
print("Metodos:", [m for m in dir(InventoryManager) if not m.startswith('_')])
