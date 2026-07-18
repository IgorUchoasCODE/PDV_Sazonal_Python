# PDV Sazonal Python

O **PDV Sazonal** é um backend de Ponto de Venda desenvolvido em Python, estruturado segundo o padrão clássico de pacotes empresariais (estilo Java) sob o namespace `br.com.pdv.src`. O projeto destaca-se pela alta precisão em cálculos financeiros usando ponto fixo e validações estritas de dados cadastrais.


---

## 🏗️ Arquitetura e Estrutura de Pastas

O projeto está organizado na seguinte estrutura sob o diretório principal [br/com/pdv/src/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src):

*   [BDD/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/BDD): Módulo de persistência local.
    *   [bancodb.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/BDD/bancodb.py): Camada de conexão com o banco SQLite (`banco.db`).
*   [estoque/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/estoque): Gerenciamento de estoque e inventário (pendente de implementação).
*   [financeiro/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro): Regras de precificação e faturamento.
    *   [Real.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/Real.py): Contém a classe [MoedaReal](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/Real.py#L4-L68) para cálculos monetários exatos de ponto fixo.
    *   [nota.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/nota.py): Classe abstrata [ComportamentoNota](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/nota.py#L5-L13) que dita os métodos para notas de compra e venda.
    *   [notaCompra.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/notaCompra.py) / [notaVenda.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/notaVenda.py): Esboços para notas fiscais.
*   [interfaceGrafica/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/interfaceGrafica):
    *   [interface.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/interfaceGrafica/interface.py): UI desktop feita com a biblioteca nativa `tkinter`, contendo a tela principal de confirmação de venda e tela secundária.
*   [memory/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/memory):
    *   [fictoryClassProduct.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/memory/fictoryClassProduct.py): Fábrica estática para criação de modelos de produtos sem dados de venda.
*   [pessoa/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa): Gestão de entidades do negócio.
    *   [pessoa.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/pessoa.py): Classe abstrata base [Pessoa](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/pessoa.py#L8-L118) para pessoas físicas.
    *   [empresa.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/empresa.py): Classe [Empresa](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/empresa.py#L9-L206) para gerenciar dados corporativos e representantes associados.
    *   [cargos.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/cargos.py): Enum [Cargo](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/cargos.py#L4-L33) com todos os papéis corporativos permitidos.
    *   [cliente.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/cliente.py): Esboço para controle de contas e limites de crédito de clientes.
*   [produto/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto):
    *   [produto.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/produto.py): Classe principal [Produto](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/produto.py#L7-L201) (identificação, cálculo de custo e estoque, manipulação de receitas para itens compostos e vendas).
    *   [UnidadeMedida.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/UnidadeMedida.py): Enum [UnidadeMedida](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/UnidadeMedida.py#L5-L10) (UNIDADE, KG, L, M, CONJUNTO) e classe auxiliar [UnidadeConjunto](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/UnidadeMedida.py#L66-L98) para definir pacotes com quantidades multiplicadoras.
*   [registro/](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro): Sistema extensível de validação e normalização de dados cadastrais.
    *   [validarResgistro.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/validarResgistro.py): Define o protocolo [IValidador](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/validarResgistro.py#L3-L16).
    *   [registro.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/registro.py): Classe [Registro](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/registro.py#L4-L17) que utiliza a interface `IValidador` para encapsular dados normalizados.
    *   [cpfcnpj.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/cpfcnpj.py): Enum [Documento](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/cpfcnpj.py#L5-L7) para validação de algoritmos matemáticos de CPF e CNPJ brasileiros.
    *   [contato.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/contato.py): Enum [Contato](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/contato.py#L4-L6) para validação de telefones fixos e celulares brasileiros com DDD.
    *   [email.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/email.py): Enum [Email](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/email.py#L6) contendo lógica regex e verificação de estruturas de provedor/usuário.
    *   [sexo.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/sexo.py): Enum [Sexo](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/sexo.py#L4-L7) contendo as opções cadastrais de gênero.
    *   [PDproduto.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/PDproduto.py): Módulo sem definição ainda (provavelmente persistência de dados de produtos).

---

## 🛠️ Detalhes Técnicos e Regras de Negócio Críticas

### 1. Aritmética de Ponto Fixo Exata (`MoedaReal`)

Operações financeiras convencionais usando tipos flutuantes (`float`) do Python sofrem de imprecisão binária inerente (ex: `0.1 + 0.2 != 0.3`). Para resolver isso de forma robusta e garantir centavos exatos no faturamento, o projeto implementa a classe utilitária [MoedaReal](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/Real.py#L4-L68):

*   **Fator de Conversão**: Todos os valores são escalados pelo multiplicador **1000** (`FATOR_MILHAR`).
    *   Exemplo: R$ 10,50 vira o inteiro `10500` no banco e na memória.
*   **Arredondamento Comercial**: Utiliza a biblioteca interna `decimal` com o modo de arredondamento comercial `ROUND_HALF_UP` (arredondamento para cima caso o dígito final seja superior ou igual a 5).
*   **Métodos Principais**:
    *   `parseCentavosPorMilhar(reais)`: Converte o valor flutuante da tela para o inteiro do sistema.
    *   `parseMilharParaReais(valor_interno_milhar)`: Transforma o inteiro normalizado de volta para o float final de exibição.
    *   `calculo_PQV_T(proporcao, quantidade, valor_milhar)`: Calcula o valor total de uma venda baseada no multiplicador de proporção e quantidade.

### 2. Validação Extensível com `IValidador`

Em vez de espalhar lógicas condicionais (`if/else`) de validação de CPF ou email pelo código principal, o projeto adota o padrão de design Strategy utilizando Protocols em Python:

*   A interface [IValidador](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/validarResgistro.py#L3-L16) dita o contrato:
    ```python
    class IValidador(Protocol):
        def getNome(self) -> str: ...
        def validar(self, valor: str) -> bool: ...
        def parse(self, valor: str) -> str: ...
    ```
*   Toda vez que a classe [Registro](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/registro.py#L4-L17) é instanciada, o valor fornecido é automaticamente processado e verificado pelo validador adequado.
*   Os validadores [Documento](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/cpfcnpj.py#L5-L7) (CPF/CNPJ) e [Contato](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/contato.py#L4-L6) (Telefone/Celular) removem caracteres não numéricos antes de rodar os algoritmos de checksum ou as expressões regulares.

### 3. Gerenciamento de Unidades de Medida e Pacotes Compostos

A precificação e controle de estoque de produtos dependem da sua forma física de medição. O enum [UnidadeMedida](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/UnidadeMedida.py#L5-L10) permite a definição de produtos vendidos por **unidade inteira** (onde quantidades fracionadas, como 1.5, causam exceção de `ValueError`) ou por **medidas fracionáveis** como Kilogramas (KG), Litros (L) e Metros (M) com precisão de até 3 casas decimais (1000g, 1000ml, 1000mm).

A classe [UnidadeConjunto](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/produto/UnidadeMedida.py#L66-L98) expande essa lógica para possibilitar a venda de "fardos" ou "pacotes" (ex: caixa com 12 unidades) mantendo a rastreabilidade interna de cada unidade individual.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
*   Python 3.10 ou superior.

### Configuração do Ambiente e Execução
1.  **Ativar o Ambiente Virtual (`venv`)**:
    No terminal, execute o comando correspondente ao seu sistema operacional a partir da pasta raiz do projeto:
    *   **Windows (PowerShell)**:
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
    *   **Linux / macOS**:
        ```bash
        source venv/bin/activate
        ```

2.  **Iniciar a Interface Gráfica**:
    Com o ambiente virtual ativado, rode o seguinte comando para abrir a janela do PDV Sazonal:
    ```bash
    python br/com/pdv/src/interfaceGrafica/interface.py
    ```

---

## 🚧 Status de Desenvolvimento e Pendências

Este projeto encontra-se atualmente em fase estrutural/desenho de arquitetura. Diversos arquivos representam stubs e requerem implementações futuras:

| Arquivo/Classe | Status | Descrição do que falta fazer |
| :--- | :--- | :--- |
| [cliente.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/pessoa/cliente.py) | ⏳ Stub | Implementar as operações financeiras de conta corrente (`adicionarNota`, `adicionarPagamento`). |
| [notaCompra.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/notaCompra.py) | ⏳ Vazio | Implementar lógica de entrada de notas fiscais de fornecedores para reabastecimento de estoque. |
| [notaVenda.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/financeiro/notaVenda.py) | ⏳ Vazio | Implementar nota fiscal de venda para emissão de cupom fiscal e dedução de estoque. |
| [fictoryClassProduct.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/memory/fictoryClassProduct.py) | ⏳ Stub | Implementar o padrão Factory/Builder para criar produtos em lote usando dicionários de entrada. |
| [bancodb.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/BDD/bancodb.py) | ⏳ Inicial | Criar a tabela de banco de dados SQLite local e as queries CRUD (Create, Read, Update, Delete). |
| [PDproduto.py](file:///c:/workspace/PDV_Sazonal_Python/br/com/pdv/src/registro/PDproduto.py) | ⏳ Vazio | Módulo sem definição ainda (provavelmente persistência de dados de produtos). |
