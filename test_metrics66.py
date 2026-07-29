import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
c.row_factory = sqlite3.Row
cursor = c.cursor()

cursor.execute('''
    SELECT 
        DATE(f.data) as dia,
        STRFTIME('%Y-%m', f.data) as mes_ano,
        SUM(CASE WHEN f.id_tipoNota = 2 THEN ABS(f.quantidade) * f.valorUnidario ELSE 0 END) as valor_venda,
        SUM(CASE WHEN f.id_tipoNota = 2 THEN f.lucroTotal ELSE 0 END) as lucro_venda,
        SUM(CASE WHEN f.id_tipoNota = 4 THEN ABS(f.quantidade) * f.valorUnidario ELSE 0 END) as valor_perda,
        MAX(s.nivel_rio_atual) as nivel_rio,
        MAX(s.temperatura_atual) as temperatura,
        COALESCE(MAX(s.indicador_clima), 'AMENO') as clima
    FROM fluxoEstoque f
    LEFT JOIN snapshot_sazonal s ON s.id_fluxo_nota = f.id_fluxo_nota
    GROUP BY DATE(f.data)
    ORDER BY DATE(f.data) ASC
''')

rows = [dict(r) for r in cursor.fetchall()]
print(f"Total registros por dia: {len(rows)}")

# Agrupando por Mês
meses = {}
for r in rows:
    m = r['mes_ano']
    if m not in meses:
        meses[m] = {'vendas': 0, 'perdas': 0}
    meses[m]['vendas'] += r['valor_venda']
    meses[m]['perdas'] += r['valor_perda']

for m, val in meses.items():
    print(f"Mês {m}: Vendas = R$ {val['vendas']:.2f} | Perdas = R$ {val['perdas']:.2f}")
