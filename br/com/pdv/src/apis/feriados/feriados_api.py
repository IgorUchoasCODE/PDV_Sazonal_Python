"""
API de Feriados Nacionais e Pontos Facultativos do Brasil
Utiliza a BrasilAPI (gratuita, sem chave de API necessária)
- Feriados: https://brasilapi.com.br/api/feriados/v1/{ano}

Inclui também uma base local de pontos facultativos e feriados estaduais do Amazonas,
agora carregada dinamicamente a partir de um arquivo JSON (sem dados no código).
"""
import urllib.request
import json
import os
from datetime import date


class FeriadosAPI:
    """
    Classe estática agregadora de Feriados Nacionais (BrasilAPI) e Locais (JSON).
    """
    
    _ARQUIVO_DADOS_LOCAIS = os.path.join(os.path.dirname(__file__), "feriados_locais.json")
    
    @staticmethod
    def _carregar_dados_locais() -> dict:
        """Carrega os pontos facultativos e feriados estaduais do arquivo JSON."""
        try:
            with open(FeriadosAPI._ARQUIVO_DADOS_LOCAIS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[FeriadosAPI] Erro ao carregar {FeriadosAPI._ARQUIVO_DADOS_LOCAIS}: {e}")
            return {"PONTOS_FACULTATIVOS": {}, "FERIADOS_AMAZONAS": []}

    @staticmethod
    def _fazer_requisicao(url: str) -> list | bool:
        """Faz uma requisição HTTP GET e retorna o JSON."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PDV_Sazonal_Python/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                return dados
        except Exception as e:
            print(f"[FeriadosAPI] Erro na requisição para {url}: {e}")
            return False

    @staticmethod
    def obter_feriados_nacionais(ano: int = None) -> dict | bool:
        """
        Retorna os feriados nacionais do ano informado via BrasilAPI.
        Se 'ano' for None, usa o ano corrente.
        Retorna um dicionário organizado por mês.
        """
        if ano is None:
            ano = date.today().year

        url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
        dados_brutos = FeriadosAPI._fazer_requisicao(url)

        if not dados_brutos:
            return False

        try:
            resultado = {
                "ano": ano,
                "fonte": "BrasilAPI",
                "totalFeriados": len(dados_brutos),
                "feriados": []
            }

            for feriado in dados_brutos:
                resultado["feriados"].append({
                    "data": feriado.get("date"),
                    "nome": feriado.get("name"),
                    "tipo": feriado.get("type", "national"),
                })

            return resultado

        except Exception as e:
            print(f"[FeriadosAPI] Erro ao processar feriados nacionais: {e}")
            return False

    @staticmethod
    def obter_pontos_facultativos(ano: int = None) -> dict:
        """
        Retorna os pontos facultativos do ano informado (base local via JSON).
        """
        if ano is None:
            ano = date.today().year

        dados_locais = FeriadosAPI._carregar_dados_locais()
        pontos_facultativos = dados_locais.get("PONTOS_FACULTATIVOS", {})
        
        # PONTOS_FACULTATIVOS é um dicionário com os anos como chaves (strings) no JSON
        facultativos = pontos_facultativos.get(str(ano), [])

        return {
            "ano": ano,
            "fonte": "Base Local (JSON)",
            "totalPontosFacultativos": len(facultativos),
            "pontosFacultativos": facultativos
        }

    @staticmethod
    def obter_feriados_amazonas(ano: int = None) -> dict:
        """
        Retorna os feriados estaduais do Amazonas e municipais de Manaus (base local via JSON).
        """
        if ano is None:
            ano = date.today().year

        dados_locais = FeriadosAPI._carregar_dados_locais()
        feriados_amazonas = dados_locais.get("FERIADOS_AMAZONAS", [])

        feriados_ano = []
        for f in feriados_amazonas:
            feriados_ano.append({
                "data": f"{ano}-{f['data_recorrente']}",
                "nome": f["nome"],
                "tipo": f["tipo"],
            })

        return {
            "ano": ano,
            "estado": "Amazonas",
            "fonte": "Base Local (JSON)",
            "totalFeriados": len(feriados_ano),
            "feriados": feriados_ano
        }

    @staticmethod
    def obter_calendario_completo(ano: int = None) -> dict | bool:
        """
        Retorna um calendário completo unificado contendo:
        - Feriados Nacionais (BrasilAPI)
        - Pontos Facultativos (Base Local)
        - Feriados Estaduais do Amazonas (Base Local)
        Tudo ordenado por data.
        """
        if ano is None:
            ano = date.today().year

        nacionais = FeriadosAPI.obter_feriados_nacionais(ano)
        facultativos = FeriadosAPI.obter_pontos_facultativos(ano)
        estaduais = FeriadosAPI.obter_feriados_amazonas(ano)

        todas_datas = []

        if nacionais and "feriados" in nacionais:
            for f in nacionais["feriados"]:
                todas_datas.append(f)

        for f in facultativos.get("pontosFacultativos", []):
            todas_datas.append(f)

        for f in estaduais.get("feriados", []):
            todas_datas.append(f)

        # Ordena por data
        todas_datas.sort(key=lambda x: x.get("data", ""))

        return {
            "ano": ano,
            "totalEventos": len(todas_datas),
            "calendario": todas_datas
        }


# =================================================================
#  TESTE DIRETO (executar: python -m br.com.pdv.src.apis.feriados.feriados_api)
# =================================================================
if __name__ == "__main__":
    print("=" * 60)
    print(" TESTE API DE FERIADOS E PONTOS FACULTATIVOS ")
    print("=" * 60)

    ano_teste = date.today().year

    # Teste 1: Feriados Nacionais
    print(f"\n[TESTE 1] Feriados Nacionais de {ano_teste}:")
    nacionais = FeriadosAPI.obter_feriados_nacionais(ano_teste)
    if nacionais:
        for f in nacionais["feriados"]:
            print(f"  {f['data']} | {f['nome']} ({f['tipo']})")
    
    # Teste 2: Pontos Facultativos
    print(f"\n[TESTE 2] Pontos Facultativos de {ano_teste}:")
    facult = FeriadosAPI.obter_pontos_facultativos(ano_teste)
    for f in facult["pontosFacultativos"]:
        print(f"  {f['data']} | {f['nome']}")

    # Teste 3: Feriados Estaduais
    print(f"\n[TESTE 3] Feriados Estaduais do Amazonas ({ano_teste}):")
    estaduais = FeriadosAPI.obter_feriados_amazonas(ano_teste)
    for f in estaduais["feriados"]:
        print(f"  {f['data']} | {f['nome']} ({f['tipo']})")

    # Teste 4: Calendário Completo
    print(f"\n[TESTE 4] Calendário Completo Unificado ({ano_teste}):")
    cal = FeriadosAPI.obter_calendario_completo(ano_teste)
    if cal:
        print(f"  Total de eventos no ano: {cal['totalEventos']}")
        for f in cal["calendario"]:
            print(f"  {f['data']} | {f['nome']} ({f['tipo']})")

    print("\n" + "=" * 60)
    print(" TESTES FINALIZADOS")
    print("=" * 60)
