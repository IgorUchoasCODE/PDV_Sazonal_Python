import os
import datetime
import tkinter as tk
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from widgets.custom_widgets import (
    Card, COR_AZUL_ESCURO, COR_AZUL, COR_AZUL_CLARO, COR_VERMELHO,
    COR_VERMELHO_CLARO, COR_VERDE, COR_LARANJA, COR_CINZA_TEXTO,
    COR_CINZA_CLARO, COR_BRANCO, COR_BORDA
)

PASTA_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

# ---------------------- Dados de exemplo (mock) ----------------------
INDICADORES = [
    {"icone": "👥", "cor": "#3b82f6", "titulo": "Clientes", "valor": "120", "variacao": "+12% este mês"},
    {"icone": "📦", "cor": "#16a34a", "titulo": "Produtos", "valor": "85", "variacao": "+8% este mês"},
    {"icone": "🛒", "cor": "#f59e0b", "titulo": "Vendas", "valor": "37", "variacao": "+15% este mês"},
    {"icone": "💲", "cor": "#e02424", "titulo": "Faturamento", "valor": "R$ 24.590", "variacao": "+18% este mês"},
]

VENDAS_7_DIAS = {
    "dias": ["24/05", "25/05", "26/05", "27/05", "28/05", "29/05", "30/05"],
    "valores": [2100, 3300, 2900, 3200, 3700, 4400, 3900],
}

VENDAS_CATEGORIA = [
    ("Eletrônicos", 45, "#2563eb"),
    ("Informática", 25, "#e02424"),
    ("Móveis", 15, "#f59e0b"),
    ("Outros", 15, "#9ca3af"),
]

ULTIMAS_VENDAS = [
    ("Notebook Dell Inspiron", "R$ 2.450,00"),
    ("Smartphone Samsung Galaxy", "R$ 1.899,00"),
    ("Monitor LG 24\"", "R$ 890,00"),
    ("Teclado Mecânico RGB", "R$ 320,00"),
    ("Mouse Gamer Logitech", "R$ 210,00"),
]

ATIVIDADES_RECENTES = [
    ("👤", "Novo cliente cadastrado", "João Silva", "30/05/2025 14:10"),
    ("📦", "Novo produto cadastrado", "Teclado Gamer Redragon", "30/05/2025 13:50"),
    ("🛒", "Venda realizada", "R$ 2.450,00", "30/05/2025 14:20"),
    ("📊", "Relatório gerado", "Relatório de vendas - Maio/2025", "30/05/2025 09:30"),
]

MENU_ITENS = [
    ("🏠", "Início"), ("📝", "Cadastro"), ("📦", "Produtos"),
    ("🛒", "Vendas"), ("📊", "Relatórios"), ("👥", "Clientes"), ("⚙️", "Configurações"),
]


class TelaDashboard(tk.Frame):
    def __init__(self, master, usuario="admin", ao_sair=None):
        super().__init__(master, bg=COR_CINZA_CLARO)
        self.usuario = usuario
        self.ao_sair = ao_sair
        self.item_selecionado = "Início"
        self.pack(fill="both", expand=True)

        self._criar_layout_base()
        self._criar_menu_lateral()
        self._criar_cabecalho()
        self._criar_area_conteudo()

    # ------------------------------------------------------------------
    def _criar_layout_base(self):
        self.sidebar = tk.Frame(self, bg=COR_AZUL_ESCURO, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.area_direita = tk.Frame(self, bg=COR_CINZA_CLARO)
        self.area_direita.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    def _criar_menu_lateral(self):
        caminho_logo = os.path.join(PASTA_ASSETS, "logo_transparente.png")
        imagem = Image.open(caminho_logo).convert("RGBA").resize((70, 72), Image.LANCZOS)
        self.logo_pequena = ImageTk.PhotoImage(imagem)

        tk.Label(self.sidebar, image=self.logo_pequena, bg=COR_AZUL_ESCURO).pack(pady=(24, 6))
        frame_titulo = tk.Frame(self.sidebar, bg=COR_AZUL_ESCURO)
        frame_titulo.pack(pady=(0, 20))
        tk.Label(frame_titulo, text="Sistema", font=("Segoe UI", 13, "bold"),
                 fg=COR_BRANCO, bg=COR_AZUL_ESCURO).pack(side="left")
        tk.Label(frame_titulo, text=" Moderno", font=("Segoe UI", 13, "bold"),
                 fg=COR_VERMELHO, bg=COR_AZUL_ESCURO).pack(side="left")

        self.botoes_menu = {}
        for icone, nome in MENU_ITENS:
            self.botoes_menu[nome] = self._criar_item_menu(icone, nome)

        self._atualizar_selecao_menu()

        # Empurra o botão "Sair" para o rodapé
        tk.Frame(self.sidebar, bg=COR_AZUL_ESCURO).pack(fill="both", expand=True)
        linha = tk.Frame(self.sidebar, bg="#1f2c52", height=1)
        linha.pack(fill="x", padx=20)
        item_sair = tk.Frame(self.sidebar, bg=COR_AZUL_ESCURO, cursor="hand2")
        item_sair.pack(fill="x", pady=16, padx=20)
        tk.Label(item_sair, text="⏻  Sair", font=("Segoe UI", 11), fg="#c9d3ee",
                 bg=COR_AZUL_ESCURO, anchor="w").pack(fill="x")
        for w in (item_sair,) + tuple(item_sair.winfo_children()):
            w.bind("<Button-1>", lambda e: self.ao_sair() if self.ao_sair else None)

    def _criar_item_menu(self, icone, nome):
        selecionado = (nome == self.item_selecionado)
        fundo = COR_VERMELHO if selecionado else COR_AZUL_ESCURO
        frame_item = tk.Frame(self.sidebar, bg=fundo, cursor="hand2")
        frame_item.pack(fill="x", padx=14, pady=3)
        rotulo = tk.Label(frame_item, text=f"{icone}   {nome}", font=("Segoe UI", 11),
                           fg=COR_BRANCO, bg=fundo, anchor="w", padx=14, pady=10)
        rotulo.pack(fill="x")

        def selecionar(evento=None, nome=nome):
            self.item_selecionado = nome
            self._atualizar_selecao_menu()

        frame_item.bind("<Button-1>", selecionar)
        rotulo.bind("<Button-1>", selecionar)
        return frame_item

    def _atualizar_selecao_menu(self):
        for nome, frame_item in self.botoes_menu.items():
            selecionado = (nome == self.item_selecionado)
            fundo = COR_VERMELHO if selecionado else COR_AZUL_ESCURO
            frame_item.config(bg=fundo)
            frame_item.winfo_children()[0].config(bg=fundo)

    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        barra = tk.Frame(self.area_direita, bg=COR_AZUL, height=54)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="☰", font=("Segoe UI", 14), fg=COR_BRANCO, bg=COR_AZUL).pack(side="left", padx=(20, 10))
        tk.Label(barra, text=f"Bem-vindo, {self.usuario}!", font=("Segoe UI", 12, "bold"),
                 fg=COR_BRANCO, bg=COR_AZUL).pack(side="left")

        agora = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")
        tk.Label(barra, text=f"📅  {agora}", font=("Segoe UI", 10), fg=COR_BRANCO,
                 bg=COR_AZUL).pack(side="right", padx=20)

    # ------------------------------------------------------------------
    def _criar_area_conteudo(self):
        conteudo = tk.Frame(self.area_direita, bg=COR_CINZA_CLARO)
        conteudo.pack(fill="both", expand=True, padx=28, pady=20)

        tk.Label(conteudo, text="Dashboard", font=("Segoe UI", 18, "bold"),
                 fg="#111827", bg=COR_CINZA_CLARO, anchor="w").pack(fill="x")
        tk.Label(conteudo, text="Visão geral do seu sistema", font=("Segoe UI", 10),
                 fg=COR_CINZA_TEXTO, bg=COR_CINZA_CLARO, anchor="w").pack(fill="x", pady=(0, 16))

        self._criar_cards_indicadores(conteudo)

        frame_graficos = tk.Frame(conteudo, bg=COR_CINZA_CLARO)
        frame_graficos.pack(fill="both", expand=True, pady=16)
        self._criar_grafico_linha(frame_graficos)
        self._criar_grafico_rosca(frame_graficos)

        frame_listas = tk.Frame(conteudo, bg=COR_CINZA_CLARO)
        frame_listas.pack(fill="both", expand=True)
        self._criar_lista_vendas(frame_listas)
        self._criar_lista_atividades(frame_listas)

    # ------------------------------------------------------------------
    def _criar_cards_indicadores(self, container):
        frame_cards = tk.Frame(container, bg=COR_CINZA_CLARO)
        frame_cards.pack(fill="x")

        for dado in INDICADORES:
            card = Card(frame_cards, largura=250, altura=110)
            card.pack(side="left", padx=(0, 16))

            def construir(canvas_pai, dado=dado):
                interno = tk.Frame(canvas_pai, bg=COR_BRANCO)
                bolha = tk.Label(interno, text=dado["icone"], font=("Segoe UI", 16),
                                  bg=self._clarear(dado["cor"]), fg=dado["cor"],
                                  width=2, height=1)
                bolha.grid(row=0, column=0, rowspan=2, padx=(0, 14))
                tk.Label(interno, text=dado["titulo"], font=("Segoe UI", 10),
                         fg=COR_CINZA_TEXTO, bg=COR_BRANCO).grid(row=0, column=1, sticky="w")
                tk.Label(interno, text=dado["valor"], font=("Segoe UI", 18, "bold"),
                         fg="#111827", bg=COR_BRANCO).grid(row=1, column=1, sticky="w")
                tk.Label(interno, text=dado["variacao"], font=("Segoe UI", 9),
                         fg=COR_VERDE, bg=COR_BRANCO).grid(row=2, column=1, sticky="w", pady=(2, 0))
                return interno

            card.adicionar_conteudo(construir)

    def _clarear(self, cor_hex, fator=0.85):
        cor_hex = cor_hex.lstrip("#")
        r, g, b = int(cor_hex[0:2], 16), int(cor_hex[2:4], 16), int(cor_hex[4:6], 16)
        r = int(r + (255 - r) * fator)
        g = int(g + (255 - g) * fator)
        b = int(b + (255 - b) * fator)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------------
    def _criar_grafico_linha(self, container):
        cartao = tk.Frame(container, bg=COR_BRANCO, highlightbackground=COR_BORDA, highlightthickness=1)
        cartao.pack(side="left", fill="both", expand=True, padx=(0, 16))

        tk.Label(cartao, text="Vendas dos últimos 7 dias", font=("Segoe UI", 11, "bold"),
                 fg="#111827", bg=COR_BRANCO, anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        figura = Figure(figsize=(5.2, 2.6), dpi=100, facecolor=COR_BRANCO)
        eixo = figura.add_subplot(111)
        eixo.plot(VENDAS_7_DIAS["dias"], VENDAS_7_DIAS["valores"], color=COR_AZUL,
                  marker="o", markersize=5, linewidth=2)
        eixo.fill_between(range(len(VENDAS_7_DIAS["dias"])), VENDAS_7_DIAS["valores"],
                           color=COR_AZUL, alpha=0.08)
        eixo.set_facecolor(COR_BRANCO)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        eixo.spines["left"].set_color(COR_BORDA)
        eixo.spines["bottom"].set_color(COR_BORDA)
        eixo.tick_params(colors=COR_CINZA_TEXTO, labelsize=8)
        eixo.grid(axis="y", color=COR_BORDA, linewidth=0.6)
        figura.tight_layout()

        canvas_grafico = FigureCanvasTkAgg(figura, master=cartao)
        canvas_grafico.draw()
        canvas_grafico.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    def _criar_grafico_rosca(self, container):
        cartao = tk.Frame(container, bg=COR_BRANCO, highlightbackground=COR_BORDA, highlightthickness=1, width=280)
        cartao.pack(side="left", fill="y")
        cartao.pack_propagate(False)

        tk.Label(cartao, text="Vendas por categoria", font=("Segoe UI", 11, "bold"),
                 fg="#111827", bg=COR_BRANCO, anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        figura = Figure(figsize=(2.4, 2.0), dpi=100, facecolor=COR_BRANCO)
        eixo = figura.add_subplot(111)
        valores = [v[1] for v in VENDAS_CATEGORIA]
        cores = [v[2] for v in VENDAS_CATEGORIA]
        eixo.pie(valores, colors=cores, startangle=90,
                 wedgeprops=dict(width=0.42, edgecolor=COR_BRANCO, linewidth=2))
        eixo.set_aspect("equal")
        figura.tight_layout()

        canvas_grafico = FigureCanvasTkAgg(figura, master=cartao)
        canvas_grafico.draw()
        canvas_grafico.get_tk_widget().pack(pady=(0, 4))

        frame_legenda = tk.Frame(cartao, bg=COR_BRANCO)
        frame_legenda.pack(fill="x", padx=16, pady=(0, 14))
        for nome, valor, cor in VENDAS_CATEGORIA:
            linha = tk.Frame(frame_legenda, bg=COR_BRANCO)
            linha.pack(fill="x", pady=2)
            tk.Label(linha, text="●", fg=cor, bg=COR_BRANCO, font=("Segoe UI", 10)).pack(side="left")
            tk.Label(linha, text=f" {nome}", fg="#374151", bg=COR_BRANCO,
                     font=("Segoe UI", 9), anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(linha, text=f"{valor}%", fg=COR_CINZA_TEXTO, bg=COR_BRANCO,
                     font=("Segoe UI", 9)).pack(side="right")

    # ------------------------------------------------------------------
    def _criar_lista_vendas(self, container):
        cartao = tk.Frame(container, bg=COR_BRANCO, highlightbackground=COR_BORDA, highlightthickness=1)
        cartao.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=(16, 0))

        tk.Label(cartao, text="Últimas vendas", font=("Segoe UI", 11, "bold"),
                 fg="#111827", bg=COR_BRANCO, anchor="w").pack(fill="x", padx=16, pady=(14, 8))

        for produto, valor in ULTIMAS_VENDAS:
            linha = tk.Frame(cartao, bg=COR_BRANCO)
            linha.pack(fill="x", padx=16, pady=4)
            tk.Label(linha, text=produto, font=("Segoe UI", 10), fg="#374151",
                     bg=COR_BRANCO, anchor="w").pack(side="left")
            tk.Label(linha, text=valor, font=("Segoe UI", 10, "bold"), fg="#111827",
                     bg=COR_BRANCO).pack(side="right")

        tk.Label(cartao, text="Ver todas →", font=("Segoe UI", 9, "bold"), fg=COR_AZUL,
                 bg=COR_BRANCO, cursor="hand2").pack(anchor="w", padx=16, pady=(8, 14))

    def _criar_lista_atividades(self, container):
        cartao = tk.Frame(container, bg=COR_BRANCO, highlightbackground=COR_BORDA, highlightthickness=1)
        cartao.pack(side="left", fill="both", expand=True, pady=(16, 0))

        tk.Label(cartao, text="Atividades recentes", font=("Segoe UI", 11, "bold"),
                 fg="#111827", bg=COR_BRANCO, anchor="w").pack(fill="x", padx=16, pady=(14, 8))

        for icone, titulo, detalhe, data_hora in ATIVIDADES_RECENTES:
            linha = tk.Frame(cartao, bg=COR_BRANCO)
            linha.pack(fill="x", padx=16, pady=5)
            tk.Label(linha, text=icone, font=("Segoe UI", 12), bg=COR_BRANCO).pack(side="left", padx=(0, 10))
            frame_texto = tk.Frame(linha, bg=COR_BRANCO)
            frame_texto.pack(side="left", fill="x", expand=True)
            tk.Label(frame_texto, text=titulo, font=("Segoe UI", 10, "bold"), fg="#111827",
                     bg=COR_BRANCO, anchor="w").pack(fill="x")
            tk.Label(frame_texto, text=detalhe, font=("Segoe UI", 9), fg=COR_CINZA_TEXTO,
                     bg=COR_BRANCO, anchor="w").pack(fill="x")
            tk.Label(linha, text=data_hora, font=("Segoe UI", 8), fg=COR_CINZA_TEXTO,
                     bg=COR_BRANCO).pack(side="right")

        tk.Label(cartao, text="Ver todas →", font=("Segoe UI", 9, "bold"), fg=COR_AZUL,
                 bg=COR_BRANCO, cursor="hand2").pack(anchor="w", padx=16, pady=(8, 14))
