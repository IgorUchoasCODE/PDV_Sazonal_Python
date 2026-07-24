from br.com.pdv.src.produto.produto import Produto
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida, UnidadeConjunto
from typing import Union, Dict, Any

class productClassFactory:
    """
    Classe estática que recebe instruções por meio de dicionário 
    ou diretamente do Banco de Dados para fabricar instâncias de Produto.
    Armazena os moldes (instruções puras) para reconstruí-los quando necessário.
    """
    
    _moldes: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def __parse_unidade_medida(cls, 
                               descricao: Union[str, int, UnidadeMedida, UnidadeConjunto] = None, 
                               fator_conjunto: int = None,
                               unidade_id: int = None) -> Union[UnidadeMedida, UnidadeConjunto]:
        """
        Converte a descrição (string), ID do banco ou enum para os objetos reais UnidadeMedida ou UnidadeConjunto.
        Trata com atenção especial as unidades de conjunto que possuem fatorConjunto.
        """
        if isinstance(descricao, (UnidadeMedida, UnidadeConjunto)):
            return descricao

        if isinstance(descricao, int) and unidade_id is None:
            unidade_id = descricao
            descricao = None

        if unidade_id is not None and (descricao is None or fator_conjunto is None):
            try:
                from br.com.pdv.src.BDD.queryEnum import DB
                um_db = DB.SELECT.UNIDADE_MEDIDA_POR_ID.buscar_um(unidade_id)
                if um_db:
                    if descricao is None:
                        descricao = um_db.get("descricao")
                    if fator_conjunto is None:
                        fator_conjunto = um_db.get("fatorConjunto")
            except Exception:
                pass

        # Extrai o fator_conjunto caso esteja na descrição do tipo "Caixa/Pacote (360 un.)"
        if fator_conjunto is None and isinstance(descricao, str) and "(" in descricao and ")" in descricao:
            try:
                conteudo_parenteses = descricao.split("(")[1].split(")")[0]
                numeros = [int(s) for s in conteudo_parenteses.split() if s.isdigit()]
                if numeros:
                    fator_conjunto = numeros[0]
            except Exception:
                pass

        # Se temos um fator de conjunto válido (> 1), trata-se de um UnidadeConjunto
        if fator_conjunto is not None and isinstance(fator_conjunto, int) and fator_conjunto > 1:
            return UnidadeConjunto(UnidadeMedida.CONJUNTO, fator_conjunto)

        if isinstance(descricao, str):
            desc_upper = descricao.strip().upper()
            
            if "CONJUNTO" in desc_upper or "PACOTE" in desc_upper:
                if fator_conjunto and fator_conjunto > 1:
                    return UnidadeConjunto(UnidadeMedida.CONJUNTO, fator_conjunto)
                return UnidadeMedida.CONJUNTO

            for um in UnidadeMedida:
                if um.getDescription().upper() == desc_upper:
                    return um
                if um.name.upper() == desc_upper:
                    return um
                if um.getDescription().upper() == desc_upper.split()[0]:
                    return um

        return UnidadeMedida.UNIDADE

    @classmethod
    def registrar_molde(cls, id_molde: str, instrucoes: dict):
        """Armazena as instruções (molde) puras para reconstruir o produto."""
        cls._moldes[str(id_molde)] = instrucoes

    @classmethod
    def fabricar_do_banco(cls, id_produto: int) -> Produto:
        """
        Busca as instruções de um produto diretamente do banco de dados (vw_produto_completo),
        monta o dicionário de molde e constrói a instância de Produto.
        """
        from br.com.pdv.src.BDD.queryEnum import DB
        
        dados_db = DB.SELECT.VW_PRODUTO_COMPLETO_POR_ID.buscar_um(id_produto)
        if not dados_db:
            raise ValueError(f"Produto com ID {id_produto} não encontrado no banco de dados.")

        instrucoes = {
            "id": dados_db["id"],
            "nome": dados_db["nome"],
            "diasDuraveis": dados_db["diasDuraveis"],
            "unidadeMedida": dados_db.get("unidade_descricao") or dados_db.get("unidadeMedida"),
            "fatorConjunto": dados_db.get("fatorConjunto")
        }

        # Se tiver receita registrada (produto composto), busca os ingredientes no banco
        if dados_db.get("receita"):
            receita_rows = DB.SELECT.RECEITA_POR_PRODUTO.buscar(id_produto)
            if receita_rows:
                instrucoes["receita"] = {row["id_ingrediente"]: row["qntdd"] for row in receita_rows}

        cls.registrar_molde(str(id_produto), instrucoes)
        return cls.fabricar(instrucoes)

    @classmethod
    def fabricar(cls, id_ou_instrucoes: Union[int, str, dict]) -> Produto:
        """
        Constrói uma nova instância de Produto.
        Pode receber um dicionário com instruções, um ID de molde já registrado,
        ou um ID de produto que será buscado diretamente do Banco de Dados.
        """
        if isinstance(id_ou_instrucoes, dict):
            instrucoes = id_ou_instrucoes
            id_molde = str(instrucoes.get("id"))
            cls.registrar_molde(id_molde, instrucoes)
        else:
            id_molde = str(id_ou_instrucoes)
            if id_molde in cls._moldes:
                instrucoes = cls._moldes[id_molde]
            else:
                # Se não tem o molde em memória, busca diretamente do banco
                try:
                    return cls.fabricar_do_banco(int(id_molde))
                except Exception as e:
                    raise ValueError(f"Molde/Produto com ID {id_molde} não encontrado. Erro: {e}")

        # Converte a descrição textual / fator de conjunto para o Objeto de Unidade necessário
        unidade_obj = cls.__parse_unidade_medida(
            descricao=instrucoes.get("unidade_descricao") or instrucoes.get("unidadeMedida"),
            fator_conjunto=instrucoes.get("fatorConjunto") or instrucoes.get("fator_conjunto")
        )
        
        produto = Produto(
            id=instrucoes.get("id"),
            nome=instrucoes.get("nome"),
            diasDuraveis=instrucoes.get("diasDuraveis"),
            unidadeMedida=unidade_obj
        )
        
        if "receita" in instrucoes and instrucoes["receita"]:
            produto.insertPropertValue(receita=instrucoes["receita"])

        elif "valorUnidario" in instrucoes and "quantidade" in instrucoes:
            produto.insertPropertValue(
                valorUnidario=instrucoes["valorUnidario"],
                quantidade=instrucoes["quantidade"]
            )
            
        return produto

    @classmethod
    def testar_e_fabricar(cls, instrucoes: Union[dict, int]) -> Produto:
        """
        Recebe instruções ou ID do banco, fabrica, testa a integridade dos dados e retorna a instância.
        """
        if isinstance(instrucoes, int):
            return cls.fabricar_do_banco(instrucoes)
            
        id_molde = str(instrucoes.get("id"))
        cls.registrar_molde(id_molde, instrucoes)
        produto = cls.fabricar(instrucoes)
        
        dados = produto.getDados(f=False)
        
        if "nome" in instrucoes and dados["nome"] != instrucoes["nome"]:
            raise ValueError(f"Falha no teste: Nome incompatível. Esperado {instrucoes['nome']}, obtido {dados['nome']}")
        
        if "diasDuraveis" in instrucoes and dados["diasDuraveis"] != instrucoes["diasDuraveis"]:
            raise ValueError(f"Falha no teste: diasDuraveis incompatível. Esperado {instrucoes['diasDuraveis']}, obtido {dados['diasDuraveis']}")
        
        return produto

# Alias para compatibilidade com importações em PascalCase
ProductClassFactory = productClassFactory


if False:
    # 1. TESTE PRODUTO VIRGEM (Molde sem dados contábeis - sem insertPropertValue)
    instrucoes_virgem = {
        "id": 100,
        "nome": "Caixa de Ovos Branco A (360 un.)",
        "diasDuraveis": 30,
        "unidadeMedida": "CONJUNTO/PACOTE (360 un.)",
        "fatorConjunto": 360
    }
    p_virgem = productClassFactory.fabricar(instrucoes_virgem)
    print(f"[OK] Produto Virgem (Molde): {p_virgem.getDados(f=True)['nome']}")
    print(f"     -> Valor Unitário: {p_virgem.getDados(f=True)['valorUnitario']} (Deve ser None)")
    print(f"     -> Estoque: {p_virgem.getDados(f=True)['estoque']} (Deve ser 0.0)")

    # 2. TESTE PRODUTO COM DADOS CONTÁBEIS (com insertPropertValue)
    instrucoes_contabil = {
        "id": 101,
        "nome": "Fardo de Coca-Cola 350ml (12 un.)",
        "diasDuraveis": 180,
        "unidadeMedida": "Conjunto/Pacote (12 un.)",
        "fatorConjunto": 12,
        "valorUnidario": 30.00,
        "quantidade": 10
    }
    p_contabil = productClassFactory.fabricar(instrucoes_contabil)
    print(f"\n[OK] Produto com Dados Contábeis: {p_contabil.getDados(f=True)['nome']}")
    print(f"     -> Valor Unitário: R$ {p_contabil.getDados(f=True)['valorUnitario']}")
    print(f"     -> Valor Total: R$ {p_contabil.getDados(f=True)['ValorTotal']}")
    print(f"     -> Estoque de Entrada: {p_contabil.getDados(f=True)['quantidadeEntrada']} fardos")


    p = productClassFactory.testar_e_fabricar(4)

    print(p.getDados())

    p = productClassFactory.testar_e_fabricar(18)
    print(p.getDados())
