from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()
tend = InventoryManager.analisar_tendencias_sazonais()
print("NOVA TEMP MEDIA IDEAL:", tend.get('indicadores', {}).get('temperatura_media_vendas'))
print("ALERTAS:", tend.get('alertas'))
