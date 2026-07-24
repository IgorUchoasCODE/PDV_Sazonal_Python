from datetime import date, datetime
import sqlite3
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.apis.meteorologia.clima import ClimaAPI
from br.com.pdv.src.apis.eventos.eventos_api import EventosAPI
from br.com.pdv.src.apis.feriados.feriados_api import FeriadosAPI


class GerenciadorSazonal:
    """
    Classe estática gerenciadora das APIs Sazonais (Clima, Rios, Eventos e Feriados).
    Possui dois objetivos principais:
      1. Gerenciar e agregar as APIs em indicativos claros (clima, rio, chuva, temperatura, eventos próximos).
      2. Salvar snapshots sazonais no banco de dados vinculados exclusivamente a Notas de Venda (2) e Perda (4/5).
    """

    # Filtro estrito: Apenas Venda (2) e Perda (4/5)
    TIPOS_NOTAS_PERMITIDOS = {2, 4, 5}

    DEFAULT_RIO = "Rio Negro (Manaus)"
    DEFAULT_CIDADE = "Manaus"

    @classmethod
    def obter_indicadores_sazonais(cls, cidade: str = DEFAULT_CIDADE, rio: str = DEFAULT_RIO) -> dict:
        """
        Objetivo 2: Consome as APIs de Clima/Rios, Eventos e Feriados e formata indicativos claros.
        
        Retorna:
          - temperatura_atual (float)
          - temperatura_min_semana (float)
          - temperatura_max_semana (float)
          - indicador_clima ('QUENTE' | 'FRIO' | 'AMENO') -> Conforme constraint do banco
          - clima_descricao (str) -> Descrição amigável
          - indicador_chuva ('SECO' | 'MODERADO' | 'CHUVOSO') -> Conforme constraint do banco
          - vai_chover ('Sim' | 'Não')
          - indicador_rio ('NORMAL' | 'CHEIA' | 'SECA') -> Conforme constraint do banco
          - nivel_rio_atual (float)
          - nivel_rio_previsao_semana (float)
          - quantidade_eventos_proximos (int)
          - detalhes_eventos (list)
        """
        data_hoje = date.today()

        # ---------------------------------------------------------------------
        # 1. API DE METEOROLOGIA E RIOS (ClimaAPI)
        # ---------------------------------------------------------------------
        clima_dados = ClimaAPI.obter_previsao_tempo(cidade)
        rio_dados = ClimaAPI.obter_nivel_rios(rio)

        temp_atual = 28.0
        temp_min = 24.0
        temp_max = 33.0
        precip_mm = 0.0
        precip_semana = 0.0

        if clima_dados and isinstance(clima_dados, dict):
            atual = clima_dados.get("atual", {})
            temp_atual = float(atual.get("temperatura", 28.0) or 28.0)
            precip_mm = float(atual.get("precipitacao_mm", 0.0) or 0.0)

            previsao_7d = clima_dados.get("previsao7dias", [])
            if previsao_7d:
                mins = [p["temperaturaMinima"] for p in previsao_7d if p.get("temperaturaMinima") is not None]
                maxs = [p["temperaturaMaxima"] for p in previsao_7d if p.get("temperaturaMaxima") is not None]
                precips = [p["precipitacao_mm"] for p in previsao_7d if p.get("precipitacao_mm") is not None]

                if mins: temp_min = min(mins)
                if maxs: temp_max = max(maxs)
                if precips: precip_semana = sum(precips)

        # Mapeamento do Indicador de Clima (Respeitando CHECK: 'QUENTE', 'FRIO', 'AMENO')
        if temp_atual >= 29.0:
            indicador_clima = "QUENTE"
            clima_desc = f"Quente ({temp_atual:.1f}°C)"
        elif temp_atual < 24.0:
            indicador_clima = "FRIO"
            clima_desc = f"Frio / Ameno ({temp_atual:.1f}°C)"
        else:
            indicador_clima = "AMENO"
            clima_desc = f"Morno / Ameno ({temp_atual:.1f}°C)"

        # Mapeamento do Indicador de Chuva (Respeitando CHECK: 'SECO', 'MODERADO', 'CHUVOSO')
        if precip_mm >= 15.0 or precip_semana >= 35.0:
            indicador_chuva = "CHUVOSO"
            vai_chover = "Sim"
        elif precip_mm >= 2.0 or precip_semana >= 5.0:
            indicador_chuva = "MODERADO"
            vai_chover = "Sim"
        else:
            indicador_chuva = "SECO"
            vai_chover = "Não"

        # Mapeamento do Indicador do Rio (Respeitando CHECK: 'SECA', 'NORMAL', 'CHEIA')
        vazao_atual = 0.0
        vazao_semana = 0.0

        if rio_dados and isinstance(rio_dados, dict):
            rios = rio_dados.get("rios", {})
            info_rio = rios.get(rio, {})
            prev_rio = info_rio.get("previsao7dias", [])
            if prev_rio:
                vazoes = [p["vazao_m3s"] for p in prev_rio if p.get("vazao_m3s") is not None]
                if vazoes:
                    vazao_atual = float(vazoes[0])
                    vazao_semana = float(sum(vazoes) / len(vazoes))

        if vazao_atual > 25000:
            indicador_rio = "CHEIA"
        elif vazao_atual < 5000 and vazao_atual > 0:
            indicador_rio = "SECA"
        else:
            indicador_rio = "NORMAL"

        # ---------------------------------------------------------------------
        # 2. API DE FERIADOS E EVENTOS PRÓXIMOS (FeriadosAPI & EventosAPI)
        # ---------------------------------------------------------------------
        eventos_proximos = []

        # Consulta Feriados Nacionais e Locais
        try:
            res_feriados = FeriadosAPI.obter_feriados_nacionais(data_hoje.year)
            if res_feriados and isinstance(res_feriados, dict):
                feriados_lista = res_feriados.get("feriados", [])
                for f in feriados_lista:
                    d_f = f.get("data")
                    if isinstance(d_f, str):
                        try:
                            data_feriado = datetime.strptime(d_f, "%Y-%m-%d").date()
                            if 0 <= (data_feriado - data_hoje).days <= 7:
                                eventos_proximos.append(f"Feriado: {f.get('nome')} ({d_f})")
                        except Exception:
                            pass
        except Exception as e:
            print(f"[GerenciadorSazonal] Aviso ao consultar FeriadosAPI: {e}")

        # Consulta Eventos da Região
        try:
            api_ev = EventosAPI(cidade=cidade)
            evs = api_ev.obter_todos_eventos()
            if evs and isinstance(evs, list):
                for ev in evs:
                    nome_ev = getattr(ev, "nome", str(ev))
                    eventos_proximos.append(f"Evento: {nome_ev}")
        except Exception as e:
            print(f"[GerenciadorSazonal] Aviso ao consultar EventosAPI: {e}")

        qtd_eventos_proximos = len(eventos_proximos)

        return {
            "cidade": cidade,
            "rio": rio,
            "temperatura_atual": round(temp_atual, 1),
            "temperatura_min_semana": round(temp_min, 1),
            "temperatura_max_semana": round(temp_max, 1),
            "indicador_clima": indicador_clima,       # 'QUENTE' | 'FRIO' | 'AMENO'
            "clima_descricao": clima_desc,
            "indicador_chuva": indicador_chuva,       # 'SECO' | 'MODERADO' | 'CHUVOSO'
            "vai_chover": vai_chover,                 # 'Sim' | 'Não'
            "precipitacao_mm": round(precip_mm, 2),
            "precipitacao_previsao_semana": round(precip_semana, 2),
            "indicador_rio": indicador_rio,           # 'NORMAL' | 'CHEIA' | 'SECA'
            "nivel_rio_atual": round(vazao_atual, 2),
            "nivel_rio_previsao_semana": round(vazao_semana, 2),
            "quantidade_eventos_proximos": qtd_eventos_proximos,
            "detalhes_eventos": eventos_proximos
        }

    @classmethod
    def salvar_snapshot_sazonal(cls, id_fluxo_nota: int, cidade: str = DEFAULT_CIDADE, rio: str = DEFAULT_RIO) -> bool:
        """
        Objetivo 1: Salva o snapshot sazonal no banco vinculando ao id_fluxo_nota.
        
        REGRA RIGOROSA: Salva SOMENTE se a nota for de VENDA (id_tipoNota = 2) ou PERDA (id_tipoNota = 4 ou 5).
        Notas de Compra (1) ou Devolução (3) são ignoradas.
        """
        try:
            nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id_fluxo_nota)
            if not nota:
                print(f"[GerenciadorSazonal] Erro: Nota de estoque ID {id_fluxo_nota} não encontrada no banco.")
                return False

            id_tipo_nota = nota.get("id_tipoNota")
            if id_tipo_nota not in cls.TIPOS_NOTAS_PERMITIDOS:
                print(f"[GerenciadorSazonal] Snapshot IGNORADO: A Nota ID {id_fluxo_nota} é do tipo {id_tipo_nota}. Snapshots sazonais são gravados SOMENTE para Notas de Venda (2) e Perda (4/5).")
                return False

            # Obtém os indicativos das APIs
            ind = cls.obter_indicadores_sazonais(cidade, rio)
            data_hoje = str(date.today())

            # Insere no banco via DB.INSERT.SNAPSHOT_SAZONAL
            DB.INSERT.SNAPSHOT_SAZONAL.executar(
                id_fluxo_nota,
                data_hoje,
                ind["temperatura_atual"],
                ind["temperatura_min_semana"],
                ind["temperatura_max_semana"],
                ind["precipitacao_mm"],
                ind["precipitacao_previsao_semana"],
                ind["indicador_clima"],            # 'QUENTE', 'FRIO' ou 'AMENO'
                ind["nivel_rio_atual"],
                ind["nivel_rio_previsao_semana"],
                ind["indicador_rio"],              # 'SECA', 'NORMAL' ou 'CHEIA'
                ind["indicador_chuva"],            # 'SECO', 'MODERADO' ou 'CHUVOSO'
                ind["quantidade_eventos_proximos"]
            )

            print(f"[GerenciadorSazonal] Snapshot Sazonal salvo com SUCESSO para Nota ID {id_fluxo_nota} (Tipo: {id_tipo_nota})")
            return True

        except Exception as e:
            print(f"[GerenciadorSazonal] Erro ao salvar snapshot sazonal para a nota {id_fluxo_nota}: {e}")
            return False


if __name__ == "__main__":
    print("=" * 80)
    print(" DEMONSTRAÇÃO DO GERENCIADOR SAZONAL ")
    print("=" * 80)

    # 1. Exibição dos Indicativos Claros
    ind = GerenciadorSazonal.obter_indicadores_sazonais()
    print("\n[INDICATIVOS SAZONAIS FORMATADOS]:")
    print(f"  * Clima: {ind['clima_descricao']} (Indicador Banco: {ind['indicador_clima']})")
    print(f"  * Temperatura Atual: {ind['temperatura_atual']}°C (Mín: {ind['temperatura_min_semana']}°C / Máx: {ind['temperatura_max_semana']}°C)")
    print(f"  * Vai Chover?: {ind['vai_chover']} (Precipitação: {ind['precipitacao_mm']} mm / Indicador Banco: {ind['indicador_chuva']})")
    print(f"  * Nível dos Rios: {ind['indicador_rio']} (Vazão Atual: {ind['nivel_rio_atual']} m³/s)")
    print(f"  * Quantidade de Eventos Próximos: {ind['quantidade_eventos_proximos']}")
    if ind["detalhes_eventos"]:
        for ev in ind["detalhes_eventos"]:
            print(f"     - {ev}")

    # 2. Teste do Filtro de Gravação para Notas
    print("\n[TESTE DE FILTRAGEM POR TIPO DE NOTA]:")
    print("\n1. Testando Nota de VENDA (ID 547, Tipo 2):")
    GerenciadorSazonal.salvar_snapshot_sazonal(547)

    print("\n2. Testando Nota de PERDA (ID 565, Tipo 4):")
    GerenciadorSazonal.salvar_snapshot_sazonal(565)

    print("\n3. Testando Nota de DEVOLUÇÃO (ID 556, Tipo 3 - DEVE SER IGNORADA):")
    GerenciadorSazonal.salvar_snapshot_sazonal(556)

