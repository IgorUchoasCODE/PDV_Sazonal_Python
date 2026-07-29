"""
API de Eventos e Geolocalização — PDV Sazonal Manaus/AM
Consome APIs reais para obter eventos públicos e privados na região de Manaus:

- Eventos públicos/culturais:
  • API SALIC (Lei Rouanet): https://api.salic.cultura.gov.br/v1/projetos/
  • Mapas Culturais: https://mapas.cultura.gov.br/api/event/find

- Eventos privados/comerciais:
  • Sympla API: https://api.sympla.com.br/public/v4/ (requer s_token)

- Geolocalização via IP: https://ipapi.co (gratuita, sem chave para uso básico)

Todas as respostas são normalizadas na dataclass `Evento` para facilitar o uso no PDV.
"""
import urllib.request
import urllib.parse
import json
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from typing import Optional

try:
    from br.com.pdv.src.apis.keyApis import SYMPLA_TOKEN
except ImportError:
    SYMPLA_TOKEN = []


# =====================================================================
#  DATACLASS DE NORMALIZAÇÃO
# =====================================================================

@dataclass
class Evento:
    """
    Classe padronizada que sintetiza eventos de todas as fontes.
    Qualquer API consumida deve mapear seus dados para esta estrutura.
    """
    nome: str
    data_inicio: str                    # Formato: "YYYY-MM-DD"
    data_fim: Optional[str] = None      # Formato: "YYYY-MM-DD" ou None
    horario: Optional[str] = None       # Formato: "HH:MM" ou None
    local: Optional[str] = None         # Nome do espaço / venue
    cidade: str = "Manaus"
    estado: str = "AM"
    tipo: str = "publico"               # "publico", "privado", "cultural", "corporativo"
    fonte: str = ""                     # "salic", "mapas_culturais", "sympla"
    descricao: Optional[str] = None     # Descrição breve do evento
    preco: Optional[str] = None         # "Gratuito", "R$ 50,00", etc.

    def to_dict(self) -> dict:
        """Converte o evento para dicionário (útil para serialização JSON no PDV)."""
        return asdict(self)


# =====================================================================
#  CLASSE PRINCIPAL — AGREGADOR DE EVENTOS
# =====================================================================

class EventosAPI:
    """
    Agregador de eventos para o PDV Sazonal.
    Consome múltiplas APIs (públicas e privadas) e normaliza os dados
    na dataclass `Evento`.

    Uso básico:
        api = EventosAPI()
        todos = api.obter_todos_eventos()
        for ev in todos:
            print(ev.nome, ev.data_inicio, ev.local)
    """

    # URLs das APIs
    _URL_SALIC = "http://api.salic.cultura.gov.br/api/v1/projetos"
    _URL_MAPAS_CULTURAIS = "https://mapas.cultura.gov.br/api"
    _URL_SYMPLA = "https://api.sympla.com.br/public/v4/events"

    def __init__(
        self,
        cidade: str = "Manaus",
        uf: str = "AM",
        timeout: int = 15,
        sympla_token: Optional[str] = None,
    ):
        """
        Args:
            cidade: Cidade alvo para filtragem de eventos.
            uf: Sigla do estado (UF).
            timeout: Timeout em segundos para requisições HTTP.
            sympla_token: Token de acesso da API Sympla (s_token). Opcional.
        """
        self.cidade = cidade
        self.uf = uf
        self.timeout = timeout
        self.sympla_token = sympla_token

    # -----------------------------------------------------------------
    #  MÉTODO HTTP INTERNO
    # -----------------------------------------------------------------

    def _fazer_requisicao(
        self, url: str, headers: Optional[dict] = None, silencioso: bool = False
    ) -> dict | list | bool:
        """Faz uma requisição HTTP GET e retorna o JSON parseado."""
        try:
            cabecalhos = {"User-Agent": "PDV_Sazonal_Python/1.0"}
            if headers:
                cabecalhos.update(headers)

            req = urllib.request.Request(url, headers=cabecalhos)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                return dados
        except Exception as e:
            if not silencioso:
                print(f"[EventosAPI] Erro na requisição para {url}: {e}")
            return False

    # -----------------------------------------------------------------
    #  FONTE 1: API SALIC (Ministério da Cultura — Lei Rouanet)
    # -----------------------------------------------------------------

    def _obter_eventos_salic(self, limite: int = 50) -> list[Evento]:
        """
        Consome a API do SALIC para obter projetos culturais aprovados
        pela Lei Rouanet no município/UF configurados.

        Endpoint: GET /api/v1/projetos?UF={uf}&municipio={cidade}&limit={limite}&format=json
        Docs: https://api.salic.cultura.gov.br/docs

        Campos retornados pela API:
          PRONAC, nome, situacao, data_inicio, data_termino, municipio, UF,
          segmento, resumo, local_realizacao (lista de dicts com municipio/sigla_uf)

        ⚠️ Esta API pode estar instável (404/503). O fallback é retornar lista vazia.
        """
        params = urllib.parse.urlencode({
            "UF": self.uf,
            "municipio": self.cidade,
            "limit": limite,
            "format": "json",
        })
        url = f"{self._URL_SALIC}?{params}"

        dados = self._fazer_requisicao(url, silencioso=True)
        if not dados or not isinstance(dados, dict):
            return []

        eventos = []
        # A API SALIC retorna projetos em _embedded.projetos (formato HAL+JSON)
        projetos = dados.get("_embedded", {}).get("projetos", [])
        if not projetos and isinstance(dados, list):
            projetos = dados

        for projeto in projetos:
            nome = projeto.get("nome") or projeto.get("PRONAC", "Projeto sem nome")
            data_inicio = projeto.get("data_inicio", "")
            data_fim = projeto.get("data_termino")
            municipio = projeto.get("municipio", self.cidade)
            segmento = projeto.get("segmento", "")
            resumo = projeto.get("resumo", "")

            # Extrai o local de realização (pode ter múltiplas cidades)
            local_realizacao = projeto.get("local_realizacao", [])
            local_str = None
            if isinstance(local_realizacao, list) and local_realizacao:
                # Filtra locais em Manaus/AM quando possível
                locais_cidade = [
                    loc for loc in local_realizacao
                    if loc.get("municipio", "").lower() == self.cidade.lower()
                    or loc.get("sigla_uf", "").upper() == self.uf.upper()
                ]
                if locais_cidade:
                    loc = locais_cidade[0]
                    local_str = f"{loc.get('municipio', '')} - {loc.get('uf', '')}"
                else:
                    # Usa o primeiro local disponível
                    loc = local_realizacao[0]
                    local_str = f"{loc.get('municipio', '')} - {loc.get('uf', '')}"

            # Monta descrição a partir de segmento e resumo
            descricao_parts = []
            if segmento:
                descricao_parts.append(f"Segmento: {segmento}")
            if resumo:
                descricao_parts.append(resumo[:200])

            # Normaliza a data para YYYY-MM-DD se possível
            data_inicio_norm = self._normalizar_data(data_inicio)
            data_fim_norm = self._normalizar_data(data_fim) if data_fim else None

            if data_inicio_norm:
                eventos.append(Evento(
                    nome=nome,
                    data_inicio=data_inicio_norm,
                    data_fim=data_fim_norm,
                    horario=None,
                    local=local_str,
                    cidade=municipio,
                    estado=self.uf,
                    tipo="publico",
                    fonte="salic",
                    descricao=" | ".join(descricao_parts) if descricao_parts else None,
                    preco="Gratuito (Incentivo Fiscal)",
                ))

        return eventos

    # -----------------------------------------------------------------
    #  FONTE 2: MAPAS CULTURAIS (Plataforma Nacional de Mapeamento Cultural)
    # -----------------------------------------------------------------

    def _obter_eventos_mapas_culturais(self, limite: int = 50) -> list[Evento]:
        """
        Consome a API do Mapas Culturais para obter eventos culturais.

        Estratégia em 2 passos:
          1. GET /api/event/find — lista de eventos com nome e descrição
          2. GET /api/eventOccurrence/find — datas, horários e locais (vinculados aos eventos)

        ⚠️ A instância federal pode retornar 403. Fallback: lista vazia.
        """
        # Passo 1: Buscar eventos
        params_eventos = urllib.parse.urlencode({
            "@select": "id,name,shortDescription,classificacaoEtaria",
            "@keyword": self.cidade,
            "@limit": limite,
            "@order": "id DESC",
        })
        url_eventos = f"{self._URL_MAPAS_CULTURAIS}/event/find?{params_eventos}"
        dados_eventos = self._fazer_requisicao(url_eventos, silencioso=True)

        if not dados_eventos or not isinstance(dados_eventos, list):
            return []

        # Mapeia id -> dados do evento
        mapa_eventos = {}
        for ev in dados_eventos:
            ev_id = ev.get("id")
            if ev_id:
                mapa_eventos[ev_id] = {
                    "nome": ev.get("name", "Evento sem nome"),
                    "descricao": ev.get("shortDescription"),
                    "classificacao": ev.get("classificacaoEtaria"),
                }

        if not mapa_eventos:
            return []

        # Passo 2: Buscar ocorrências (datas e locais) para esses eventos
        params_ocorrencias = urllib.parse.urlencode({
            "@select": "id,eventId,space.name,space.En_Municipio,rule",
            "@limit": limite * 2,
            "@order": "id DESC",
        })
        url_ocorrencias = f"{self._URL_MAPAS_CULTURAIS}/eventOccurrence/find?{params_ocorrencias}"
        dados_ocorrencias = self._fazer_requisicao(url_ocorrencias, silencioso=True)

        eventos = []

        if dados_ocorrencias and isinstance(dados_ocorrencias, list):
            for occ in dados_ocorrencias:
                event_id = occ.get("eventId")
                info_evento = mapa_eventos.get(event_id)

                if not info_evento:
                    continue

                rule = occ.get("rule", {}) or {}
                space = occ.get("space", {}) or {}

                data_inicio = rule.get("startsOn", "")
                horario = rule.get("startsAt")
                preco = rule.get("price")
                local_nome = space.get("name", "Local não informado")
                municipio = space.get("En_Municipio") or self.cidade

                data_inicio_norm = self._normalizar_data(data_inicio)
                data_fim_str = rule.get("until")
                data_fim_norm = self._normalizar_data(data_fim_str) if data_fim_str else None

                if data_inicio_norm:
                    eventos.append(Evento(
                        nome=info_evento["nome"],
                        data_inicio=data_inicio_norm,
                        data_fim=data_fim_norm,
                        horario=horario,
                        local=local_nome,
                        cidade=municipio if municipio and municipio != "value" else self.cidade,
                        estado=self.uf,
                        tipo="publico",
                        fonte="mapas_culturais",
                        descricao=info_evento.get("descricao"),
                        preco=preco,
                    ))

                # Remove do mapa para não duplicar
                mapa_eventos.pop(event_id, None)

        # Eventos sem ocorrência (sem data definida) — ainda úteis para o PDV saber que existem
        for ev_id, info in mapa_eventos.items():
            eventos.append(Evento(
                nome=info["nome"],
                data_inicio="",
                data_fim=None,
                horario=None,
                local=None,
                cidade=self.cidade,
                estado=self.uf,
                tipo="publico",
                fonte="mapas_culturais",
                descricao=info.get("descricao"),
                preco=None,
            ))

        return eventos

    # -----------------------------------------------------------------
    #  FONTE 3: SYMPLA API (Eventos Privados / Shows / Festas)
    # -----------------------------------------------------------------

    def _obter_eventos_sympla(self, limite: int = 50) -> list[Evento]:
        """
        Consome a API da Sympla para obter eventos privados/comerciais.

        ⚠️ REQUER TOKEN: A API da Sympla exige um `s_token` (Bearer Token)
        no cabeçalho da requisição. Sem o token, esta fonte retorna lista vazia.

        Endpoint: GET /public/v4/events?city={cidade}&state={uf}
        Docs: https://developers.sympla.com.br/api-doc/
        """
        token = self.sympla_token or SYMPLA_TOKEN
        if not token:
            return []

        params = urllib.parse.urlencode({
            "page_size": limite,
            "city": self.cidade,
            "state": self.uf,
            "published": "true",
        })
        url = f"{self._URL_SYMPLA}?{params}"

        headers = {
            "s_token": token,
            "Accept": "application/json",
        }
        dados = self._fazer_requisicao(url, headers=headers, silencioso=True)

        if not dados or not isinstance(dados, dict):
            return []

        eventos = []
        lista_eventos = dados.get("data", [])

        for ev in lista_eventos:
            nome = ev.get("name", "Evento sem nome")
            data_inicio = ev.get("start_date", "")
            data_fim = ev.get("end_date")
            local_info = ev.get("address", {}) or {}
            local_nome = local_info.get("name") or ev.get("venue_name", "")
            cidade = local_info.get("city", self.cidade)

            # A Sympla retorna datas em ISO 8601 (ex: "2026-07-25T18:00:00-04:00")
            data_inicio_norm = self._normalizar_data(data_inicio)
            data_fim_norm = self._normalizar_data(data_fim) if data_fim else None

            horario = None
            if "T" in str(data_inicio):
                try:
                    horario = data_inicio.split("T")[1][:5]
                except (IndexError, AttributeError):
                    pass

            if data_inicio_norm:
                eventos.append(Evento(
                    nome=nome,
                    data_inicio=data_inicio_norm,
                    data_fim=data_fim_norm,
                    horario=horario,
                    local=local_nome,
                    cidade=cidade,
                    estado=self.uf,
                    tipo="privado",
                    fonte="sympla",
                    descricao=ev.get("detail"),
                    preco=None,
                ))

        return eventos

    # -----------------------------------------------------------------
    #  MÉTODOS PÚBLICOS — CONSULTAS CONSOLIDADAS
    # -----------------------------------------------------------------

    def obter_todos_eventos(self, limite: int = 50) -> list[Evento]:
        """
        Consolida eventos de TODAS as fontes disponíveis (públicos + privados).
        Se uma fonte falhar, as demais continuam normalmente.

        Returns:
            Lista de objetos Evento ordenados por data_inicio.
        """
        todos = []

        # Fonte 1: SALIC (projetos culturais / Lei Rouanet)
        try:
            salic = self._obter_eventos_salic(limite)
            todos.extend(salic)
        except Exception as e:
            print(f"[EventosAPI] Falha ao consultar SALIC: {e}")

        # Fonte 2: Mapas Culturais (eventos culturais públicos)
        try:
            mapas = self._obter_eventos_mapas_culturais(limite)
            todos.extend(mapas)
        except Exception as e:
            print(f"[EventosAPI] Falha ao consultar Mapas Culturais: {e}")

        # Fonte 3: Sympla (eventos privados/comerciais)
        try:
            sympla = self._obter_eventos_sympla(limite)
            todos.extend(sympla)
        except Exception as e:
            print(f"[EventosAPI] Falha ao consultar Sympla: {e}")

        # Ordena por data_inicio (eventos sem data ficam no final)
        todos.sort(key=lambda ev: ev.data_inicio or "9999-99-99")

        return todos

    def obter_eventos_publicos(self, limite: int = 50) -> list[Evento]:
        """Retorna apenas eventos públicos (SALIC + Mapas Culturais)."""
        todos = self.obter_todos_eventos(limite)
        return [ev for ev in todos if ev.tipo == "publico"]

    def obter_eventos_privados(self, limite: int = 50) -> list[Evento]:
        """Retorna apenas eventos privados (Sympla e similares)."""
        todos = self.obter_todos_eventos(limite)
        return [ev for ev in todos if ev.tipo == "privado"]

    def obter_eventos_por_data(
        self,
        data_inicio: str,
        data_fim: str,
        limite: int = 50,
    ) -> list[Evento]:
        """
        Filtra eventos que ocorrem dentro do intervalo de datas informado.

        Args:
            data_inicio: Data inicial no formato "YYYY-MM-DD".
            data_fim: Data final no formato "YYYY-MM-DD".
            limite: Limite de registros por fonte.

        Returns:
            Lista de Evento dentro do intervalo.
        """
        todos = self.obter_todos_eventos(limite)

        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            print("[EventosAPI] Formato de data inválido. Use YYYY-MM-DD.")
            return []

        filtrados = []
        for ev in todos:
            if not ev.data_inicio:
                continue
            try:
                dt_evento = datetime.strptime(ev.data_inicio, "%Y-%m-%d").date()
                if dt_inicio <= dt_evento <= dt_fim:
                    filtrados.append(ev)
            except ValueError:
                continue

        return filtrados

    def obter_eventos_proximos(self, dias: int = 30) -> list[Evento]:
        """
        Retorna eventos que ocorrem nos próximos 'dias' dias.

        Args:
            dias: Quantidade de dias à frente para buscar (padrão: 30).

        Returns:
            Lista de Evento nos próximos dias, ordenada por data.
        """
        hoje = date.today()
        data_fim = hoje + timedelta(days=dias)
        return self.obter_eventos_por_data(
            data_inicio=str(hoje),
            data_fim=str(data_fim),
        )

    # -----------------------------------------------------------------
    #  UTILITÁRIOS
    # -----------------------------------------------------------------

    @staticmethod
    def _normalizar_data(data_str: Optional[str]) -> Optional[str]:
        """
        Tenta normalizar uma string de data para o formato YYYY-MM-DD.
        Suporta formatos comuns retornados pelas APIs.
        """
        if not data_str or not isinstance(data_str, str):
            return None

        data_str = data_str.strip()

        # Já está no formato correto
        if len(data_str) == 10 and data_str[4] == "-" and data_str[7] == "-":
            return data_str

        # ISO 8601 com horário (ex: "2026-07-25T18:00:00Z" ou "2026-07-25T18:00:00-04:00")
        if "T" in data_str:
            return data_str.split("T")[0]

        # Formato brasileiro dd/mm/yyyy
        formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formatos:
            try:
                dt = datetime.strptime(data_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None


# =====================================================================
#  GEOLOCALIZAÇÃO VIA IP (mantida do módulo original)
# =====================================================================

def _fazer_requisicao_geo(url: str, silencioso: bool = False) -> dict | bool:
    """Faz uma requisição HTTP GET e retorna o JSON como dicionário."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PDV_Sazonal_Python/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            return dados
    except Exception as e:
        if not silencioso:
            print(f"Erro na requisição para {url}: {e}")
        return False


def obter_localizacao() -> dict | bool:
    """
    Obtém a localização atual do usuário baseada no IP público.
    Tenta primeiro a API ipapi.co e, se falhar (por bloqueio DNS/outage), usa ip-api.com.
    """
    # Tentativa 1: ipapi.co (HTTPS)
    url1 = "https://ipapi.co/json/"
    dados = _fazer_requisicao_geo(url1, silencioso=True)

    if dados and isinstance(dados, dict) and "city" in dados:
        try:
            return {
                "ip": dados.get("ip"),
                "cidade": dados.get("city"),
                "regiao": dados.get("region"),
                "estado_sigla": dados.get("region_code"),
                "pais": dados.get("country_name"),
                "pais_codigo": dados.get("country_code"),
                "latitude": dados.get("latitude"),
                "longitude": dados.get("longitude"),
                "timezone": dados.get("timezone"),
                "moeda": dados.get("currency"),
                "provedor": dados.get("org"),
            }
        except Exception:
            pass

    # Tentativa 2 (Fallback): ip-api.com (HTTP - versão gratuita não aceita HTTPS)
    url2 = "http://ip-api.com/json/"
    dados = _fazer_requisicao_geo(url2, silencioso=True)

    if dados and isinstance(dados, dict) and dados.get("status") == "success":
        try:
            return {
                "ip": dados.get("query"),
                "cidade": dados.get("city"),
                "regiao": dados.get("regionName"),
                "estado_sigla": dados.get("region"),
                "pais": dados.get("country"),
                "pais_codigo": dados.get("countryCode"),
                "latitude": dados.get("lat"),
                "longitude": dados.get("lon"),
                "timezone": dados.get("timezone"),
                "moeda": "BRL",  # O ip-api não retorna moeda, assumimos BRL
                "provedor": dados.get("isp"),
            }
        except Exception:
            pass

    print("Erro (Barreira): Não foi possível obter a localização através de nenhuma das APIs públicas.")
    return False












# =====================================================================
#  TESTE DIRETO (executar: python -m br.com.pdv.src.apis.eventos.eventos_api)
# =====================================================================
if __name__ == "__main__":
    print("=" * 65)
    print(" TESTE API DE EVENTOS - PDV SAZONAL MANAUS/AM ")
    print("=" * 65)

    api = EventosAPI(cidade="Manaus", uf="AM")

    # Teste 1: Geolocalização via IP
    print("\n[TESTE 1] Obtendo Localizacao pelo IP...")
    loc = obter_localizacao()
    if loc:
        print(f"  Cidade: {loc['cidade']}")
        print(f"  Estado: {loc['regiao']} ({loc['estado_sigla']})")
        print(f"  Pais: {loc['pais']}")
        print(f"  Coordenadas: {loc['latitude']}, {loc['longitude']}")
        print(f"  Timezone: {loc['timezone']}")
        print(f"  Provedor: {loc['provedor']}")
    else:
        print("  [!] Nao foi possivel obter a localizacao.")

    # Teste 2: Todos os eventos (todas as fontes)
    print(f"\n[TESTE 2] Buscando todos os eventos para {api.cidade}/{api.uf}...")
    todos = api.obter_todos_eventos(limite=20)
    print(f"  Total de eventos encontrados: {len(todos)}")
    for ev in todos[:10]:  # Mostra ate 10
        print(f"\n  [DATA]   {ev.data_inicio or 'Nao definida'}")
        print(f"  [EVENTO] {ev.nome}")
        print(f"  [LOCAL]  {ev.local or 'Nao informado'}")
        print(f"  [TIPO]   {ev.tipo} | Fonte: {ev.fonte}")
        if ev.horario:
            print(f"  [HORA]   {ev.horario}")
        if ev.preco:
            print(f"  [PRECO]  {ev.preco}")
        if ev.descricao:
            print(f"  [DESC]   {ev.descricao[:100]}...")
        print("  " + "-" * 50)

    # Teste 3: Eventos proximos (30 dias)
    print(f"\n[TESTE 3] Eventos nos proximos 30 dias:")
    proximos = api.obter_eventos_proximos(0)
    if proximos:
        for ev in proximos[:5]:
            print(f"  {ev.data_inicio} | {ev.nome} ({ev.fonte})")
    else:
        print("  Nenhum evento encontrado nos proximos 30 dias.")

    # Teste 4: Conversao para dict (uso no PDV)
    print(f"\n[TESTE 4] Exemplo de serializacao para dict (uso no PDV):")
    if todos:
        exemplo = todos[0].to_dict()
        print(f"  {json.dumps(exemplo, indent=4, ensure_ascii=True)}")
    else:
        print("  Sem eventos para demonstrar serializacao.")

    # Teste 5: Status das fontes
    print(f"\n[TESTE 5] Resumo por fonte:")
    fontes = {}
    for ev in todos:
        fontes[ev.fonte] = fontes.get(ev.fonte, 0) + 1
    for fonte, qtd in fontes.items():
        print(f"  {fonte}: {qtd} evento(s)")
    if not fontes:
        print("  Nenhuma fonte retornou dados (APIs podem estar instaveis).")

    print("\n" + "=" * 65)
    print(" TESTES FINALIZADOS")
    print("=" * 65)
