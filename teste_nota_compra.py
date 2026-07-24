import sys
import os
import json
from datetime import date

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from br.com.pdv.src.pessoa.empresa import Empresa
from br.com.pdv.src.pessoa.fornecedor import Fornecedor
from br.com.pdv.src.financeiro.notaCompra import NotaCompra
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida

def formatar_dict(d):
    return json.dumps(d, indent=4, ensure_ascii=False, default=str)

def main():
    print("="*70)
    print(" TESTE: NOTA COMPRA & FORNECEDOR ")
    print("="*70)

    empresa = Empresa(id="1", nome="Distribuidora X")
    fornecedor = Fornecedor(id=1, tipoFornecedor=empresa)
    
    produto1 = Produto(id=1, nome="Refrigerante Lata", diasDuraveis=180, unidadeMedida=UnidadeMedida.UNIDADE)
    produto1.insertPropertValue(valorUnidario="3.50", quantidade="100")

    produto2 = Produto(id=2, nome="Refrigerante", diasDuraveis=180, unidadeMedida=UnidadeMedida.UNIDADE)
    produto2.insertPropertValue(valorUnidario="4.00", quantidade="50")
    
    nota = NotaCompra(id=1001, fornecedor=fornecedor, dataEmissao=date.today())
    nota.adicionarProduto(produto1, tipo=1)
    nota.adicionarProduto(produto2, tipo=1)
    
    fornecedor.adicionarNotaCompra(nota)
    
    chaves = list(nota.getDados()["produtos"].keys())
    if chaves:
        nota.venderProduto(idProduto=chaves[0], valorVenda="5.00", quantidadeVenda="20")
    
    nota.aplicarDesconto("50.00")
    nota.salvar()
    
    print("\nDados da Nota Compra (Após Salvar):")
    print(formatar_dict(nota.getDados()))
    print("\nTotal Global Fornecedor:")
    print(formatar_dict(Fornecedor.getDadosGlobais()))

if __name__ == '__main__':
    main()
