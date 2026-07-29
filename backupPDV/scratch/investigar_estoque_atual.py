import sys
import sqlite3
sys.path.append(".")

from br.com.pdv.src.memory.inventoryManager import InventoryManager
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory

# Reconstrói o estado do estoque a partir do banco principal
InventoryManager.carregarTudo()

print("="*80)
print("POSIÇÃO DO ESTOQUE EM MEMÓRIA (InventoryManager._mapaProdutos):")
print("="*80)

for prod_id in range(1, 11):
    id_str = str(prod_id)
    info = InventoryManager._mapaProdutos.get(id_str, {})
    prod_obj = ProductClassFactory.fabricar(prod_id)
    nome = prod_obj.getDados().get("nome") if prod_obj else f"Produto {prod_id}"
    
    qtd_tot = info.get("quantidadeTotal", 0.0)
    val_tot = info.get("valorTotalEstoque", 0.0)
    custo_med = info.get("custoMedio", 0.0)
    lotes_qtd = len(info.get("lotes", []))
    
    print(f"ID {prod_id:2d} | {nome:35s} | Qtd Estoque: {qtd_tot:10.2f} | Valor Total: R$ {val_tot:10.2f} | Custo Médio: R$ {custo_med:8.2f} | Lotes: {lotes_qtd}")

print("="*80)
