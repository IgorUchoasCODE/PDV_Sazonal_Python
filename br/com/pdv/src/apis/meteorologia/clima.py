"""
API de Dados Meteorológicos e Nível dos Rios — Amazonas
Utiliza a Open-Meteo API (gratuita, sem chave necessária).
- Clima (Previsão 7 dias): https://api.open-meteo.com/v1/forecast
- Rios (Flood API GloFAS): https://flood-api.open-meteo.com/v1/flood

As coordenadas das principais cidades do Amazonas e pontos de medição dos rios
agora são carregadas dinamicamente a partir do arquivo clima_locais.json.
"""
import urllib.request
import json
import os
from datetime import date


class ClimaAPI:
    """
    Classe estática agregadora de Dados Meteorológicos (Open-Meteo) 
    e Nível dos Rios para o Estado do Amazonas.
    """
    
    _ARQUIVO_DADOS_LOCAIS = os.path.join(os.path.dirname(__file__), "clima_locais.json")
    
    @staticmethod
    def _carregar_dados_locais() -> dict:
        """Carrega as coordenadas das cidades e rios a partir do JSON."""
        try:
            with open(ClimaAPI._ARQUIVO_DADOS_LOCAIS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ClimaAPI] Erro ao carregar {ClimaAPI._ARQUIVO_DADOS_LOCAIS}: {e}")
            return {"CIDADES_AMAZONAS": {}, "RIOS_AMAZONAS": {}}

    @staticmethod
    def _fazer_requisicao(url: str) -> dict | bool:
        """Faz uma requisição HTTP GET e retorna o JSON como dicionário."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PDV_Sazonal_Python/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                return dados
        except Exception as e:
            print(f"[ClimaAPI] Erro na requisição para {url}: {e}")
            return False

    @staticmethod
    def obter_previsao_tempo(cidade: str = "Manaus") -> dict | bool:
        """
        Retorna a previsão do tempo para a cidade informada (padrão: Manaus).
        Dados: temperatura, umidade relativa, precipitação, vento, e condição do céu.
        Retorna um dicionário organizado ou False em caso de erro.
        """
        dados_locais = ClimaAPI._carregar_dados_locais()
        cidades = dados_locais.get("CIDADES_AMAZONAS", {})

        if cidade not in cidades:
            print(f"[ClimaAPI] Erro: Cidade '{cidade}' não cadastrada. Cidades disponíveis: {list(cidades.keys())}")
            return False

        coord = cidades[cidade]
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coord['lat']}&longitude={coord['lon']}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset"
            f"&timezone=America/Manaus"
            f"&forecast_days=7"
        )

        dados_brutos = ClimaAPI._fazer_requisicao(url)
        if not dados_brutos:
            return False

        try:
            atual = dados_brutos.get("current", {})
            diario = dados_brutos.get("daily", {})

            resultado = {
                "cidade": cidade,
                "coordenadas": coord,
                "dataConsulta": str(date.today()),
                "atual": {
                    "temperatura": atual.get("temperature_2m"),
                    "sensacaoTermica": atual.get("apparent_temperature"),
                    "umidadeRelativa": atual.get("relative_humidity_2m"),
                    "precipitacao_mm": atual.get("precipitation"),
                    "velocidadeVento_kmh": atual.get("wind_speed_10m"),
                    "codigoClima": atual.get("weather_code"),
                },
                "previsao7dias": []
            }

            datas = diario.get("time", [])
            temp_max = diario.get("temperature_2m_max", [])
            temp_min = diario.get("temperature_2m_min", [])
            precip = diario.get("precipitation_sum", [])
            nascerSol = diario.get("sunrise", [])
            porSol = diario.get("sunset", [])

            for i in range(len(datas)):
                resultado["previsao7dias"].append({
                    "data": datas[i],
                    "temperaturaMaxima": temp_max[i] if i < len(temp_max) else None,
                    "temperaturaMinima": temp_min[i] if i < len(temp_min) else None,
                    "precipitacao_mm": precip[i] if i < len(precip) else None,
                    "nascerDoSol": nascerSol[i] if i < len(nascerSol) else None,
                    "porDoSol": porSol[i] if i < len(porSol) else None,
                })

            return resultado

        except Exception as e:
            print(f"[ClimaAPI] Erro ao processar dados meteorológicos: {e}")
            return False

    @staticmethod
    def obter_nivel_rios(rio: str = None) -> dict | bool:
        """
        Retorna a previsão de vazão/nível dos rios do Amazonas usando a API GloFAS (Open-Meteo Flood API).
        Se 'rio' for None, retorna dados de TODOS os rios cadastrados.
        Retorna um dicionário com os dados ou False em caso de erro.
        """
        dados_locais = ClimaAPI._carregar_dados_locais()
        rios_disponiveis = dados_locais.get("RIOS_AMAZONAS", {})
        
        rios_consulta = {}
        if rio is not None:
            if rio not in rios_disponiveis:
                print(f"[ClimaAPI] Erro: Rio '{rio}' não cadastrado. Rios disponíveis: {list(rios_disponiveis.keys())}")
                return False
            rios_consulta = {rio: rios_disponiveis[rio]}
        else:
            rios_consulta = rios_disponiveis

        resultado = {
            "dataConsulta": str(date.today()),
            "rios": {}
        }

        for nome_rio, coord in rios_consulta.items():
            url = (
                f"https://flood-api.open-meteo.com/v1/flood?"
                f"latitude={coord['lat']}&longitude={coord['lon']}"
                f"&daily=river_discharge,river_discharge_mean,river_discharge_max,river_discharge_min"
                f"&forecast_days=7"
            )

            dados_brutos = ClimaAPI._fazer_requisicao(url)
            if not dados_brutos:
                resultado["rios"][nome_rio] = {"erro": "Falha na requisição"}
                continue

            try:
                diario = dados_brutos.get("daily", {})
                datas = diario.get("time", [])
                vazao = diario.get("river_discharge", [])
                vazao_media = diario.get("river_discharge_mean", [])
                vazao_max = diario.get("river_discharge_max", [])
                vazao_min = diario.get("river_discharge_min", [])

                previsoes = []
                for i in range(len(datas)):
                    previsoes.append({
                        "data": datas[i],
                        "vazao_m3s": vazao[i] if i < len(vazao) else None,
                        "vazaoMedia_m3s": vazao_media[i] if i < len(vazao_media) else None,
                        "vazaoMaxima_m3s": vazao_max[i] if i < len(vazao_max) else None,
                        "vazaoMinima_m3s": vazao_min[i] if i < len(vazao_min) else None,
                    })

                resultado["rios"][nome_rio] = {
                    "coordenadas": coord,
                    "previsao7dias": previsoes
                }

            except Exception as e:
                resultado["rios"][nome_rio] = {"erro": str(e)}

        return resultado


# =================================================================
#  TESTE DIRETO (executar: python -m br.com.pdv.src.apis.meteorologia.clima)
# =================================================================
if __name__ == "__main__":
    print("=" * 60)
    print(" TESTE API METEOROLÓGICA - AMAZONAS ")
    print("=" * 60)

    # Teste 1: Previsão do Tempo
    print("\n[TESTE 1] Previsão do Tempo para Manaus:")
    tempo = ClimaAPI.obter_previsao_tempo("Manaus")
    if tempo:
        print(f"  Temperatura atual: {tempo['atual']['temperatura']}°C")
        print(f"  Sensação Térmica: {tempo['atual']['sensacaoTermica']}°C")
        print(f"  Umidade: {tempo['atual']['umidadeRelativa']}%")
        print(f"  Precipitação: {tempo['atual']['precipitacao_mm']} mm")
        print(f"\n  Previsão 7 dias:")
        for dia in tempo["previsao7dias"]:
            print(f"    {dia['data']}: Min {dia['temperaturaMinima']}°C / Max {dia['temperaturaMaxima']}°C | Chuva: {dia['precipitacao_mm']} mm")

    # Teste 2: Nível do Rio Negro
    print("\n" + "-" * 60)
    print("[TESTE 2] Nível do Rio Negro (Manaus):")
    rios = ClimaAPI.obter_nivel_rios("Rio Negro (Manaus)")
    if rios:
        for nome, dados in rios["rios"].items():
            if "erro" not in dados:
                print(f"  {nome}:")
                for dia in dados["previsao7dias"]:
                    print(f"    {dia['data']}: Vazão {dia['vazao_m3s']} m³/s (Média: {dia['vazaoMedia_m3s']})")
            else:
                print(f"  {nome}: {dados['erro']}")

    print("\n" + "=" * 60)
    print(" TESTES FINALIZADOS")
    print("=" * 60)
