from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

print("--- NOTAS DE COMPRA CARREGADAS ---")
for nota in InventoryManager._NotasCompras:
    dados = nota.getDados()
    for key, prod in dados.get("produtos", {}).items():
        print(dados.get("id"), key, prod)
