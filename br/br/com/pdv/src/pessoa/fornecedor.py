from br.com.pdv.src.pessoa.pessoa import Pessoa
from br.com.pdv.src.pessoa.empresa import Empresa
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union

class Fornecedor:
    # Variáveis estáticas globais — acumulam os valores de TODAS as notas de TODOS os fornecedores
    __saldoTotalGlobal : int = 0       # compras - vendas (custo líquido global)
    __comprasTotalGlobal : int = 0     # soma de todos os valorFinal das notas salvas
    __vendaTotalGlobal : int = 0       # soma de todos os valorTotalVenda das notas salvas
    __lucroTotalGlobal : int = 0       # soma de todos os lucros das notas salvas

    def __init__(self, id:int, tipoFornecedor: Union[Pessoa, Empresa]):
        self.__id = id
        self.__origem = tipoFornecedor

        # Dicionário de notas deste fornecedor: {id_nota: NotaCompra}
        self.__notasCompra: dict[int, object] = {}

        # Totais individuais deste fornecedor (acumulados ao salvar cada nota)
        self.__comprasTotal = 0     # soma do valorFinal das notas deste fornecedor
        self.__vendaTotal = 0       # soma do valorTotalVenda das notas deste fornecedor
        self.__lucroTotal = 0       # soma dos lucros das notas deste fornecedor

    def adicionarNotaCompra(self, nota) -> bool:
        """Adiciona uma nota de compra ao fornecedor."""
        try:
            dados = nota.getDados()
            idNota = dados["id"]

            if idNota in self.__notasCompra:
                print(f"Nota com id {idNota} já existe neste fornecedor")
                return False

            self.__notasCompra[idNota] = nota
            return True

        except Exception as e:
            print(f" Erro ao adicionar nota: {e}")
            return False
    
    def removerNotaCompra(self, idNotaCompra:int) -> bool:
        """Remove uma nota de compra pelo id."""
        if idNotaCompra not in self.__notasCompra:
            print(f"Nota {idNotaCompra} não encontrada")
            return False
        
        del self.__notasCompra[idNotaCompra]
        return True
    
    def alterarNotaCompra(self, idNotaCompra:int, nota) -> bool:
        """Substitui uma nota existente por uma nova."""
        if idNotaCompra not in self.__notasCompra:
            print(f"Nota {idNotaCompra} não encontrada para alteração")
            return False
        
        self.__notasCompra[idNotaCompra] = nota
        return True
    
    def getNotaCompra(self, idNotaCompra:int):
        """Retorna uma nota específica pelo id."""
        if idNotaCompra not in self.__notasCompra:
            return None
        return self.__notasCompra[idNotaCompra]
    
    def getNotasCompra(self) -> tuple:
        """Retorna todas as notas de compra deste fornecedor."""
        return tuple(self.__notasCompra.values())

    def atualizarContabilidade(self, valorCompra:int, valorVenda:int, lucro:int) -> bool:
        """
        Chamado pelo método salvar() da NotaCompra para atualizar os totais 
        do fornecedor e os totais globais estáticos.
        Recebe valores em milhar (int) já calculados pela nota.
        """
        try:
            # Atualiza totais do fornecedor
            self.__comprasTotal = valorCompra
            self.__vendaTotal = valorVenda
            self.__lucroTotal = lucro

            # Atualiza totais globais (estáticos)
            Fornecedor.__comprasTotalGlobal += valorCompra
            Fornecedor.__vendaTotalGlobal += valorVenda
            Fornecedor.__lucroTotalGlobal += lucro
            Fornecedor.__saldoTotalGlobal = Fornecedor.__comprasTotalGlobal - Fornecedor.__vendaTotalGlobal

            return True

        except Exception as e:
            print(f" Erro ao atualizar contabilidade do fornecedor: {e}")
            return False

    def getDados(self) -> dict:
        """Retorna os dados do fornecedor e seus totais."""
        return {
            "id" : self.__id,
            "origem" : self.__origem.info(),
            "quantidadeNotas" : len(self.__notasCompra),
            "comprasTotal" : MoedaReal.parseMilharParaReais(self.__comprasTotal),
            "vendaTotal" : MoedaReal.parseMilharParaReais(self.__vendaTotal),
            "lucroTotal" : MoedaReal.parseMilharParaReais(self.__lucroTotal),
        }

    @classmethod
    def getDadosGlobais(cls) -> dict:
        """Retorna os totais globais de todos os fornecedores."""
        return {
            "saldoTotalGlobal" : MoedaReal.parseMilharParaReais(cls.__saldoTotalGlobal),
            "comprasTotalGlobal" : MoedaReal.parseMilharParaReais(cls.__comprasTotalGlobal),
            "vendaTotalGlobal" : MoedaReal.parseMilharParaReais(cls.__vendaTotalGlobal),
            "lucroTotalGlobal" : MoedaReal.parseMilharParaReais(cls.__lucroTotalGlobal),
        }