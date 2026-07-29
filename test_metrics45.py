from br.com.pdv.src.memory.inventoryManager import InventoryManager
InventoryManager.carregarTudo()

print("--- NOTAS DE VENDA CARREGADAS ---")
for nota in InventoryManager._NotasVendas:
    dados = nota.getDados()
    for key, prod in dados.get("produtos", {}).items():
        print(dados.get("id"), key, prod)
