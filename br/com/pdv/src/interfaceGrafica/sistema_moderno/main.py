import tkinter as tk

from screens.login_screen import TelaLogin
from screens.dashboard_screen import TelaDashboard


class Aplicativo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Moderno")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(bg="#ffffff")

        self.tela_atual = None
        self.mostrar_tela_login()

    def _trocar_tela(self, nova_tela_classe, **kwargs):
        if self.tela_atual is not None:
            self.tela_atual.destroy()
        self.tela_atual = nova_tela_classe(self, **kwargs)

    def mostrar_tela_login(self):
        self._trocar_tela(TelaLogin, ao_logar=self.mostrar_tela_dashboard)

    def mostrar_tela_dashboard(self, usuario):
        self._trocar_tela(TelaDashboard, usuario=usuario, ao_sair=self.mostrar_tela_login)


if __name__ == "__main__":
    app = Aplicativo()
    app.mainloop()
