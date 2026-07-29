from br.com.pdv.src.financeiro.nota import ComportamentoNota
from br.com.pdv.src.pessoa.fornecedor import Fornecedor
from br.com.pdv.src.memory.idClassFactory import IdClassFactory
from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union
from datetime import date

class NotaCompra(ComportamentoNota):
    
    ''' essa classe representa a nota de entrada e contem as instancias dos produtos e suas proprieadades serão armazenas aqui
    assim como os valores de vendas e compras referente a essa nota'''

    
    def __init__(self,id:int,
                fornecedor: Union[Fornecedor, Pessoa], 
                dataEmissao:date=date.today(),
                dataVencimento:date=None):        
        try:

            if int(id) <= 0:
                raise ValueError("O id deve ser maior que zero")
            
            if fornecedor is None:
                raise ValueError("O fornecedor deve ser informado")

            if not isinstance(fornecedor, (Fornecedor, Pessoa)):
                raise ValueError("O fornecedor deve ser uma instancia de Fornecedor ou Pessoa")

            if not isinstance(dataEmissao, date):
                raise ValueError("A data de emissão deve ser uma instancia de date")

            if not isinstance(dataVencimento, date) and dataVencimento is not None:
                raise ValueError("A data de vencimento deve ser uma instancia de date")

        except ValueError as e:
            print(f" Erro na inicialização do objeto NotaCompra: {e}")
            return
        
        #propriedades de identificação  
        self.__I = id
        self.__F = fornecedor
        self.__dataE = dataEmissao
        self.__dataV = dataVencimento

        #listas e dicionarios para armazena os produtos
        self.__produtos: dict[str, Produto] = {}

        #propriedades de valor da nota (custo de compra)
        self.__valorTotal = 0
        self.__desconto = 0
        self.__acrescimo = 0
        self.__valorFinal = 0

        #propriedades de venda dos produtos dessa nota 
        self.__valorTotalVenda = 0
        self.__lucroTotal = 0

        # flag que indica se a nota foi salva (os totais estão atualizados)
        self.__salvo = False
        

    
    def adicionarProduto(self, produto:Produto, tipo:int|str=1, teste:bool=False)-> bool:
        '''qualquer produto que seja inserido nesta nota só pode ter sua quantidade alterada na classe produto  
        e só pode ser produto puro, quando não há necessidade de dicionario ou depedencia de outro produto
        de por o id do tipo de entrada 1 normal, 2 reposição, 3 bonificação '''
        
        p = produto
        t = tipo
        lp = self.__produtos

        try:

            if not isinstance(p, Produto):
                raise ValueError("O produto deve ser uma instancia de Produto")

            if t not in [1,2,3]:
                raise ValueError("O tipo de entrada deve ser 1, 2 ou 3")
            
            if "Receita" in p.getDados().keys():
                raise ValueError("Produto composto nao pode ser adicionado em nota de compra")
            
            key = IdClassFactory.gerar_id_produto_nota(lp, p.getDados(), t)

        except ValueError as e:
            print(f" Erro ao adicioinar o produto : {e}")
            return False

        if teste: return True

        lp[key] = p
        self.__salvo = False
        return True


    def venderProduto(self, idProduto:str, valorVenda:Union[int,float,str], quantidadeVenda:Union[int,float,str])-> bool| dict:
        idp = idProduto
        vv = valorVenda
        qv = quantidadeVenda
        lp = self.__produtos

        if idp not in lp.keys():
            return False

        try:
        
            p = lp[idp]

            retorno = p.vender(qv, vv); 
            
            if not retorno:
                return False
    
            self.__salvo = False
            return retorno
        
        except Exception as e:
            print(f" Erro na classe nota no metodo venderProduto : {e}")
            return False
        

    def removerProduto(self, idProduto:int)-> bool:
        idp = idProduto
        lp = self.__produtos
        
        if idp not in lp.keys():
            return False
        
        del lp[idp]
        self.__salvo = False
        return True
    
    

    def alterarProduto(self, idProduto: str, produto: Produto = None, instrucao: dict = None) -> bool | dict:
        """
        Altera propriedades de um produto já inserido na nota.
        O único argumento obrigatório é 'idProduto'. Deve-se passar APENAS UM dentre 'produto' (nova instância) ou 'instrucao' (dict).
        """
        idp = str(idProduto)
        lp = self.__produtos

        # Barreira 1: Validar quantidade de argumentos e obrigatoriedade
        if not idp:
            print("Erro (Barreira): idProduto é obrigatório.")
            return False

        if sum([produto is not None, instrucao is not None]) != 1:
            print("Erro (Barreira): Deve-se fornecer apenas UM argumento adicional ('produto' OU 'instrucao').")
            return False

        # Barreira 2: Validar existência na nota
        if idp not in lp.keys():
            print(f"Erro (Barreira): O produto '{idp}' não está registrado nesta nota.")
            return False

        prod_reg = lp[idp]
        vendas_realizadas_tela = prod_reg.getDados(f=True).get("vendas", 0.0)

        instrucao_final = None

        # Caminho A: Instrução via Dicionário
        if instrucao is not None:
            if not isinstance(instrucao, dict):
                print("Erro (Barreira): O argumento 'instrucao' deve ser um dicionário.")
                return False
            instrucao_final = instrucao

        # Caminho B: Instrução via Nova Instância de Produto
        elif produto is not None:
            if not isinstance(produto, Produto):
                print("Erro (Barreira): O argumento 'produto' deve ser instância da classe Produto.")
                return False
            
            dados_novo = produto.getDados(f=True)
            dados_reg = prod_reg.getDados(f=True)

            # Verifica se é o MESMO produto (pelo ID original da classe)
            if dados_reg["id"] == dados_novo["id"]:
                # Coleta os dados para transformar em instrução
                instrucao_final = {
                    "quantidade": dados_novo.get("quantidadeEntrada", 0),
                    "valorUnidario": dados_novo.get("valorUnitario", 0)
                }

            else:
                # É um produto diferente
                if vendas_realizadas_tela > 0:
                    # Se já vendeu, limita o estoque antigo ao que já foi vendido e adiciona o novo
                    inst_zerar = {"quantidade": vendas_realizadas_tela}
                    if not prod_reg.alterarValores(inst_zerar):
                        print("Erro ao reajustar o estoque do produto original.")
                        return False
                    
                    if not self.adicionarProduto(produto):
                        print("Erro ao adicionar o novo produto.")
                        return False
                    
                    self.__salvo = False
                    return True
                else:
                    # Sem vendas, apenas remove o antigo e coloca o novo no lugar
                    del lp[idp]
                    if not self.adicionarProduto(produto):
                        print("Erro ao substituir pelo novo produto.")
                        return False
                        
                    self.__salvo = False
                    return True

        # Validação Lógica de Limite (Barreira Final antes do processamento pesado)
        if instrucao_final is not None:
            if "quantidade" in instrucao_final:
                nova_qtd = instrucao_final["quantidade"]
                try:
                    if float(nova_qtd) < float(vendas_realizadas_tela):
                        print(f"Erro (Lógica): A quantidade de entrada ({nova_qtd}) não pode ser menor que o total já vendido ({vendas_realizadas_tela}).")
                        return False
                except Exception as e:
                    print(f"Erro (Barreira): Erro na validação de formato da quantidade -> {e}")
                    return False
                    
            # Aciona a inteligência de alteração do próprio produto
            resultado = prod_reg.alterarValores(instrucao_final)
            if resultado:
                self.__salvo = False
                return resultado

        return False
        

    def getProdutos(self) -> tuple[Produto]:
        return tuple(self.__produtos.values())
   
    def getDados(self)-> dict:
        return {
            "id" : self.__I,
            "fornecedor" : self.__F.getDados(),
            "dataEmissao" : self.__dataE,
            "dataVencimento" : self.__dataV,
            "produtos" : {k: p.getDados(True) for k, p in self.__produtos.items()},
            "valorTotal" : MoedaReal.parseMilharParaReais(self.__valorTotal),
            "desconto" : MoedaReal.parseMilharParaReais(self.__desconto),
            "acrescimo" : MoedaReal.parseMilharParaReais(self.__acrescimo),
            "valorFinal" : MoedaReal.parseMilharParaReais(self.__valorFinal),
            "valorTotalVenda" : MoedaReal.parseMilharParaReais(self.__valorTotalVenda),
            "lucroTotal" : MoedaReal.parseMilharParaReais(self.__lucroTotal),
            "salvo" : self.__salvo
        }

    def __recalcularTotais(self) -> bool:
        """
        Recalcula todos os totais da nota a partir dos produtos atualmente inseridos.
        Esse é o único ponto que modifica as variáveis contábeis.
        """
        self.__valorTotal = 0
        self.__valorTotalVenda = 0
        self.__lucroTotal = 0

        for key, p in self.__produtos.items():
            dados = p.getDados(f=False) # dados puros em inteiros (milhar/gramas)

            self.__valorTotal += dados.get("ValorTotal", 0) or 0
            self.__valorTotalVenda += dados.get("valorTotalVendas", 0) or 0
            self.__lucroTotal += dados.get("valorTotalLucro", 0) or 0

        # Calcula o valor final com desconto e acréscimo
        self.__valorFinal = self.__valorTotal - self.__desconto + self.__acrescimo

        return True

    def aplicarDesconto(self, valor: float | str) -> bool:
        """Aplica um valor de desconto na nota (em reais). Só terá efeito após salvar()."""
        try:
            self.__desconto = MoedaReal.parseCentavosPorMilhar(valor)
            self.__salvo = False
            return True
        except Exception as e:
            print(f" Erro ao aplicar desconto: {e}")
            return False

    def aplicarAcrescimo(self, valor: float | str) -> bool:
        """Aplica um valor de acréscimo na nota (em reais). Só terá efeito após salvar()."""
        try:
            self.__acrescimo = MoedaReal.parseCentavosPorMilhar(valor)
            self.__salvo = False
            return True
        except Exception as e:
            print(f" Erro ao aplicar acréscimo: {e}")
            return False

    def salvar(self)-> bool:
        """
        Salva as alterações da nota:
        1. Recalcula todos os valores contábeis (valorTotal, valorFinal, lucro, vendas)
        2. Atualiza as variáveis estáticas do Fornecedor (saldo global, compras, vendas)
        3. Marca a nota como salva
        """
        try:
            # 1. Recalcula todos os totais a partir dos produtos
            self.__recalcularTotais()

            # 2. Atualiza os dados globais do fornecedor
            if isinstance(self.__F, Fornecedor):
                self.__F.atualizarContabilidade(
                    valorCompra=self.__valorFinal,
                    valorVenda=self.__valorTotalVenda,
                    lucro=self.__lucroTotal
                )

            # 3. Marca como salvo
            self.__salvo = True
            return True

        except Exception as e:
            print(f" Erro ao salvar a nota: {e}")
            return False