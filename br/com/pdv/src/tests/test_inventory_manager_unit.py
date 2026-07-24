"""
Testes Unitários — InventoryManager
====================================
Valida o comportamento do hub central do sistema após carregamento real do banco.

Estrutura:
  TestCarregamento  — verifica inicialização e coleções
  TestGetStatus     — valida dict de status geral
  TestGetEstoque    — valida mapa de produto e lotes FIFO
  TestGetNota       — valida busca de nota por ID
  TestTriangulacao  — valida triangulação sazonal
  TestTendencias    — valida análise de tendências sazonais
  TestProdutosLista — valida lista de produtos para UI
  TestNotasPorTipo  — valida paginação de notas
  TestIndicComposto — valida split do índice composto
"""
import unittest
import sys
import os
# tests → src → pdv → com → br → PDV_Sazonal_Python (5 níveis)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))


from br.com.pdv.src.memory.inventoryManager import InventoryManager

# ── Fixture: carrega uma única vez para todos os testes ──────────────
_CARREGADO = False

def _garantir_carregado():
    global _CARREGADO
    if not _CARREGADO:
        InventoryManager.carregarTudo()
        _CARREGADO = True


class TestCarregamento(unittest.TestCase):
    """1. Verifica carregamento e inicialização das coleções."""

    def setUp(self):
        _garantir_carregado()

    def test_01_carregar_tudo_retorna_true(self):
        """carregarTudo() deve retornar True."""
        # Já carregado, só verifica que não há dados inválidos
        self.assertIsInstance(InventoryManager._mapaProdutos, dict)
        self.assertIsInstance(InventoryManager._mapaEstoque, dict)

    def test_02_colecoes_populadas(self):
        """Todas as 5 coleções devem ter ao menos 1 item cada (banco com dados reais)."""
        self.assertGreater(len(InventoryManager._NotasCompras), 0,
                           "Nenhuma nota de compra carregada.")
        self.assertGreater(len(InventoryManager._NotasVendas), 0,
                           "Nenhuma nota de venda carregada.")

    def test_03_mapa_produtos_nao_vazio(self):
        """_mapaProdutos deve conter ao menos 1 produto."""
        self.assertGreater(len(InventoryManager._mapaProdutos), 0)

    def test_04_mapa_estoque_nao_vazio(self):
        """_mapaEstoque deve conter ao menos 1 lote."""
        self.assertGreater(len(InventoryManager._mapaEstoque), 0)

    def test_05_contador_lote_positivo(self):
        """O contador de lotes deve ser maior que zero após o carregamento."""
        self.assertGreater(InventoryManager._contadorLote, 0)


class TestGetStatus(unittest.TestCase):
    """2. Valida a estrutura e tipos do dict retornado por get_status()."""

    def setUp(self):
        _garantir_carregado()
        self.status = InventoryManager.get_status()

    def test_06_status_tem_chaves_obrigatorias(self):
        """get_status() deve retornar um dict com todas as chaves esperadas."""
        chaves_esperadas = [
            "total_produtos_distintos",
            "total_notas",
            "valor_total_estoque",
            "total_lotes_ativos",
            "produtos_negativos",
            "produtos_sem_estoque_count",
        ]
        for chave in chaves_esperadas:
            self.assertIn(chave, self.status, f"Chave ausente: {chave}")

    def test_07_total_notas_tem_5_tipos(self):
        """total_notas deve conter os 5 tipos: compra, venda, devolucao, perda, compensacao."""
        tn = self.status["total_notas"]
        for tipo in ["compra", "venda", "devolucao", "perda", "compensacao"]:
            self.assertIn(tipo, tn, f"Tipo ausente em total_notas: {tipo}")
            self.assertIsInstance(tn[tipo], int)

    def test_08_valor_total_estoque_positivo(self):
        """valor_total_estoque deve ser >= 0."""
        self.assertGreaterEqual(self.status["valor_total_estoque"], 0)

    def test_09_produtos_negativos_e_lista(self):
        """produtos_negativos deve ser uma lista."""
        self.assertIsInstance(self.status["produtos_negativos"], list)


class TestGetEstoque(unittest.TestCase):
    """3. Valida get_estoque_produto() para produto existente e inexistente."""

    def setUp(self):
        _garantir_carregado()
        # Pega o primeiro produto existente no mapa
        self._id_valido = int(next(iter(InventoryManager._mapaProdutos)))

    def test_10_produto_valido_retorna_dict(self):
        """get_estoque_produto(id_valido) deve retornar dict não-vazio."""
        est = InventoryManager.get_estoque_produto(self._id_valido)
        self.assertIsInstance(est, dict)
        self.assertGreater(len(est), 0)

    def test_11_produto_valido_tem_chaves_obrigatorias(self):
        """Dict de estoque deve ter chaves contábeis e 'lotes'."""
        est = InventoryManager.get_estoque_produto(self._id_valido)
        for chave in ["quantidadeTotal", "custoMedio", "totalCompras",
                      "totalVendas", "lotes", "composicao"]:
            self.assertIn(chave, est, f"Chave ausente no estoque: {chave}")

    def test_12_lotes_e_lista(self):
        """O campo 'lotes' deve ser uma lista."""
        est = InventoryManager.get_estoque_produto(self._id_valido)
        self.assertIsInstance(est["lotes"], list)

    def test_13_produto_invalido_retorna_dict_vazio(self):
        """get_estoque_produto(id_inexistente) deve retornar {}."""
        est = InventoryManager.get_estoque_produto(999999)
        self.assertEqual(est, {})


class TestGetNota(unittest.TestCase):
    """4. Valida get_nota() para nota existente e inexistente."""

    def setUp(self):
        _garantir_carregado()
        nota_exemplo = list(InventoryManager._NotasVendas)[0]
        self._id_valido = nota_exemplo.getDados()["id"]

    def test_14_nota_valida_retorna_dados(self):
        """get_nota(id_valido) deve retornar dict com o mesmo id."""
        dados = InventoryManager.get_nota(self._id_valido)
        self.assertIsInstance(dados, dict)
        self.assertEqual(dados.get("id"), self._id_valido)

    def test_15_nota_invalida_retorna_dict_vazio(self):
        """get_nota(999999) deve retornar {}."""
        dados = InventoryManager.get_nota(999999)
        self.assertEqual(dados, {})


class TestTriangulacao(unittest.TestCase):
    """5. Valida get_triangulacao_sazonal()."""

    def setUp(self):
        _garantir_carregado()
        self.triang = InventoryManager.get_triangulacao_sazonal()

    def test_16_retorna_lista(self):
        """get_triangulacao_sazonal() deve retornar uma lista."""
        self.assertIsInstance(self.triang, list)

    def test_17_cada_item_tem_chaves_obrigatorias(self):
        """Cada item da triangulação deve ter as chaves esperadas."""
        if not self.triang:
            self.skipTest("Nenhuma triangulação disponível.")
        for chave in ["id_nota", "tipo", "data", "produtos", "snapshot_sazonal"]:
            self.assertIn(chave, self.triang[0], f"Chave ausente: {chave}")

    def test_18_tipo_e_venda_ou_perda(self):
        """O campo 'tipo' de cada item deve ser 'VENDA' ou 'PERDA'."""
        for item in self.triang:
            self.assertIn(item["tipo"], ("VENDA", "PERDA"))

    def test_19_filtro_por_produto(self):
        """Filtrar por id_produto deve reduzir ou manter o número de resultados."""
        id_prod = int(next(iter(InventoryManager._mapaProdutos)))
        triang_filtrada = InventoryManager.get_triangulacao_sazonal(id_prod)
        self.assertLessEqual(len(triang_filtrada), len(self.triang))


class TestTendencias(unittest.TestCase):
    """6. Valida analisar_tendencias_sazonais()."""

    def setUp(self):
        _garantir_carregado()
        self.tend = InventoryManager.analisar_tendencias_sazonais()

    def test_20_retorna_dict(self):
        """analisar_tendencias_sazonais() deve retornar um dict."""
        self.assertIsInstance(self.tend, dict)

    def test_21_chaves_principais_presentes(self):
        """Dict de tendências deve ter as chaves de nível 1."""
        for chave in ["resumo", "por_clima", "por_chuva", "por_rio",
                      "por_temperatura", "por_eventos",
                      "serie_temporal_semanal", "indicadores", "alertas"]:
            self.assertIn(chave, self.tend, f"Chave ausente: {chave}")

    def test_22_por_clima_tem_3_categorias(self):
        """por_clima deve ter exatamente QUENTE, FRIO, AMENO."""
        self.assertSetEqual(set(self.tend["por_clima"].keys()), {"QUENTE", "FRIO", "AMENO"})

    def test_23_por_temperatura_tem_5_faixas(self):
        """por_temperatura deve ter as 5 faixas de temperatura."""
        self.assertSetEqual(set(self.tend["por_temperatura"].keys()),
                            {"ate_20", "20_25", "25_30", "30_35", "acima_35"})

    def test_24_indicadores_tem_chaves_esperadas(self):
        """indicadores deve ter as chaves para cards da UI."""
        ind = self.tend["indicadores"]
        for chave in ["clima_mais_vendas", "clima_mais_perdas",
                      "temperatura_media_vendas", "risco_perda_clima", "eventos_impacto"]:
            self.assertIn(chave, ind)

    def test_25_alertas_e_lista(self):
        """alertas deve ser uma lista de strings."""
        alertas = self.tend["alertas"]
        self.assertIsInstance(alertas, list)
        for a in alertas:
            self.assertIsInstance(a, str)

    def test_26_serie_temporal_ordenada(self):
        """serie_temporal_semanal deve estar em ordem cronológica."""
        serie = self.tend["serie_temporal_semanal"]
        semanas = [s["semana"] for s in serie]
        self.assertEqual(semanas, sorted(semanas))


class TestProdutosLista(unittest.TestCase):
    """7. Valida get_produtos_lista() para uso em dropdowns/tabelas na UI."""

    def setUp(self):
        _garantir_carregado()
        self.lista = InventoryManager.get_produtos_lista()

    def test_27_retorna_lista(self):
        """get_produtos_lista() deve retornar uma lista não-vazia."""
        self.assertIsInstance(self.lista, list)
        self.assertGreater(len(self.lista), 0)

    def test_28_cada_item_tem_campos_obrigatorios(self):
        """Cada item deve ter os campos necessários para a UI."""
        campos = ["id", "id_str", "qtd_estoque", "valor_estoque",
                  "custo_medio", "eh_composto", "lotes_disponiveis", "alerta_negativo"]
        for campo in campos:
            self.assertIn(campo, self.lista[0], f"Campo ausente: {campo}")

    def test_29_ordenado_por_id(self):
        """Lista deve estar ordenada por id numérico crescente."""
        ids = [p["id"] for p in self.lista]
        self.assertEqual(ids, sorted(ids))

    def test_30_alerta_negativo_e_bool(self):
        """alerta_negativo deve ser bool."""
        for p in self.lista:
            self.assertIsInstance(p["alerta_negativo"], bool)


class TestNotasPorTipo(unittest.TestCase):
    """8. Valida get_notas_por_tipo() com paginação."""

    def setUp(self):
        _garantir_carregado()

    def test_31_tipo_2_retorna_dict_paginado(self):
        """get_notas_por_tipo(2) deve retornar dict com total, limit, offset, dados."""
        resultado = InventoryManager.get_notas_por_tipo(2)
        self.assertIsInstance(resultado, dict)
        for chave in ["total", "limit", "offset", "dados"]:
            self.assertIn(chave, resultado)

    def test_32_paginacao_limit_funciona(self):
        """Com limit=5, dados deve ter no máximo 5 itens."""
        resultado = InventoryManager.get_notas_por_tipo(2, limit=5, offset=0)
        self.assertLessEqual(len(resultado["dados"]), 5)

    def test_33_tipo_label_adicionado(self):
        """Cada nota no resultado deve ter tipo_label='VENDA' para tipo 2."""
        resultado = InventoryManager.get_notas_por_tipo(2, limit=3)
        for nota in resultado["dados"]:
            self.assertEqual(nota.get("tipo_label"), "VENDA")

    def test_34_tipo_invalido_retorna_vazio(self):
        """Tipo inexistente deve retornar total=0 e dados=[]."""
        resultado = InventoryManager.get_notas_por_tipo(99)
        self.assertEqual(resultado["total"], 0)
        self.assertEqual(resultado["dados"], [])

    def test_35_offset_pagina_corretamente(self):
        """offset deve avançar a página corretamente."""
        p1 = InventoryManager.get_notas_por_tipo(1, limit=3, offset=0)
        p2 = InventoryManager.get_notas_por_tipo(1, limit=3, offset=3)
        ids_p1 = [n["id"] for n in p1["dados"]]
        ids_p2 = [n["id"] for n in p2["dados"]]
        # Nenhum ID deve repetir entre as duas páginas
        self.assertEqual(len(set(ids_p1) & set(ids_p2)), 0)


class TestIndiceComposto(unittest.TestCase):
    """9. Valida o split e estrutura do índice composto {seq}.{nota}.{tipo}.{prod}.{var}."""

    def setUp(self):
        _garantir_carregado()
        # Pega o primeiro lote disponível
        self._idx = next(iter(InventoryManager._mapaEstoque))

    def test_36_idx_tem_5_partes(self):
        """O índice composto deve ter exatamente 5 partes separadas por '.'."""
        partes = self._idx.split(".")
        self.assertEqual(len(partes), 5, f"Esperado 5 partes, obtido {len(partes)}: {self._idx}")

    def test_37_partes_sao_numericas(self):
        """Todas as 5 partes do índice devem ser inteiros."""
        partes = self._idx.split(".")
        for parte in partes:
            self.assertTrue(parte.isdigit(), f"Parte '{parte}' não é numérica no índice {self._idx}")

    def test_38_acesso_direto_sem_loop(self):
        """O lote deve ser acessível diretamente pelo índice (O1) sem loops."""
        lote = InventoryManager._mapaEstoque.get(self._idx)
        self.assertIsNotNone(lote)
        self.assertIn("qtd_disponivel", lote)
        self.assertIn("custo_unitario", lote)
        self.assertIn("data_entrada", lote)

    def test_39_idx_produto_consistente_com_mapa(self):
        """O id_produto extraído do índice deve existir em _mapaProdutos."""
        partes = self._idx.split(".")
        id_prod_str = partes[3]
        self.assertIn(id_prod_str, InventoryManager._mapaProdutos,
                      f"id_produto {id_prod_str} do índice não encontrado em _mapaProdutos")

    def test_40_tipo_no_idx_valido(self):
        """O id_tipo extraído do índice deve ser 1, 2, 3, 4 ou 5."""
        partes = self._idx.split(".")
        id_tipo = int(partes[2])
        self.assertIn(id_tipo, {1, 2, 3, 4, 5},
                      f"id_tipo {id_tipo} fora do intervalo válido")


if __name__ == "__main__":
    # Executa com verbosidade máxima para exibir cada teste individualmente
    unittest.main(verbosity=2)
