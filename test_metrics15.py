import pandas as pd
df = pd.read_excel('temp_gestao.xlsm', sheet_name='estoque', skiprows=13, usecols="B:J")
df.columns = [
    'data', 'tipo', 'representante', 'id_produto', 'nome_produto', 
    'Unidade', 'Quantidade', 'Valor Unitario', 'Valor Total'
]
vendas = df[df['tipo'] == 'Saida']
total_revenue = 0
for _, row in vendas.iterrows():
    if pd.isna(row['Valor Total']):
        total_revenue += row['Quantidade'] * row['Valor Unitario']
    else:
        total_revenue += row['Valor Total']
print("Excel Faturamento Real:", total_revenue)
