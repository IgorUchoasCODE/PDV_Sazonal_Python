import pandas as pd
df = pd.read_excel('servidor.xlsx')
vendas = df[df['id_tipoNota'] == 2]

# Ensure we're calculating revenue correctly
total_revenue = 0
for _, row in vendas.iterrows():
    if pd.isna(row['Valor Total']):
        total_revenue += row['Quantidade'] * row['Valor Unitario']
    else:
        total_revenue += row['Valor Total']
        
print("Excel Faturamento:", total_revenue)
