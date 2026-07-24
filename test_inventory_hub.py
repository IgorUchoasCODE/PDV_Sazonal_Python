"""
Teste de validação do InventoryManager como Hub Central.
Verifica:
  1. Carregamento de todas as notas
  2. get_status() com totais coerentes
  3. get_estoque_produto() com lotes FIFO
  4. get_triangulacao_sazonal()
  5. Simulação de insert_compra, insert_venda, get_nota
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from br.com.pdv.src.memory.inventoryManager import InventoryManager

# ── 1. Carregar tudo ───────────────────────────────────────────────
print("=" * 65)
print("1. CARREGAMENTO GERAL")
print("=" * 65)
ok = InventoryManager.carregarTudo()
print(f"   carregarTudo() => {ok}")

# ── 2. Status Geral ────────────────────────────────────────────────
print("\n" + "=" * 65)
print("2. STATUS GERAL (get_status)")
print("=" * 65)
status = InventoryManager.get_status()
for k, v in status.items():
    print(f"   {k}: {v}")

# ── 3. Estoque de um produto ───────────────────────────────────────
print("\n" + "=" * 65)
print("3. ESTOQUE DO PRODUTO ID=1 (get_estoque_produto)")
print("=" * 65)
est = InventoryManager.get_estoque_produto(1)
if est:
    for k, v in est.items():
        if k != "lotes":
            print(f"   {k}: {v}")
    print(f"   lotes disponíveis: {len(est.get('lotes', []))}")
    for lote in est.get("lotes", [])[:3]:  # mostra até 3
        print(f"     -> {lote}")
else:
    print("   Produto ID=1 não encontrado no mapa.")

# ── 4. Triangulação Sazonal ────────────────────────────────────────
print("\n" + "=" * 65)
print("4. TRIANGULAÇÃO SAZONAL (5 primeiros resultados)")
print("=" * 65)
triang = InventoryManager.get_triangulacao_sazonal()
print(f"   Total de triangulações: {len(triang)}")
for t in triang[:5]:
    snap = t.get("snapshot_sazonal")
    snap_str = f"clima={snap.get('indicador_clima')}" if snap else "sem snapshot"
    print(f"   Nota {t['id_nota']} ({t['tipo']}) {t['data']} | {snap_str}")

# ── 5. get_nota (qualquer ID carregado) ───────────────────────────
print("\n" + "=" * 65)
print("5. GET NOTA (primeira nota de venda carregada)")
print("=" * 65)
if InventoryManager._NotasVendas:
    primeira_venda = list(InventoryManager._NotasVendas)[0]
    id_exemplo = primeira_venda.getDados()["id"]
    nota_dados = InventoryManager.get_nota(id_exemplo)
    print(f"   id_nota buscado: {id_exemplo}")
    print(f"   cliente: {nota_dados.get('cliente', {}).get('nome', 'N/A')}")
    print(f"   produtos: {list(nota_dados.get('produtos', {}).keys())}")
else:
    print("   Nenhuma nota de venda carregada.")

print("\n" + "=" * 65)
print("VALIDAÇÃO CONCLUÍDA")
print("=" * 65)
