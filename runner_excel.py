import os
import sys
import pandas as pd
from datetime import datetime
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from br.com.pdv.src.BDD.bancodb import BancoDB
from br.com.pdv.src.memory.inventoryManager import InventoryManager
from br.com.pdv.src.memory.paymentManager import PaymentManager
from br.com.pdv.src.apis.gerenciadorSazonal import GerenciadorSazonal

MAP_PROD = {
    'OVO BRANCO A': 1,
    'OVO BRANCO B': 2,
    'OVO BRANCO C': 3,
    'OVO BRANCO EXTRA': 4,
    'OVO BRANCO JUMBO': 5
}

MAP_FORNECEDORES = {
    'Ovos de ouro': 4,
    'Gema De Ouro': 5,
    'Granja Marinho': 6
}

def parse_money(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).replace('R$', '').replace('-R$', '-').replace(' ', '').replace('.', '').replace(',', '.')
    if s == '-' or not s: return 0.0
    try:
        return float(s)
    except:
        return 0.0

def format_date(val):
    if pd.isna(val): return '2026-01-01'
    if isinstance(val, pd.Timestamp) or hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, str):
        if '/' in val:
            parts = val.split('/')
            if len(parts) >= 2:
                day, month = parts[0], parts[1]
                return f"2026-{int(month):02d}-{int(day):02d}"
        if len(val) >= 10:
            return val[:10]
    return '2026-01-01'

def parse_date_obj(val):
    s = format_date(val)
    return datetime.strptime(s, '%Y-%m-%d')

def processar_excel():
    print("=" * 90)
    print("  INICIANDO GRAVACAO: LENDO EXCLUSIVAMENTE temp_gestao.xlsm")
    print("=" * 90)
    
    # 1. Limpa e reinicia o banco
    conn = BancoDB.obter_conexao()
    conn.execute('DROP TABLE IF EXISTS fluxoEstoque')
    conn.execute('DROP TABLE IF EXISTS fluxosNotasEstoque')
    conn.execute('DROP TABLE IF EXISTS fluxoPagamentoNotas')
    conn.execute('DROP TABLE IF EXISTS snapshot_sazonal')
    conn.commit()
    BancoDB.inicializar_banco()
    InventoryManager.carregarTudo()
    
    # 2. Le a planilha
    print("[1/5] Carregando temp_gestao.xlsm...")
    df = pd.read_excel('temp_gestao.xlsm', sheet_name='estoque', skiprows=13)
    
    compras_dict = defaultdict(list)
    operacoes = []
    
    for idx, row in df.iterrows():
        tipo = str(row.iloc[0]).strip()
        if pd.isna(row.iloc[1]):
            continue
            
        produto_str = str(row.iloc[1]).strip()
        if produto_str.lower() == 'produto':
            continue
            
        id_produto = MAP_PROD.get(produto_str)
        if id_produto is None:
            continue
            
        try:
            qtd = float(str(row.iloc[2]).replace(',', '.'))
        except:
            continue
            
        lucro_str = str(row.iloc[8]) if len(row) > 8 else "0"
        lucro = parse_money(lucro_str)
        data_op_str = format_date(row.iloc[5])
        data_op_obj = parse_date_obj(row.iloc[5])
        
        # Identifica o fornecedor
        is_forn = False
        for f, id_forn in MAP_FORNECEDORES.items():
            if tipo.lower().startswith(f.lower()):
                is_forn = True
                
                val_total = parse_money(row.iloc[4]) if len(row) > 4 else 0.0
                val_un = val_total / (qtd/12) if qtd > 0 else 0.0
                
                # Agrupa compras por data e fornecedor
                chave_compra = (data_op_str, id_forn)
                compras_dict[chave_compra].append({
                    "id": id_produto,
                    "quantidade": qtd/12,
                    "valorUnidario": val_un
                })
                break
                
        if not is_forn and (tipo.lower().startswith('saída') or tipo.lower().startswith('saida')):
            if lucro < 0 or '-R$' in lucro_str:
                payload = {
                    "tipo": "perda",
                    "dados": {
                        "id_nota_origem": 0,
                        "produtos": [{"id": id_produto, "quantidade": (qtd/12)}],
                        "data": data_op_str
                    }
                }
                operacoes.append({"data_raw": data_op_obj, "payload": payload})
            else:
                val_total_sheet = parse_money(row.iloc[4]) if len(row) > 4 else 0.0
                if val_total_sheet == 0.0:
                    val_un_sheet = parse_money(row.iloc[3]) if len(row) > 3 else 0.0
                    val_total_sheet = val_un_sheet * qtd
                
                val_un = val_total_sheet / qtd if qtd > 0 else 0.0

                payload = {
                    "tipo": "venda",
                    "dados": {
                        "id_cliente": 1,
                        "produtos": [{"id": id_produto+5, "quantidade": qtd, "valorVenda": val_un}],
                        "data": data_op_str
                    },
                    "valor_total": val_un * qtd
                }
                operacoes.append({"data_raw": data_op_obj, "payload": payload})

    # Adiciona as compras agrupadas na lista de operações
    for (data_str, id_forn), produtos in compras_dict.items():
        data_obj = datetime.strptime(data_str, '%Y-%m-%d')
        payload = {
            "tipo": "compra",
            "dados": {
                "id_fornecedor": id_forn,
                "produtos": produtos,
                "data": data_str
            }
        }
        operacoes.append({"data_raw": data_obj, "payload": payload})

    # Separa as operações por tipo para processar Compras primeiro (garantindo saldo de estoque)
    op_compras = [op for op in operacoes if op["payload"]["tipo"] == "compra"]
    op_perdas = [op for op in operacoes if op["payload"]["tipo"] == "perda"]
    op_vendas = [op for op in operacoes if op["payload"]["tipo"] == "venda"]
    
    op_compras.sort(key=lambda x: x["data_raw"])
    op_perdas.sort(key=lambda x: x["data_raw"])
    op_vendas.sort(key=lambda x: x["data_raw"])

    # A nova ordem de processamento
    operacoes_ordenadas = op_compras + op_perdas + op_vendas

    last_inserted_nota_id = None
    sucessos = 0
    erros = 0
    
    saldo_caixa = 0.0
    dividas = []

    print(f"\n[2/5] Inserindo {len(operacoes_ordenadas)} operacoes ordenadas (Compras -> Perdas -> Vendas)...")
    for op in operacoes_ordenadas:
        data_str = op["data_raw"].strftime('%Y-%m-%d')
        tipo_op = op["payload"]["tipo"]
        
        if tipo_op == "compra":
            dados = op["payload"]["dados"]
            nota = InventoryManager.insert_compra(dados)
            if nota:
                id_nota = nota.getDados().get("id")
                last_inserted_nota_id = id_nota
                sucessos += 1
                total_compra = sum(p["quantidade"] * p["valorUnidario"] for p in dados["produtos"])
                dividas.append({"id_fluxo_nota": id_nota, "restante": total_compra})
                print(f" -> Compra inserida: Data {data_str} | Nota ID: {id_nota} | Valor: R$ {total_compra:.2f}")
                
        elif tipo_op == "perda":
            dados = op["payload"]["dados"]
            nota = InventoryManager.insert_perda(dados)
            if nota:
                id_nota = nota.getDados().get("id")
                last_inserted_nota_id = id_nota
                sucessos += 1
                print(f" -> Perda inserida: Data {data_str} | Nota ID: {id_nota}")
            else:
                erros += 1
                
        elif tipo_op == "venda":
            dados = op["payload"]["dados"]
            valor_total = op["payload"]["valor_total"]
            nota = InventoryManager.insert_venda(dados)
            if nota:
                id_nota = nota.getDados().get("id")
                last_inserted_nota_id = id_nota
                sucessos += 1
                print(f" -> Venda inserida: Data {data_str} | Nota ID: {id_nota} | Valor: R$ {valor_total:.2f}")
                
                # Pagamento e acerto de caixa
                if valor_total > 0:
                    pay_payload = {
                        "id_venda": id_nota,
                        "data_pagamento": data_str,
                        "id_tipo_pagamento": 1,
                        "valor": valor_total
                    }
                    PaymentManager.registrar_pagamento(pay_payload)
                    saldo_caixa += valor_total
                    
                    # Tenta pagar as dívidas com o caixa existente
                    for d in dividas:
                        if d["restante"] > 0 and saldo_caixa > 0:
                            pagamento = min(saldo_caixa, d["restante"])
                            pay_forn_payload = {
                                "id_fluxo_nota": d["id_fluxo_nota"],
                                "data_pagamento": data_str,
                                "id_tipo_pagamento": 1,
                                "valor": pagamento
                            }
                            PaymentManager.registrar_pagamento(pay_forn_payload)
                            d["restante"] -= pagamento
                sucessos += 1
                print(f" -> Perda inserida: Data {data_str} | Nota ID: {last_inserted_nota_id}")
            else:
                erros += 1

    print(f"\n[5/5] Finalizando importação...\n")
    print("\n" + "=" * 90)
    print(f"  PROCESSAMENTO CONCLUIDO | Operacoes: {sucessos} | Erros: {erros}")
    print(f"  SALDO EM CAIXA SOBRANTE: R$ {saldo_caixa:.2f}")
    print("=" * 90 + "\n")
    
    conn = BancoDB.obter_conexao()
    query = '''
    SELECT 
        p.nome, 
        SUM(CASE WHEN f.id_tipoNota IN (1, 3) THEN f.quantidade ELSE -f.quantidade END) as Estoque
    FROM fluxoEstoque f
    JOIN produto p ON f.id_produto = p.id
    GROUP BY p.nome
    ORDER BY p.nome
    '''
    print("--- SALDO FINAL NO BANCO DE DADOS (em cartelas) ---")
    for row in conn.execute(query):
        print(f"{row[0]}: {row[1]} cartelas ({row[1]/12:.2f} caixas)")

if __name__ == "__main__":
    processar_excel()
