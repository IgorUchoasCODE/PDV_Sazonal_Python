from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
tendencias = InventoryManager.analisar_tendencias_sazonais()
print(tendencias.get('produtos_negativos'))
