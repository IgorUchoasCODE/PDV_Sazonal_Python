import sys
import os
import json
from datetime import date

# Adiciona a raiz do projeto ao sys.path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from br.com.pdv.src.pessoa.empresa import Empresa
from br.com.pdv.src.pessoa.fornecedor import Fornecedor
from br.com.pdv.src.financeiro.notaCompra import NotaCompra
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida

def formatar_dict(d):
    return json.dumps(d, indent=4, ensure_ascii=False)

def main():
    print("="*70)
    print(" INICIANDO TESTES DE INTEGRAÇÃO: NOTA COMPRA & FORNECEDOR ")
    print("="*70)

    # ---------------------------------------------------------
    # Passo 1: Criação de Empresa
    # ---------------------------------------------------------

    print("\n[PASSO 1] Criando a Empresa (Distribuidora X)...")

    empresa_x = Empresa(id="1", nome="Distribuidora X")
    
    print(f" -> Empresa criada: {empresa_x.info()['nome']}")

    # ---------------------------------------------------------
    # Passo 2: Criação de Fornecedor
    # ---------------------------------------------------------
    print("\n[PASSO 2] Criando Fornecedor a partir da Empresa...")
    fornecedor = Fornecedor(id=1, tipoFornecedor=empresa_x)
    print(f" -> Fornecedor criado. Dados iniciais:\n{formatar_dict(fornecedor.getDados())}")

    # ---------------------------------------------------------
    # Passo 3: Criação de Produtos
    # ---------------------------------------------------------
    print("\n[PASSO 3] Criando Produtos para inserir na nota...")
    produto1 = Produto(id=1, nome="Refrigerante Lata", durabilidade=180, unidadeMedida=UnidadeMedida.UNIDADE)
    produto1.insertPropertValue(valorUnidario="3.50", quantidade="100") # Custo: 3.50, Qtd: 100

    produto2 = Produto(id=2, nome="Fardo de Arroz 5kg", durabilidade=365, unidadeMedida=UnidadeMedida.UNIDADE)
    produto2.insertPropertValue(valorUnidario="20.00", quantidade="50") # Custo: 20.00, Qtd: 50

    print(" -> Produtos instanciados com sucesso.")

    # ---------------------------------------------------------
    # Passo 4: Criação da Nota de Compra
    # ---------------------------------------------------------
    print("\n[PASSO 4] Criando Nota de Compra vinculada ao Fornecedor...")
    nota1 = NotaCompra(id=1001, fornecedor=fornecedor, dataEmissao=date.today())
    print(" -> Nota de Compra 1001 criada.")

    # ---------------------------------------------------------
    # Passo 5: Adicionando Produtos na Nota
    # ---------------------------------------------------------
    print("\n[PASSO 5] Adicionando produtos na Nota de Compra...")
    nota1.adicionarProduto(produto1, tipo=1)
    nota1.adicionarProduto(produto2, tipo=1)
    print(f" -> Quantidade de produtos atuais na nota: {len(nota1.getProdutos())}")

    # ---------------------------------------------------------
    # Passo 6: Vinculando a Nota ao Fornecedor
    # ---------------------------------------------------------
    print("\n[PASSO 6] Adicionando a nota ao controle interno do Fornecedor...")
    fornecedor.adicionarNotaCompra(nota1)
    print(f" -> Quantidade de notas cadastradas no Fornecedor: {len(fornecedor.getNotasCompra())}")

    # ---------------------------------------------------------
    # Passo 7: Simulando Vendas
    # ---------------------------------------------------------
    print("\n[PASSO 7] Realizando vendas de alguns produtos da nota...")
    # Pega as chaves compostas (ex: "1.1.0") geradas pelo IdClassFactory que estão no getDados da nota
    chaves_nota = list(nota1.getDados()["produtos"].keys())
    id_composto_p1 = chaves_nota[0]
    id_composto_p2 = chaves_nota[1]

    print(f" -> Vendendo 20 unidades de {produto1.getDados()['nome']} a R$ 5.00/un (Id na nota: {id_composto_p1})")
    nota1.venderProduto(idProduto=id_composto_p1, valorVenda="5.00", quantidadeVenda="20")

    print(f" -> Vendendo 10 unidades de {produto2.getDados()['nome']} a R$ 25.00/un (Id na nota: {id_composto_p2})")
    nota1.venderProduto(idProduto=id_composto_p2, valorVenda="25.00", quantidadeVenda="10")

    # ---------------------------------------------------------
    # Passo 8: Aplicar Descontos
    # ---------------------------------------------------------
    print("\n[PASSO 8] Aplicando um desconto de R$ 50.00 no total da nota...")
    nota1.aplicarDesconto("50.00")

    # ---------------------------------------------------------
    # Passo 9: Status Antes de Salvar
    # ---------------------------------------------------------
    print("\n[PASSO 9] Verificando Totais Globais do Fornecedor ANTES de salvar a nota:")
    print(formatar_dict(Fornecedor.getDadosGlobais()))
    print(f" -> A nota está salva? {nota1.getDados()['salvo']}")

    # ---------------------------------------------------------
    # Passo 10: Salvando a Nota
    # ---------------------------------------------------------
    print("\n[PASSO 10] Chamando o método 'salvar()' na nota...")
    nota1.salvar()
    print(f" -> A nota está salva? {nota1.getDados()['salvo']}")

    # ---------------------------------------------------------
    # Passo 11: Totais da Nota Após Salvar
    # ---------------------------------------------------------
    print("\n[PASSO 11] Dados financeiros da Nota COMPRA 1001 APÓS salvar:")
    dados_nota = nota1.getDados()
    print(f" -> Custo Bruto (valorTotal): R$ {dados_nota['valorTotal']}")
    print(f" -> Desconto:                 R$ {dados_nota['desconto']}")
    print(f" -> Custo Liquido (Final):    R$ {dados_nota['valorFinal']}")
    print(f" -> Valor Total Vendido:      R$ {dados_nota['valorTotalVenda']}")
    print(f" -> Lucro das vendas:         R$ {dados_nota['lucroTotal']}")

    # ---------------------------------------------------------
    # Passo 12: Status do Fornecedor Após Salvar
    # ---------------------------------------------------------
    print("\n[PASSO 12] Totais Individuais do Fornecedor APÓS salvar a nota:")
    print(formatar_dict(fornecedor.getDados()))

    # ---------------------------------------------------------
    # Passo 13: Totais Globais
    # ---------------------------------------------------------
    print("\n[PASSO 13] Totais Globais e Estáticos (Contabilidade do Sistema):")
    print(formatar_dict(Fornecedor.getDadosGlobais()))

  

if __name__ == '__main__':
    main()
