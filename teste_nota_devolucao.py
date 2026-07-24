import sys
import os
import json
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.cliente import Cliente
from br.com.pdv.src.registro.sexo import Sexo
from br.com.pdv.src.financeiro.notaDevolucao import NotaDevolucao
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida

def formatar_dict(d):
    return json.dumps(d, indent=4, ensure_ascii=False, default=str)

def main():
    print("="*70)
    print(" TESTE: NOTA DEVOLUÇÃO & CLIENTE ")
    print("="*70)

    pessoa = Pessoa(id="1", nome="João da Silva", sexo=Sexo.MASCULINO)
    cliente = Cliente(id=1, tipoCliente=pessoa)
    
    produto1 = Produto(id=1, nome="Cerveja", diasDuraveis=180, unidadeMedida=UnidadeMedida.UNIDADE)
    # Simulando devolução de 10 unidades
    produto1.insertPropertValue(valorUnidario="4.00", quantidade="10")
    
    nota = NotaDevolucao(id=2001, clienteFornecedor=cliente, id_nota_venda_origem=1001, dataEmissao=date.today())
    nota.adicionarProduto(produto1)
    
    nota.salvar()
    
    print("\nDados da Nota Devolução:")
    print(formatar_dict(nota.getDados()))
    print("\nDados do Cliente após Devolução (Contabilidade Atualizada):")
    print(formatar_dict(cliente.getDados()))

if __name__ == '__main__':
    main()
