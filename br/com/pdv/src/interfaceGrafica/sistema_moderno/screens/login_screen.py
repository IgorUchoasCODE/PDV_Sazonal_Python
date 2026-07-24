import os
import tkinter as tk
from PIL import Image, ImageTk

from widgets.custom_widgets import (
    BotaoArredondado, CampoEntrada,
    COR_AZUL, COR_AZUL_ESCURO, COR_VERMELHO, COR_BRANCO, COR_CINZA_TEXTO
)

PASTA_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


class TelaLogin(tk.Frame):
    def __init__(self, master, ao_logar):
        """
        master: janela/contêiner pai
        ao_logar: função chamada quando o login for efetuado com sucesso
        """
        super().__init__(master, bg=COR_BRANCO)
        self.ao_logar = ao_logar
        self.pack(fill="both", expand=True)

        self._criar_fundo_ondulado()
        self._criar_logo_e_titulo()
        self._criar_formulario()

    # ---------------------------------------------------------------
    def _criar_fundo_ondulado(self):
        """Desenha as ondas azul/vermelha na parte inferior da tela."""
        self.canvas_fundo = tk.Canvas(self, bg=COR_BRANCO, highlightthickness=0, bd=0)
        self.canvas_fundo.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas_fundo.bind("<Configure>", self._redesenhar_ondas)

    def _redesenhar_ondas(self, evento=None):
        c = self.canvas_fundo
        c.delete("onda")
        largura = c.winfo_width()
        altura = c.winfo_height()
        if largura < 10 or altura < 10:
            return

        base = altura * 0.72
        # Onda vermelha (atrás)
        c.create_polygon(
            0, base + 40,
            largura * 0.3, base - 10,
            largura * 0.6, base + 30,
            largura, base - 20,
            largura, altura, 0, altura,
            smooth=True, fill="#f6b8b8", outline="", tags="onda"
        )
        # Onda azul (frente, mais baixa)
        c.create_polygon(
            0, base + 70,
            largura * 0.25, base + 20,
            largura * 0.55, base + 65,
            largura * 0.8, base + 15,
            largura, base + 55,
            largura, altura, 0, altura,
            smooth=True, fill=COR_AZUL, outline="", tags="onda"
        )
        c.tag_lower("onda")

    # ---------------------------------------------------------------
    def _criar_logo_e_titulo(self):
        caminho_logo = os.path.join(PASTA_ASSETS, "logo_transparente.png")
        imagem = Image.open(caminho_logo).convert("RGBA")
        imagem = imagem.resize((150, 154), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(imagem)

        tk.Label(self, image=self.logo_img, bg=COR_BRANCO).pack(pady=(60, 10))

        frame_titulo = tk.Frame(self, bg=COR_BRANCO)
        frame_titulo.pack()
        tk.Label(frame_titulo, text="Sistema", font=("Segoe UI", 26, "bold"),
                 fg=COR_AZUL_ESCURO, bg=COR_BRANCO).pack(side="left")
        tk.Label(frame_titulo, text=" Moderno", font=("Segoe UI", 26, "bold"),
                 fg=COR_VERMELHO, bg=COR_BRANCO).pack(side="left")

        tk.Label(self, text="Faça Login", font=("Segoe UI", 12),
                 fg=COR_CINZA_TEXTO, bg=COR_BRANCO).pack(pady=(2, 25))

    # ---------------------------------------------------------------
    def _criar_formulario(self):
        frame_form = tk.Frame(self, bg=COR_BRANCO)
        frame_form.pack()

        tk.Label(frame_form, text="Usuário", font=("Segoe UI", 10),
                 fg="#374151", bg=COR_BRANCO, anchor="w").pack(fill="x", pady=(0, 4))
        self.campo_usuario = CampoEntrada(frame_form, placeholder="Digite seu usuário",
                                          icone="👤", largura=320)
        self.campo_usuario.pack(pady=(0, 16))

        tk.Label(frame_form, text="Senha", font=("Segoe UI", 10),
                 fg="#374151", bg=COR_BRANCO, anchor="w").pack(fill="x", pady=(0, 4))
        self.campo_senha = CampoEntrada(frame_form, placeholder="Digite sua senha",
                                        icone="🔒", senha=True, largura=320)
        self.campo_senha.pack(pady=(0, 26))

        botao_entrar = BotaoArredondado(frame_form, "ENTRAR", comando=self._logar,
                                         cor_fundo=COR_AZUL, largura=320, altura=46,
                                         icone="→")
        botao_entrar.pack()

        tk.Label(self, text="© 2026 Sistema de Gestão", font=("Segoe UI", 9),
                 fg=COR_CINZA_TEXTO, bg=COR_BRANCO).pack(side="bottom", pady=18)

        # Permite logar apertando Enter
        self.campo_senha.entry.bind("<Return>", lambda e: self._logar())
        self.campo_usuario.entry.bind("<Return>", lambda e: self._logar())

    # ---------------------------------------------------------------
    def _logar(self):
        usuario = self.campo_usuario.obter_valor() or "admin"
        # Aqui poderia entrar uma validação real de usuário/senha
        self.ao_logar(usuario)
