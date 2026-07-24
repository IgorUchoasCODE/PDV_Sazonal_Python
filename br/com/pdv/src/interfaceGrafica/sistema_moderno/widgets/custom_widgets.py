"""
Widgets customizados reutilizáveis para o Sistema Moderno.
Como o tkinter puro não tem botões/campos arredondados nativos,
criamos aqui versões "bonitas" usando Canvas.
"""
import tkinter as tk
from tkinter import font as tkfont

# ---------- Paleta de cores do sistema ----------
COR_AZUL_ESCURO = "#0d1b3e"
COR_AZUL = "#1f4fd8"
COR_AZUL_CLARO = "#e8edfb"
COR_VERMELHO = "#e02424"
COR_VERMELHO_CLARO = "#fdecec"
COR_VERDE = "#16a34a"
COR_LARANJA = "#f59e0b"
COR_CINZA_TEXTO = "#6b7280"
COR_CINZA_CLARO = "#f4f6fb"
COR_BRANCO = "#ffffff"
COR_BORDA = "#e5e7eb"


class BotaoArredondado(tk.Canvas):
    """Botão com cantos arredondados e efeito hover."""

    def __init__(self, master, texto, comando=None, cor_fundo=COR_AZUL,
                 cor_fundo_hover=None, cor_texto=COR_BRANCO, largura=200,
                 altura=44, raio=10, fonte=("Segoe UI", 11, "bold"), icone=""):
        super().__init__(master, width=largura, height=altura,
                          bg=master["bg"] if isinstance(master, (tk.Frame, tk.Canvas)) else COR_BRANCO,
                          highlightthickness=0, bd=0, cursor="hand2")
        self.comando = comando
        self.cor_fundo = cor_fundo
        self.cor_fundo_hover = cor_fundo_hover or self._escurecer(cor_fundo)
        self.cor_texto = cor_texto
        self.largura, self.altura, self.raio = largura, altura, raio
        self.texto = f"{icone}  {texto}" if icone else texto
        self.fonte = fonte

        self._desenhar(self.cor_fundo)
        self.bind("<Enter>", lambda e: self._desenhar(self.cor_fundo_hover))
        self.bind("<Leave>", lambda e: self._desenhar(self.cor_fundo))
        self.bind("<Button-1>", lambda e: self.comando() if self.comando else None)

    def _escurecer(self, cor_hex, fator=0.85):
        cor_hex = cor_hex.lstrip("#")
        r, g, b = int(cor_hex[0:2], 16), int(cor_hex[2:4], 16), int(cor_hex[4:6], 16)
        r, g, b = int(r * fator), int(g * fator), int(b * fator)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _retangulo_arredondado(self, x1, y1, x2, y2, r, **kwargs):
        pontos = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.create_polygon(pontos, smooth=True, **kwargs)

    def _desenhar(self, cor_fundo):
        self.delete("all")
        self._retangulo_arredondado(1, 1, self.largura-1, self.altura-1,
                                     self.raio, fill=cor_fundo, outline=cor_fundo)
        self.create_text(self.largura/2, self.altura/2, text=self.texto,
                          fill=self.cor_texto, font=self.fonte)


class CampoEntrada(tk.Frame):
    """Campo de texto com borda arredondada, ícone e placeholder."""

    def __init__(self, master, placeholder="", icone="", senha=False,
                 largura=300, altura=44, bg_fundo=COR_BRANCO):
        super().__init__(master, bg=master["bg"])
        self.mostrar_senha = tk.BooleanVar(value=False)
        self.senha = senha
        self.placeholder = placeholder
        self.bg_fundo = bg_fundo

        self.canvas = tk.Canvas(self, width=largura, height=altura,
                                 bg=master["bg"], highlightthickness=0, bd=0)
        self.canvas.pack()
        self._retangulo_arredondado(1, 1, largura-1, altura-1, 10,
                                     fill=bg_fundo, outline=COR_BORDA)

        fonte = ("Segoe UI", 11)
        x_texto = 42 if icone else 16
        if icone:
            self.canvas.create_text(18, altura/2, text=icone, font=("Segoe UI", 12), fill=COR_CINZA_TEXTO)

        self.entry = tk.Entry(self.canvas, font=fonte, bd=0,
                               bg=bg_fundo, fg="#111827",
                               insertbackground="#111827",
                               show="*" if senha and not self.mostrar_senha.get() else "")
        self.canvas.create_window(x_texto, altura/2, anchor="w",
                                   window=self.entry, width=largura - x_texto - (34 if senha else 16))
        self._aplicar_placeholder()
        self.entry.bind("<FocusIn>", self._ao_focar)
        self.entry.bind("<FocusOut>", self._ao_sair)

        if senha:
            self.olho = self.canvas.create_text(largura-20, altura/2, text="👁", font=("Segoe UI", 11), fill=COR_CINZA_TEXTO)
            self.canvas.tag_bind(self.olho, "<Button-1>", self._alternar_senha)

    def _retangulo_arredondado(self, x1, y1, x2, y2, r, **kwargs):
        pontos = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.canvas.create_polygon(pontos, smooth=True, **kwargs)

    def _aplicar_placeholder(self):
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=COR_CINZA_TEXTO)
        if self.senha:
            self.entry.config(show="")

    def _ao_focar(self, evento):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg="#111827")
            if self.senha and not self.mostrar_senha.get():
                self.entry.config(show="*")

    def _ao_sair(self, evento):
        if self.entry.get() == "":
            self._aplicar_placeholder()

    def _alternar_senha(self, evento):
        self.mostrar_senha.set(not self.mostrar_senha.get())
        if self.entry.get() != self.placeholder:
            self.entry.config(show="" if self.mostrar_senha.get() else "*")

    def obter_valor(self):
        valor = self.entry.get()
        return "" if valor == self.placeholder else valor


class Card(tk.Frame):
    """Cartão branco com cantos arredondados usado nos indicadores do dashboard."""

    def __init__(self, master, largura=180, altura=110, cor_fundo=COR_BRANCO, raio=14):
        super().__init__(master, bg=master["bg"])
        self.canvas = tk.Canvas(self, width=largura, height=altura,
                                 bg=master["bg"], highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        pontos = self._pontos_arredondados(1, 1, largura-1, altura-1, raio)
        self.canvas.create_polygon(pontos, smooth=True, fill=cor_fundo, outline=COR_BORDA)
        self.largura, self.altura = largura, altura

    def _pontos_arredondados(self, x1, y1, x2, y2, r):
        return [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]

    def adicionar_conteudo(self, widget_construtor):
        """Recebe uma função que constrói o conteúdo interno do card."""
        janela = widget_construtor(self.canvas)
        self.canvas.create_window(self.largura/2, self.altura/2, window=janela)
