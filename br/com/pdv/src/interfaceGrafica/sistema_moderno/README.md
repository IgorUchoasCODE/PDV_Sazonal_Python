# Sistema Moderno — Frontend em Python

Reprodução da tela de login e do dashboard mostrados no print, feita em
Python puro com `tkinter` (interface gráfica nativa) + `matplotlib`
(para os gráficos) + `Pillow` (para exibir a logo).

Não usa nenhuma biblioteca "exótica" — só coisas fáceis de instalar.

## 📁 Estrutura do projeto

```
sistema_moderno/
├── main.py                    # Ponto de entrada — roda o app
├── requirements.txt           # Dependências
├── assets/
│   └── logo_transparente.png  # Logo usada no login e no menu lateral
├── screens/
│   ├── login_screen.py        # Tela de login (ondas, logo, formulário)
│   └── dashboard_screen.py    # Tela de dashboard (cards, gráficos, listas)
└── widgets/
    └── custom_widgets.py      # Botão arredondado, campo de texto, card
```

## ▶️ Como rodar

1. Tenha o Python 3.10+ instalado (o `tkinter` já vem junto no Windows/Mac).
   No Linux, se necessário: `sudo apt install python3-tk`

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Execute:
   ```
   python main.py
   ```

## ✨ O que foi reproduzido

- **Tela de Login**: logo, fundo com ondas azul/vermelho, campos de
  usuário e senha (com ícone de mostrar/ocultar senha) e botão "ENTRAR".
- **Dashboard**:
  - Menu lateral azul-escuro com ícones (Início, Cadastro, Produtos,
    Vendas, Relatórios, Clientes, Configurações, Sair);
  - Cabeçalho azul com saudação e data/hora atual;
  - 4 cards de indicadores (Clientes, Produtos, Vendas, Faturamento);
  - Gráfico de linha "Vendas dos últimos 7 dias";
  - Gráfico de rosca "Vendas por categoria" com legenda;
  - Lista "Últimas vendas" e lista "Atividades recentes".

## 🛠 Como personalizar

- **Cores**: todas as cores estão centralizadas no topo de
  `widgets/custom_widgets.py` (`COR_AZUL`, `COR_VERMELHO` etc.), então
  dá pra trocar o tema inteiro mudando poucas linhas.
- **Dados do dashboard**: os números mostrados (clientes, vendas,
  gráficos, listas) estão em variáveis no topo de
  `screens/dashboard_screen.py` (`INDICADORES`, `VENDAS_7_DIAS`,
  `ULTIMAS_VENDAS` etc.) — é só trocar pelos dados reais ou ligar num
  banco de dados depois.
- **Login real**: hoje o botão "ENTRAR" aceita qualquer usuário/senha
  (é só um mock). O lugar certo para validar contra um banco de dados
  é o método `_logar()` em `screens/login_screen.py`.
