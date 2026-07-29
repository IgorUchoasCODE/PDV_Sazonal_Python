import json
with open('c:/Users/stone/.gemini/antigravity-ide/brain/a9e08e93-f90d-42e0-9647-778c985b97e2/implementation_plan.md', 'w', encoding='utf-8') as f:
    f.write('''# Implementação de Alertas, Tendências e Filtros no Dashboard

Vamos incrementar a Home (Dashboard) com filtros no gráfico, relatórios de tendências sazonais e painéis de alerta, além de aprimorar a estética geral (Premium Design).

## User Review Required
> [!NOTE]
> Gostaria que você conferisse os painéis que serão adicionados e o escopo dos filtros do gráfico.

## Proposed Changes

### iews_gerais.py
- Adicionar chamada para InventoryManager.analisar_tendencias_sazonais() para obter os alertas e métricas climáticas/ambientais do comportamento de vendas.
- Buscar diretamente no banco (w_produto_completo) a lista de produtos com estoque negativo ou zerado para compor o painel de "Alertas de Produtos".
- Passar essas novas variáveis de contexto (lertas_produtos, 	endencias_sazonais) para o dashboard.html.

### dashboard.html
- **Filtros no Gráfico**: Adicionar lógica JavaScript aos botões de filtro acima do gráfico (ex: "Últimos 7 dias", "Últimos 30 dias", "Tudo"). Ao clicar, os arrays do Chart.js serão filtrados e o gráfico renderizado novamente sem precisar recarregar a página.
- **Painéis Abaixo do Gráfico**:
  - Criar um grid duplo contendo dois grandes blocos visuais.
  - **Bloco 1 (Tendências Sazonais)**: Vai listar insights dinâmicos como "Vendas 500% maiores em clima Ameno" com ícones e destaque.
  - **Bloco 2 (Alertas de Produtos)**: Uma lista estilizada sinalizando produtos em vermelho (estoque negativo) ou laranja (estoque zerado/baixo) para chamar sua atenção.

### style.css
- Aprimorar o *Glassmorphism* e as animações de *hover* nos cards da Home.
- Adicionar estilos Premium para os novos painéis de alerta e tendências, usando micro-animações, cores contrastantes (vermelho/âmbar) sobre fundos suaves, e tipografia moderna (Google Fonts - Inter).

## Verification Plan
1. Recarregar o dashboard e garantir que o gráfico seja perfeitamente renderizado com a funcionalidade de filtro de datas (JS puro).
2. Garantir que os alertas de estoque apontem com precisão os mesmos produtos negativos detalhados no relatório de estoque anterior.
3. Certificar-se que a apresentação estética atende ao padrão "premium".
''')
