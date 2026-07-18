from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida, UnidadeConjunto
from typing import Union

class productClassFactory:
    """
    Classe estática que recebe instruções por meio de dicionário para fabricar cada produto 
    e armazenar os moldes (instruções puras/strings) para reconstruí-los quando necessário.
    """
    
    _moldes = {}

    @classmethod
    def __parse_unidade_medida(cls, descricao: str, fator_conjunto: int = None) -> Union[UnidadeMedida, UnidadeConjunto]:
        """Converte a descrição em string de volta para os objetos reais UnidadeMedida ou UnidadeConjunto"""
        unidade_enum = None
        for um in UnidadeMedida:
            
            #Se for conjunto, verificar se a descrição é igual
            if um.getDescription() == descricao:
                unidade_enum = um
                break

            elif um.getDescription() == descricao.split()[0]:
                #Extrai o fator conjunto da descrição
                fator_conjunto = int(descricao.split("(")[1].split(" ")[0])

                if UnidadeConjunto(um, fator_conjunto).getDescription() == descricao:
                    unidade_enum = UnidadeConjunto(um, fator_conjunto)
                    break

                
        if unidade_enum is None:
            raise ValueError(f"Unidade de medida não reconhecida: {descricao}")
            
        if unidade_enum == UnidadeMedida.CONJUNTO and fator_conjunto is not None:
            return UnidadeConjunto(unidade_enum, fator_conjunto)
        
        return unidade_enum

    @classmethod
    def registrar_molde(cls, id_molde: str, instrucoes: dict):
        """Armazena as instruções (molde) puras para reconstruir o produto."""
        cls._moldes[id_molde] = instrucoes

    @classmethod
    def fabricar(cls, id_molde: str) -> Produto:
        """Constrói uma nova instância de Produto convertendo strings em objetos e usando o molde salvo."""
        if id_molde not in cls._moldes:
            raise ValueError(f"Molde {id_molde} não encontrado.")
        
        instrucoes = cls._moldes[id_molde]
        
        # Converte a descrição textual da unidade de volta para o Objeto necessário
        unidade_obj = cls.__parse_unidade_medida(
            descricao=instrucoes.get("unidadeMedida"),
            fator_conjunto=instrucoes.get("fatorConjunto")
        )
        
        produto = Produto(
            id=instrucoes.get("id"),
            nome=instrucoes.get("nome"),
            durabilidade=instrucoes.get("durabilidade"),
            unidadeMedida=unidade_obj
        )
        
        if "receita" in instrucoes:
            produto.insertPropertValue(receita=instrucoes["receita"])

        elif "valorUnidario" in instrucoes and "quantidade" in instrucoes:

            produto.insertPropertValue(
                valorUnidario=instrucoes["valorUnidario"],
                quantidade=instrucoes["quantidade"]
            )
            
        return produto

    @classmethod
    def testar_e_fabricar(cls, instrucoes: dict) -> Produto:
        """
        Recebe instruções, fabrica, testa usando getDados, compara e 
        armazena no dicionário de moldes para reconstrução. Retorna uma instância pronta.
        """
        id_molde = str(instrucoes.get("id"))
        
        # Armazena em um dicionário para reconstruir quantas vezes for necessário
        cls.registrar_molde(id_molde, instrucoes)
        
        # Fabrica a instância
        produto = cls.fabricar(id_molde)
        
        # Testa usando o método getDados (f=False retorna os valores internos sem formatação p/ tela)
        dados = produto.getDados(f=False)
        
        # Compara com os atributos passados na instrução (teste de integridade)
        if dados["nome"] != instrucoes["nome"]:
            raise ValueError(f"Falha no teste: Nome incompatível. Esperado {instrucoes['nome']}, obtido {dados['nome']}")
        
        if dados["diasDuraveis"] != instrucoes["durabilidade"]:
            raise ValueError(f"Falha no teste: Durabilidade incompatível. Esperado {instrucoes['durabilidade']}, obtido {dados['diasDuraveis']}")
        
       
        return produto


if False:
    # Exemplo funcional com strings e tipos primitivos apenas no dicionário
    instrucoes_teste_1 = {
        "id": 1,
        "nome": "Coca-Cola 2L",
        "durabilidade": 365,
        "unidadeMedida": "Unidade" # Passando como string pura

    }
    
    instrucoes_teste_2 = {
        "id": 2,
        "nome": "caixa de ovos branco tipo A",
        "durabilidade": 7,
        "unidadeMedida": "Conjunto/Pacote (360 un.)", # Passando como string pura
        "fatorConjunto": 360 # Parâmetro extra necessário para a forma especial do Conjunto

    }

    instrucoes_teste_3 = {
        "id": 3,
        "nome": "cartela de ovos branco tipo A",
        "durabilidade": 7,
        "unidadeMedida": "Conjunto/Pacote (30 un.)",
        "fatorConjunto": 30,
        "receita": {2: 30}

    }

    


    p = productClassFactory.testar_e_fabricar(instrucoes_teste_2)
    for k,v in p.getDados(f=True).items():
        print(f"{k} ==> {v}")

    print(f"\n{p.insertPropertValue(valorUnidario=120, quantidade=720)}\n")

    for k,v in p.getDados(f=True).items():
        print(f"{k} ==> {v}")

    print(f"\n{p.vender(30,180)}\n")

    for k,v in p.getDados(f=True).items():
        print(f"{k} ==> {v}")