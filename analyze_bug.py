import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sazonal_web.settings')
django.setup()
from br.com.pdv.src.BDD.bancodb import BancoDB

# ANÁLISE DO BUG
# Produto 113 (CARVÃO BRINQUETE) varejo = R$4.00 (preço de venda)
# Receita: 1.25 kg CARVÃO PÓ + 0.25 kg GLUTINANTE + 2 L ÁGUA
# Custo real de compra dos ingredientes:
#   CARVÃO PÓ:  custo_medio = 0.11/kg  → 1.25 * 0.11 = 0.1375
#   GLUTINANTE: custo_medio = 0.35/kg  → 0.25 * 0.35 = 0.0875
#   ÁGUA:       custo_medio = 1.28/L   → 2.00 * 1.28 = 2.5600
#   CUSTO TOTAL REAL = 0.1375 + 0.0875 + 2.56 = 2.785
#   LUCRO REAL = 4.00 - 2.785 = 1.215

# O QUE ACONTECEU ERRADO:
# valorUnidario foi salvo como 4 (o preço de venda do composto) para TODOS os ingredientes
# Em vez do custo real de cada lote/ingrediente
# Lucro = 1.3333 × 3 linhas = 4.0 → ou seja, lucro = 100% do valor de venda

with BancoDB.obter_conexao() as conn:
    cur = conn.cursor()
    # Checar o custo do lote real na nota 927 (nota de compra origem)
    cur.execute('''
        SELECT fe.id_produto, p.nome, fe.quantidade, fe.valorUnidario, fe.id_fluxo_nota, fn.id_tipoNota
        FROM fluxoEstoque fe
        JOIN produto p ON p.id = fe.id_produto
        JOIN fluxosNotasEstoque fn ON fn.id = fe.id_fluxo_nota
        WHERE fe.id_fluxo_nota = 927 AND fe.id_produto IN (110, 111, 112)
    ''')
    print('LOTES DA NOTA DE COMPRA 927:')
    for r in cur.fetchall():
        d = dict(r)
        print(f"  prod={d['id_produto']} ({d['nome']}) | qtd={d['quantidade']} | valorUnit={d['valorUnidario']} | tipoNota={d['id_tipoNota']}")

    # Verificar _mapaEstoque para entender como o custo é lido no FIFO
    # O problema está em que custo_unitario no lote = custo de compra
    # Mas na hora de calcular val_venda_banco, ele está usando errado
    
    # Reconstituir o cálculo que DEVERIA ter acontecido:
    # qtd_vendida_brinquete = 1 unidade
    # Para cada ingrediente:
    #   CARVÃO PÓ (110): qtd_por_un=1.25 → qtd_total=1.25 → custo_lote = 1.25 * 0.11 = 0.1375
    #   GLUTINANTE (111): qtd_por_un=0.25 → qtd_total=0.25 → custo_lote = 0.25 * 0.35 = 0.0875
    #   ÁGUA (112): qtd_por_un=2.0 → qtd_total=2.0 → custo_lote = 2.0 * 1.28 = 2.56
    #   custo_total = 2.785
    #   valor_venda_brinquete = R$4.00
    #   lucro_total = 4.00 - 2.785 = 1.215
    
    # Distribuição proporcional por ingrediente:
    #   CARVÃO PÓ:  parcela = (0.1375 / 2.785) * 4.00 = 0.1975 → lucro = 0.1975 - 0.1375 = 0.06
    #   GLUTINANTE: parcela = (0.0875 / 2.785) * 4.00 = 0.1257 → lucro = 0.1257 - 0.0875 = 0.038
    #   ÁGUA:       parcela = (2.56   / 2.785) * 4.00 = 3.677  → lucro = 3.677 - 2.56 = 1.117
    #   total lucro = 0.06 + 0.038 + 1.117 = 1.215 ✓
    
    custo = {'CARVÃO PÓ': (1.25, 0.11), 'GLUTINANTE': (0.25, 0.35), 'ÁGUA': (2.0, 1.28)}
    val_venda = 4.0
    custo_total = sum(qtd * c for qtd, c in custo.values())
    print(f'\nCUSTO TOTAL INGREDIENTES: R$ {custo_total:.4f}')
    print(f'VALOR VENDA BRINQUETE: R$ {val_venda:.4f}')
    print(f'LUCRO REAL: R$ {val_venda - custo_total:.4f}')
    print(f'MARGEM REAL: {(val_venda - custo_total) / val_venda * 100:.1f}%')
    
    print('\nDISTRIBUIÇÃO CORRETA POR INGREDIENTE (proporcional ao custo):')
    for nome, (qtd, custo_unit) in custo.items():
        custo_ingr = qtd * custo_unit
        # parcela do valor de venda proporcional ao CUSTO (não à quantidade física)
        parcela_venda = (custo_ingr / custo_total) * val_venda if custo_total > 0 else 0
        lucro_ingr = parcela_venda - custo_ingr
        val_unit_banco = parcela_venda / qtd if qtd > 0 else 0
        print(f"  {nome}: qtd={qtd} | custo_unit={custo_unit:.4f} | custo_total={custo_ingr:.4f} | parcela_venda={parcela_venda:.4f} | lucro={lucro_ingr:.4f} | valorUnit_banco={val_unit_banco:.4f}")
