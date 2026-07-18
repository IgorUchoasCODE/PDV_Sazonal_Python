from typing import Dict, Any, Union

class IdClassFactory:
    """
    Fábrica responsável por gerar IDs.
    Gera IDs internos (compostos) usados dentro de notas e IDs globais para uso no gerenciador de fluxo de estoque (inventoryFlowManage).
    """

    @staticmethod
    def gerar_id_produto_nota(produtos_nota: Dict[str, Any], dados_produto: Dict[str, Any], id_nota: int) -> str:
        """
        Gera o ID interno de um produto quando adicionado a uma nota.
        Formato gerado: {id_produto}.{id_nota}.{variacaoEntrada} (Ex: 1.1.0, 1.1.1, 2.1.0)
        
        :param produtos_nota: Dicionário contendo os produtos já adicionados (chave: ID composto string, valor: Produto).
        :param dados_produto: Dicionário com os dados do produto (deve possuir a chave 'id', que pode ser retornado por getDados()).
        :param id_nota: ID da nota (funciona como id do tipo de entrada/saída).
        :return: ID composto em formato string.
        """
        id_produto = dados_produto.get("id")
        if id_produto is None:
            raise ValueError("O dicionário 'dados_produto' precisa conter a chave 'id'.")
            
        # Prefixo base do ID composto: id_produto.id_nota.
        prefixo = f"{id_produto}.{id_nota}."
        
        max_variacao = -1
        
        # Itera sobre os IDs já registrados no dicionário da nota para encontrar a maior variação
        for id_existente in produtos_nota.keys():
            id_str = str(id_existente)
            if id_str.startswith(prefixo):
                try:
                    # Extrai a última parte do ID composto que representa a variação
                    variacao_atual = int(id_str.split('.')[-1])
                    if variacao_atual > max_variacao:
                        max_variacao = variacao_atual
                except ValueError:
                    continue
                    
        # A nova variação será o último maior valor encontrado + 1 (inicia em 0 se não existir nenhum)
        nova_variacao = max_variacao + 1
        
        return f"{prefixo}{nova_variacao}"

    @staticmethod
    def gerar_id_global(colecao: Union[Dict, list]) -> int:
        """
        Gera um ID global auto-incremental. 
        Pode ser usado no 'inventoryFlowManage' para criar IDs únicos para produtos, notas, tipos, etc.
        
        :param colecao: Pode ser um dicionário (onde as chaves são os IDs) ou uma lista de IDs atuais.
        :return: Um novo ID inteiro, sequencial baseado no maior ID existente.
        """
        if not colecao:
            return 1
            
        ids_existentes = []
        
        if isinstance(colecao, dict):
            itens = colecao.keys()
        else:
            itens = colecao
            
        for item in itens:
            if isinstance(item, int):
                ids_existentes.append(item)
            elif isinstance(item, str) and item.isdigit():
                ids_existentes.append(int(item))
                
        if not ids_existentes:
            return 1
            
        return max(ids_existentes) + 1

produtos_notas = {
    "1.1.0": "coca cola",
    "1.1.1": "coca cola",
    "2.1.0": "coca cola",
    "3.1.0": "coca cola",
    "1.1.15": "coca cola"
    
    
    
    }    


print(IdClassFactory.gerar_id_produto_nota(
    produtos_notas,
    {"id":"77","nome":"coca cola","tipo":"refrigerante"},
    1,
    ))

