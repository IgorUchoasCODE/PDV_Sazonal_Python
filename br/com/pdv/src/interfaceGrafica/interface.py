import tkinter as tk
class JanelaSecundaria(tk.Toplevel):
    def __init__(self, pai):
        super().__init__(pai)
        
        # Configurações da nova janela
        self.title("Nova Tela - Detalhes")
        self.geometry("400x300")
        self.configure(bg="#3a3a3a")
        
        # Garante que o foco vá para esta janela quando aberta
        self.focus_set()
        self.grab_set()  # Opcional: impede o usuário de clicar na janela de trás
        
        self.criar_widgets()
        
    def criar_widgets(self):
        # Mensagem interna da nova tela
        label = tk.Label(
            self, 
            text="Esta é a Nova Janela!", 
            font=("Arial", 14, "bold"),
            bg="#146f96",
            fg="white"
        )
        label.pack(pady=40)
        
        # Botão para fechar apenas esta janela
        btn_fechar = tk.Button(
            self,
            text="Fechar Janela",
            font=("Arial", 10),
            bg="#dc3545",
            fg="white",
            relief="flat",
            command=self.destroy
        )
        btn_fechar.pack(pady=20)




class Janela (tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PDV Sazonal")
        self.geometry("1000x800")
        self.config(bg="#79a8c6")
        self.widgets_b()

    def widgets_b(self):
        self.Bnt_Venda = tk.Button(
            self,
            text="Confirma venda baby",
            font=("Arial",20,"bold"),
            background="#E1B08C",
            activebackground="#005999",
            command= self.abrirJanela
        )

        self.Bnt_Venda.pack()

    def abrirJanela(self):
        JanelaSecundaria(self)



    


j = Janela()
j.mainloop()

