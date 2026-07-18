from decimal import Decimal, ROUND_HALF_UP
from typing import Union

class MoedaReal:
    """
    Classe Utilitária Estática para Aritmética de Ponto Fixo.
    Nenhuma instância deve ser criada. Todo o sistema financeiro passa por aqui.
    """
    
    # Constante da classe (equivalente ao 'public static final' no Java)
    FATOR_MILHAR = Decimal("1000")

    @staticmethod
    def parseCentavosPorMilhar(reais: Union[float, str]) -> int:
        """
        Converte o valor flutuante da tela (ex: 10.50) para o inteiro do sistema (10500).
        """
        valor_decimal = Decimal(str(reais))
        resultado = valor_decimal * MoedaReal.FATOR_MILHAR
        
        # Arredonda comercialmente e garante que a saída seja um int puro
        return int(resultado.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def parseMilharParaReais(valor_interno_milhar: int) -> float:
        """
        Converte o inteiro do sistema (10500) de volta para float (10.5) para a Interface.
        """
        valor_decimal = Decimal(str(valor_interno_milhar))
        resultado = valor_decimal / MoedaReal.FATOR_MILHAR
        
        # Retorna com 3 casas decimais de precisão se necessário
        return float(resultado.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculo_PQV_T(proporcao: int, quantidade: int, valor_milhar: int) -> int:
        """
        Calcula o Valor Total: (Quantidade * Valor) / Proporção
        Usa Decimal internamente para impedir perdas por divisão truncada.
        """
        q = Decimal(str(quantidade))
        v = Decimal(str(valor_milhar))
        p = Decimal(str(proporcao))

        resultado = (q * v) / p
        
        # O quantize com "1" garante que arredonde para o inteiro mais próximo.
        # Ex: 26.5 vira 27 milésimos. 26.4 vira 26 milésimos.
        return int(resultado.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculo_QeVp_Vu(proporcao: int, valor_milhar: int) -> int:
        """
        Calcula o Custo Unitário: Valor / Proporção
        """
        v = Decimal(str(valor_milhar))
        p = Decimal(str(proporcao))

        resultado = v / p
  
        
        valor_final = int(resultado.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        
        # Opcional: Proteção contra custo zero se for muito menor que a proporção
        if valor_final == 0 and valor_milhar > 0:
            raise ValueError(f"O valor {valor_milhar} é pequeno demais para a proporção {proporcao}, resultando em custo zero.")
            
        return valor_final

    



