from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
try:
    print("Tendencias:", InventoryManager.analisar_tendencias_sazonais())
except Exception as e:
    print("Erro:", e)
