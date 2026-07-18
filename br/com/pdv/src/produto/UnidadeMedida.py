from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

class UnidadeMedida(Enum):
    UNIDADE = ("Unidade", 1)
    KG = ("Kilograma", 1000)
    L = ("Litros", 1000)
    M = ("Metros", 1000)
    CONJUNTO = ("Conjunto/Pacote", 1)

    def __init__(self, descricao: str, proporcao: int):
        self._descricao = descricao
        self._proporcao = proporcao

    def getDescription(self) -> str:
        return self._descricao

    def getMultInt(self, config: int = None) -> int:
        if config is not None:
            if not isinstance(config, int):
                raise ValueError(f"config deve ser um número inteiro, recebido: {config}")
            if config <= 1:
                raise ValueError(f"config deve ser maior que 1, recebido: {config}")
            return self._proporcao * config
        
        return self._proporcao

    def parseInt(self, valor_tela: Union[float, str], config: int = None) -> int:
        """
        Converte o valor flutuante/texto da tela e multiplica pela proporção da unidade.
        Garante precisão absoluta usando Decimal e bloqueia frações em unidades inteiras.
        """
        
        p = self.getMultInt(config)
        

        # 1. Padroniza a entrada para Decimal com segurança
        valor_decimal = Decimal(str(valor_tela))
        
        # 2. Validação de Regra de Negócio: Impede fracionar unidades!
        if p == 1 and valor_decimal % 1 != 0:
            raise ValueError(f"O produto é vendido por {self.getDescription()} e não aceita quantidades fracionadas (recebido: {valor_tela}).")

        # 3. Faz o cálculo da conversão (ex: 5.3 * 1000)
        resultado = valor_decimal * Decimal(str(p))
        
        # 4. Arredonda comercialmente e retorna um inteiro puro para o sistema
        return int(resultado.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    
    def parseFloat(self, valor_interno: int, config: int = None) -> float:
        """
        Converte o inteiro do sistema (ex: 5300) de volta para float (ex: 5.3) na tela.
        """
           
        p = self.getMultInt(config)


        valor_decimal = Decimal(str(valor_interno))
        resultado = valor_decimal / Decimal(str(p))
        
        return float(resultado)
    


class UnidadeConjunto:
    """
    Esta classe encapsula a UnidadeMedida (Enum) e associa-lhe um fator 
    de conversão específico para aquela instância de produto.
    """
    def __init__(self, unidade_base: UnidadeMedida, fator_conjunto: int):

        if unidade_base.getDescription() != "Conjunto/Pacote":
            raise ValueError(f"unidade_base deve ser do tipo UnidadeMedida, recebido: {unidade_base}")
        
        if not isinstance(fator_conjunto, int) or fator_conjunto <= 1:
            raise ValueError(f"fator_conjunto deve ser um número inteiro maior que 1, recebido: {fator_conjunto}")
        
        
        self.__unidade_base = unidade_base
        self.__fator_conjunto = fator_conjunto

    def getMultInt(self) -> int:
       
        return self.__unidade_base.getMultInt(self.__fator_conjunto)

    def parseInt(self, valor_tela: Union[float, str]) -> int:
       
        return self.__unidade_base.parseInt(valor_tela)
    
    def parseFloat(self, valor_interno: int) -> float:
       
        return self.__unidade_base.parseFloat(valor_interno)
        
    def getDescription(self) -> str:
        if self.__fator_conjunto:
            return f"{self.__unidade_base.getDescription()} ({self.__fator_conjunto} un.)"
        return self.__unidade_base.getDescription()
    



