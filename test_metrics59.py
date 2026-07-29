from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

print("--- MAPA PRODUTOS EM INVENTORYMANAGER ---")
for pid, mapa in InventoryManager._mapaProdutos.items():
    print(f"ID {pid} | quantidadeTotal: {mapa.get('quantidadeTotal')} | totalCompras: {mapa.get('totalCompras')} | totalVendas: {mapa.get('totalVendas')} | totalPerdas: {mapa.get('totalPerdas')}")
