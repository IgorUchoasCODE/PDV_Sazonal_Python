import sys
import os
import json
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from br.com.pdv.src.financeiro.notaPerda import NotaPerda
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida

def formatar_dict(d):
    return json.dumps(d, indent=4, ensure_ascii=False, default=str)

def main():
    print("="*70)
    print(" TESTE: NOTA PERDA ")
    print("="*70)

    produto1 = Produto(id=1, nome="Tomate", diasDuraveis=7, unidadeMedida=UnidadeMedida.KG)
    # Simulando perda de 5 kgs no estoque
    produto1.insertPropertValue(valorUnidario="3.00", quantidade="5")
    
    nota = NotaPerda(id=3001, id_nota_origem=1001, tipo_origem="ESTOQUE", dataEmissao=date.today())
    nota.adicionarProduto(produto1)
    
    nota.salvar()
    
    print("\nDados da Nota Perda:")
    print(formatar_dict(nota.getDados()))

if __name__ == '__main__':
    main()
