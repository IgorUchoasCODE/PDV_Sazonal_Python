import sqlite3
c = sqlite3.connect('databaseSazonalizei.db')
cursor = c.cursor()
cursor.execute('SELECT SUM(receita_total), SUM(lucro_total) FROM vw_resumo_vendas_produto')
print("From vw_resumo_vendas_produto:", cursor.fetchone())
