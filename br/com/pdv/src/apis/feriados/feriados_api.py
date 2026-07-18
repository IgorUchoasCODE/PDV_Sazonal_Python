"""
API de Feriados Nacionais e Pontos Facultativos do Brasil
Utiliza a BrasilAPI (gratuita, sem chave de API necessária)
- Feriados: https://brasilapi.com.br/api/feriados/v1/{ano}

Inclui também uma base local de pontos facultativos e feriados estaduais do Amazonas.
"""
import urllib.request
import json
from datetime import date

# Base local de Pontos Facultativos Nacionais (normalmente definidos por decreto)
# e feriados estaduais do Amazonas
PONTOS_FACULTATIVOS = {
    2025: [
        {"data": "2025-03-03", "nome": "Carnaval (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2025-03-04", "nome": "Carnaval (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2025-03-05", "nome": "Quarta-feira de Cinzas (até 14h)", "tipo": "facultativo"},
        {"data": "2025-06-19", "nome": "Corpus Christi (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2025-10-28", "nome": "Dia do Servidor Público (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2025-12-24", "nome": "Véspera de Natal (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2025-12-31", "nome": "Véspera de Ano Novo (Ponto Facultativo)", "tipo": "facultativo"},
    ],
    2026: [
        {"data": "2026-02-16", "nome": "Carnaval (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2026-02-17", "nome": "Carnaval (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2026-02-18", "nome": "Quarta-feira de Cinzas (até 14h)", "tipo": "facultativo"},
        {"data": "2026-06-04", "nome": "Corpus Christi (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2026-10-28", "nome": "Dia do Servidor Público (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2026-12-24", "nome": "Véspera de Natal (Ponto Facultativo)", "tipo": "facultativo"},
        {"data": "2026-12-31", "nome": "Véspera de Ano Novo (Ponto Facultativo)", "tipo": "facultativo"},
    ]
}

# Feriados Estaduais do Amazonas
FERIADOS_AMAZONAS = [
    {"data_recorrente": "09-05", "nome": "Elevação do Amazonas à Categoria de Província", "tipo": "estadual"},
    {"data_recorrente": "11-20", "nome": "Dia da Consciência Negra", "tipo": "estadual"},
    {"data_recorrente": "12-08", "nome": "Dia de Nossa Senhora da Conceição (Padroeira de Manaus)", "tipo": "municipal_manaus"},
    {"data_recorrente": "10-24", "nome": "Aniversário de Manaus", "tipo": "municipal_manaus"},
]


def _fazer_requisicao(url: str) -> list | bool:
    """Faz uma requisição HTTP GET e retorna o JSON."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PDV_Sazonal_Python/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            return dados
    except Exception as e:
        print(f"Erro na requisição para {url}: {e}")
        return False


def obter_feriados_nacionais(ano: int = None) -> dict | bool:
    """
    Retorna os feriados nacionais do ano informado via BrasilAPI.
    Se 'ano' for None, usa o ano corrente.
    Retorna um dicionário organizado por mês.
    """
    if ano is None:
        ano = date.today().year

    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
    dados_brutos = _fazer_requisicao(url)

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
        print(f"Erro ao processar feriados: {e}")
        return False


def obter_pontos_facultativos(ano: int = None) -> dict:
    """
    Retorna os pontos facultativos do ano informado (base local).
    """
    if ano is None:
        ano = date.today().year

    facultativos = PONTOS_FACULTATIVOS.get(ano, [])

    return {
        "ano": ano,
        "fonte": "Base Local (Decreto Federal)",
        "totalPontosFacultativos": len(facultativos),
        "pontosFacultativos": facultativos
    }


def obter_feriados_amazonas(ano: int = None) -> dict:
    """
    Retorna os feriados estaduais do Amazonas e municipais de Manaus.
    """
    if ano is None:
        ano = date.today().year

    feriados_ano = []
    for f in FERIADOS_AMAZONAS:
        feriados_ano.append({
            "data": f"{ano}-{f['data_recorrente']}",
            "nome": f["nome"],
            "tipo": f["tipo"],
        })

    return {
        "ano": ano,
        "estado": "Amazonas",
        "fonte": "Base Local (Legislação Estadual/Municipal)",
        "totalFeriados": len(feriados_ano),
        "feriados": feriados_ano
    }


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

    nacionais = obter_feriados_nacionais(ano)
    facultativos = obter_pontos_facultativos(ano)
    estaduais = obter_feriados_amazonas(ano)

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
    nacionais = obter_feriados_nacionais(ano_teste)
    if nacionais:
        for f in nacionais["feriados"]:
            print(f"  {f['data']} | {f['nome']} ({f['tipo']})")
    
    # Teste 2: Pontos Facultativos
    print(f"\n[TESTE 2] Pontos Facultativos de {ano_teste}:")
    facult = obter_pontos_facultativos(ano_teste)
    for f in facult["pontosFacultativos"]:
        print(f"  {f['data']} | {f['nome']}")

    # Teste 3: Feriados Estaduais
    print(f"\n[TESTE 3] Feriados Estaduais do Amazonas ({ano_teste}):")
    estaduais = obter_feriados_amazonas(ano_teste)
    for f in estaduais["feriados"]:
        print(f"  {f['data']} | {f['nome']} ({f['tipo']})")

    # Teste 4: Calendário Completo
    print(f"\n[TESTE 4] Calendário Completo Unificado ({ano_teste}):")
    cal = obter_calendario_completo(ano_teste)
    if cal:
        print(f"  Total de eventos no ano: {cal['totalEventos']}")
        for f in cal["calendario"]:
            print(f"  {f['data']} | {f['nome']} ({f['tipo']})")

    print("\n" + "=" * 60)
    print(" TESTES FINALIZADOS")
    print("=" * 60)
