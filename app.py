import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, render_template

# 1. Leitura e limpeza dos dados
try:
    colunas = [
        'drs', 'drs_nome', 'cod_rs', 'nome_rs_2024', 'municipio',
        'janeiro_notificados', 'janeiro_confirmados_autoctone', 'janeiro_confirmados_importados',
        'fevereiro_notificados', 'fevereiro_confirmados_autoctone', 'fevereiro_confirmados_importados',
        'março_notificados', 'março_confirmados_autoctone', 'março_confirmados_importados',
        'abril_notificados', 'abril_confirmados_autoctone', 'abril_confirmados_importados',
        'maio_notificados', 'maio_confirmados_autoctone', 'maio_confirmados_importados',
        'unnamed_col'
    ]

    df = pd.read_csv(
        'trab5_editada.csv',
        sep=';',
        header=None,
        skiprows=2,
        names=colunas,
        encoding='latin-1'
    )

except FileNotFoundError:
    print("Erro: O arquivo 'trab5_editada.csv' não foi encontrado. Verifique o caminho.")
    exit()

colunas_numericas = colunas[5:-1]
for col in colunas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

df.drop(columns=['unnamed_col'], inplace=True)
df.dropna(subset=['drs', 'municipio'], inplace=True)

# 2. Análise dos dados e criação dos gráficos

# Gráfico de barras: Casos Confirmados por Município e Mês
meses = {
    'Janeiro': ['janeiro_confirmados_autoctone', 'janeiro_confirmados_importados'],
    'Fevereiro': ['fevereiro_confirmados_autoctone', 'fevereiro_confirmados_importados'],
    'Março': ['março_confirmados_autoctone', 'março_confirmados_importados'],
    'Abril': ['abril_confirmados_autoctone', 'abril_confirmados_importados'],
    'Maio': ['maio_confirmados_autoctone', 'maio_confirmados_importados']
}

df_confirmados_melted = pd.DataFrame()
for mes, cols in meses.items():
    temp_df = df[['municipio']].copy()
    temp_df['Mês'] = mes
    temp_df['Total de Casos Confirmados'] = df[cols].sum(axis=1)
    df_confirmados_melted = pd.concat([df_confirmados_melted, temp_df])

fig_bar = px.bar(
    df_confirmados_melted,
    x='municipio',
    y='Total de Casos Confirmados',
    color='Mês',
    title='Casos Confirmados de Dengue por Município e Mês',
    labels={'municipio': 'Município de Residência', 'Total de Casos Confirmados': 'Total de Casos Confirmados'},
    height=500
)

# Gráfico de pizza: Distribuição de Casos por Mês (Total)
df_pie = pd.DataFrame({
    'Mês': meses.keys(),
    'Total de Casos': [df[cols].sum().sum() for cols in meses.values()]
})

fig_pie = px.pie(
    df_pie,
    values='Total de Casos',
    names='Mês',
    title='Distribuição de Casos Confirmados por Mês',
    hole=0.3
)

# **CÓDIGO NOVO/MODIFICADO: Gráfico de Linhas com Dropdown de Municípios**

# 1. Prepara os dados (mesma estrutura que o gráfico anterior)
df_linha_cidade = pd.DataFrame()
for mes, cols in meses.items():
    temp_df = df[['municipio']].copy()
    temp_df['Mês'] = mes
    temp_df['Casos Confirmados'] = df[cols].sum(axis=1)
    df_linha_cidade = pd.concat([df_linha_cidade, temp_df])

# 2. Prepara a lista de municípios únicos (e a opção 'Total')
municipios = ['Total (Todas as Cidades)'] + sorted(df_linha_cidade['municipio'].unique().tolist())

# 3. Cria a figura vazia para popular com as traces
fig_line = go.Figure()

# 4. Adiciona a trace 'Total' (visível por padrão)
df_total_por_mes = df_linha_cidade.groupby('Mês', sort=False)['Casos Confirmados'].sum().reset_index()
fig_line.add_trace(go.Scatter(
    x=df_total_por_mes['Mês'],
    y=df_total_por_mes['Casos Confirmados'],
    mode='lines+markers',
    name='Total',
    visible=True
))

# 5. Adiciona traces para cada município (invisíveis por padrão)
for i, cidade in enumerate(municipios[1:]): # Ignora 'Total'
    df_cidade = df_linha_cidade[df_linha_cidade['municipio'] == cidade]
    fig_line.add_trace(go.Scatter(
        x=df_cidade['Mês'],
        y=df_cidade['Casos Confirmados'],
        mode='lines+markers',
        name=cidade,
        visible=False  # Inicialmente invisível
    ))

# 6. Cria os botões do Dropdown
dropdown_buttons = []
for i, cidade in enumerate(municipios):
    # 'visible' é um array booleano: True apenas para a trace correspondente
    visibility = [False] * len(municipios)
    visibility[i] = True 
    
    # Se for o 'Total', usa o índice 0. Se for cidade, usa o índice (i).
    trace_index = i 
    
    dropdown_buttons.append(dict(
        label=cidade,
        method='update',
        args=[
            {'visible': [i == trace_index for i in range(len(fig_line.data))]}, # Alterna a visibilidade
            {'title': f'Evolução de Casos Confirmados - {cidade}', 
             'showlegend': False}
        ]
    ))

# 7. Adiciona o dropdown menu ao layout do gráfico
fig_line.update_layout(
    updatemenus=[dict(
        active=0, # O primeiro item da lista ('Total') é o padrão
        buttons=dropdown_buttons,
        direction="down",
        x=0.01,
        xanchor="left",
        y=1.15,
        yanchor="top"
    )],
    title='Evolução de Casos Confirmados - Total (Todas as Cidades)',
    xaxis_title='Mês',
    yaxis_title='Casos Confirmados',
    height=500
)

# FIM DO CÓDIGO NOVO/MODIFICADO

# Tabela resumo: Casos por Município
df_tabela = df.copy()
df_tabela['total_notificados'] = df_tabela[[f'{m}_notificados' for m in ['janeiro', 'fevereiro', 'março', 'abril', 'maio']]].sum(axis=1)
df_tabela['total_confirmados'] = df_tabela[[f'{m}_confirmados_autoctone' for m in ['janeiro', 'fevereiro', 'março', 'abril', 'maio']]].sum(axis=1) + \
                               df_tabela[[f'{m}_confirmados_importados' for m in ['janeiro', 'fevereiro', 'março', 'abril', 'maio']]].sum(axis=1)
df_resumo = df_tabela[['municipio', 'total_notificados', 'total_confirmados']]


# 3. Configuração do Flask e criação do dashboard
app = Flask(__name__)

@app.route('/')
def dashboard():
    # Converte os gráficos do Plotly para HTML
    grafico_barras_html = fig_bar.to_html(full_html=False)
    grafico_pizza_html = fig_pie.to_html(full_html=False)
    grafico_linha_html = fig_line.to_html(full_html=False)
    tabela_html = df_resumo.to_html(index=False, classes='table table-striped table-hover', justify='center')
    
    # Renderiza o template HTML e passa as variáveis
    return render_template(
        'dashboard.html',
        grafico_barras_html=grafico_barras_html,
        grafico_pizza_html=grafico_pizza_html,
        grafico_linha_html=grafico_linha_html,
        tabela_html=tabela_html
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
