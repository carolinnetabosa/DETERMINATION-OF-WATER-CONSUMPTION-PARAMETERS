import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
import os
import glob
from scipy.interpolate import make_interp_spline, BSpline, CubicSpline # pra suavizar as linhas

# ----------------------------------------------------- Lendo os arquivos excel ----------------------------------------------------

# Selecionando todos os arquivos de vazao mensais
#arquivos = glob.glob('dados mensais\\vazao_*.xlsx')
arquivos = glob.glob('Downloads\TCC\dados mensais\\vazao_*.xlsx')

# Lista para armazenar os DataFrames de cada arquivo
dataframes = []

# Lendo cada arquivo em um DataFrame e adicionando à lista
for arquivo in arquivos:
    df = pd.read_excel(arquivo)
    dataframes.append(df)

# Concatenar os DataFrames em um único DataFrame
dados = pd.concat(dataframes)

#------------------------------------------ Tratando de forma básica os dados ---------------------------------------------------------

# Tirando a hora "00:00:00" padrão python das datas 
dados['data'] = pd.to_datetime(dados['data']).dt.date

# Excluindo duas colunas sem dados que estão aparecendo no dataframe
dados = dados.drop(dados.columns[[3, 4]], axis=1)

# Substituindo as vazões de 0 por NaN
dados['vazão (L/s)'] = dados['vazão (L/s)'].replace(0, np.nan)

# Substituindo os valores de vazão acima de 600 por NaN
dados.loc[dados['vazão (L/s)'] > 600, 'vazão (L/s)'] = np.nan

# Adicionando a coluna "dia_da_semana" às planilhas 
dados['dia_da_semana'] = pd.to_datetime(dados['data']).dt.day_name()

# Garantindo que a coluna 'data' esteja no formato datetime
dados['data'] = pd.to_datetime(dados['data'])

# Organizando a ordem das colunas
dados = dados[['data', 'dia_da_semana', 'hora', 'vazão (L/s)']]

print("dados: \n", dados)

# Parâmetro que determina o intervalo do desvio padrão: "desv"
desv = 1.5

# --------------------------------------------------------------------- K1-------------------------------------------------------------

# Calculando a média e o desvio padrão pra cada data
media_por_data = dados.groupby('data')['vazão (L/s)'].mean()
desvio_padrao_por_data = dados.groupby('data')['vazão (L/s)'].std()

#print("\n dados: \n",dados)

# Definindo os limites com os outliers sendo +-desv * desvio + média
limite_superior_por_data = media_por_data + desv * desvio_padrao_por_data
limite_inferior_por_data = media_por_data - desv * desvio_padrao_por_data



# GRÁFICO DOS DADOS ANTES DA FILTRAGEM (DEMONSTRANDO O DESVIO PADRAO)

# # Plotando os dados de vazão ao longo do tempo
# plt.figure(figsize=(10, 10))

# # Plotando os limites superior e inferior do desvio padrão em relação à média por data
# plt.plot(media_por_data.index, media_por_data.values, color='red', label='Vazão média diária')
# plt.plot(limite_superior_por_data.index, limite_superior_por_data.values, color='green', label='Limite Superior')
# plt.plot(limite_inferior_por_data.index, limite_inferior_por_data.values, color='green', label='Limite Inferior')

# # Plotando os dados de vazão
# plt.scatter(dados['data'], dados['vazão (L/s)'], label='Vazões diárias', color='blue', alpha=0.5, s=0.5)


# # Adicionando título e rótulos dos eixos
# plt.title('Vazão ao longo do tempo com Média e Desvio Padrão por Data')
# plt.xlabel('Data')
# plt.ylabel('Vazão (L/s)')

# # Adicionando legenda
# plt.legend(fontsize=13)

# # Rotacionando os rótulos do eixo x para facilitar a leitura
# plt.xticks(rotation=45)

# # Exibindo o gráfico
# plt.grid(True)
# plt.tight_layout()
# plt.show()



# Aplicando esses limites para filtrar os dados correspondentes para cada data
dados_filtrados_por_data = {}

for data in dados['data'].unique():
    dados_data = dados[dados['data'] == data]
    filtro_superior_data = dados_data['vazão (L/s)'] <= limite_superior_por_data[data]
    filtro_inferior_data = dados_data['vazão (L/s)'] >= limite_inferior_por_data[data]
    dados_filtrados_por_data[data] = dados_data[filtro_superior_data & filtro_inferior_data]

#print("\n dados iniciais filtrados por data\n",dados_filtrados_por_data)

# Os dados por data já foram filtrados com o desvio padrão, agora vão ser feitas as operações pra obter os resultados e gráficos -----

# Criando um DataFrame para armazenar as médias de vazão por data (VAZÕES MÉDIAS DIÁRIAS)
vazao_media_por_data_df = pd.DataFrame(columns=['data', 'vazão (L/s)'])

# Iterando sobre os dados filtrados para cada data
for data, dados_filtrados_data in dados_filtrados_por_data.items():
    vazao_media_data = dados_filtrados_data['vazão (L/s)'].mean()
    # Adicionando a média de vazão para a data atual ao DataFrame
   # vazao_media_por_data_df = vazao_media_por_data_df.append({'data': data, 'vazão (L/s)': vazao_media_data}, ignore_index=True)
    vazao_media_por_data_df = pd.concat([vazao_media_por_data_df, pd.DataFrame({'data': [data], 'vazão (L/s)': [vazao_media_data]})], ignore_index=True)

#print("\n Vazoes medias por data \n", vazao_media_por_data_df)

# Encontrando a vazão MÉDIA após filtragem (MÉDIA DAS MÉDIAS DIÁRIAS)
Qmedia_filtrada_data = vazao_media_por_data_df['vazão (L/s)'].mean()
print("\n vazao media filtrada por data", Qmedia_filtrada_data)

# Encontrando a vazão MÁXIMA após filtragem
Qmax_k1 = vazao_media_por_data_df['vazão (L/s)'].max()
print("\n Qmax k1: \n", Qmax_k1)

# k1
k1 = Qmax_k1/Qmedia_filtrada_data
print("\n k1: ", k1)


# -------------------------------------------------------------- GRÁFICO K1

# Plotando os dados de vazão ao longo do tempo
plt.figure(figsize=(10, 10))
x = vazao_media_por_data_df['data']
y = vazao_media_por_data_df['vazão (L/s)']

# plt.rcParams['xtick.labelsize'] = 16
# plt.rcParams['ytick.labelsize'] = 16

plt.plot(x, y, label='Vazão', color='blue')

# Plotando a linha da vazão média
plt.axhline(y=Qmedia_filtrada_data, color='red', linestyle='--', label='Vazão Média')

# Obtendo a data correspondente a vazao maxima
data_vazao_max = vazao_media_por_data_df.loc[vazao_media_por_data_df['vazão (L/s)'].idxmax(), 'data']
print("\n data da vazao maxima anual (pra k1): ", data_vazao_max)

# Plotar o ponto de vazão máxima
plt.scatter(data_vazao_max, Qmax_k1, color='red', label='Vazão máxima')

# Adicionando título e rótulos dos eixos
plt.title('Variação do consumo ao longo de 12 meses (k1)')
plt.xlabel('Data', fontsize = 18)
plt.ylabel('Vazão (L/s)', fontsize = 18)

# Adicionando legenda
plt.legend(fontsize=14)

# Rotacionando os rótulos do eixo x para facilitar a leitura
plt.xticks(rotation=45)

# Exibindo o gráfico
plt.grid(True)
plt.tight_layout()
plt.show()

# -------------------------------------------------------------- k2 -------------------------------------------------------------------

# Calculando a média e o desvio padrão pra cada horário
media_por_horario = dados.groupby('hora')['vazão (L/s)'].mean()
desvio_padrao_por_horario = dados.groupby('hora')['vazão (L/s)'].std()

# Definindo os limites com os outliers sendo +-desv * desvio + média
limite_superior_por_horario = media_por_horario + desv * desvio_padrao_por_horario
limite_inferior_por_horario = media_por_horario - desv * desvio_padrao_por_horario



# # GRÁFICO DOS DADOS ANTES DA FILTRAGEM (DEMONSTRANDO O DESVIO PADRAO)

# # Plotando os dados de vazão ao longo do tempo
# plt.figure(figsize=(10, 10))

# # Plotando os limites superior e inferior do desvio padrão em relação à média por horário
# plt.plot(media_por_horario.index.astype(str), media_por_horario.values, color='red', label='Vazões médias horárias')
# plt.plot(limite_superior_por_horario.index.astype(str), limite_superior_por_horario.values, color='green', label='Limite Superior')
# plt.plot(limite_inferior_por_horario.index.astype(str), limite_inferior_por_horario.values, color='green', label='Limite Inferior')

# # Convertendo os valores da coluna 'hora' para strings
# dados['hora'] = dados['hora'].astype(str)

# # Plotando os dados de vazão
# plt.scatter(dados['hora'], dados['vazão (L/s)'], label='Vazões horárias', color='blue', alpha=0.5, s=2)  # Defina o tamanho dos pontos ajustando o valor de 's'

# # Adicionando título e rótulos dos eixos
# plt.title('Vazão ao longo do tempo com Média e Desvio Padrão por Horário')
# plt.xlabel('Hora')
# plt.ylabel('Vazão (L/s)')

# # Adicionando legenda
# plt.legend(fontsize=13)

# # Rotacionando os rótulos do eixo x para facilitar a leitura
# plt.xticks(rotation=90)

# # Exibindo o gráfico
# plt.grid(True)
# plt.tight_layout()
# plt.show()




# Aplicando esses limites para filtrar os dados correspondentes para cada horário
dados_filtrados_por_horario = {}

for horario in dados['hora'].unique():
    dados_horario = dados[dados['hora'] == horario]
    filtro_superior = dados_horario['vazão (L/s)'] <= limite_superior_por_horario[horario]
    filtro_inferior = dados_horario['vazão (L/s)'] >= limite_inferior_por_horario[horario]
    dados_filtrados_por_horario[horario] = dados_horario[filtro_superior & filtro_inferior]

#print("\n dados completos depois do filtro: \n",dados_filtrados_por_horario)

# Criando um DataFrame para armazenar as médias (filtradas) de vazão por horario
vazao_media_por_horario_df = pd.DataFrame(columns=['hora', 'vazão (L/s)'])

# Iterando sobre os dados filtrados para cada horario
for horario, dados_filtrados_horario in dados_filtrados_por_horario.items():
    vazao_media_horario = dados_filtrados_horario['vazão (L/s)'].mean()
    # Adicionando a média de vazão para a data atual ao DataFrame
    vazao_media_por_horario_df = pd.concat([vazao_media_por_horario_df, pd.DataFrame({'hora': [horario], 'vazão (L/s)': [vazao_media_horario]})], ignore_index=True)

#print("\n vazao media por horario: \n",vazao_media_por_horario_df)

# Encontrando a vazão MÉDIA após filtragem
Qmedia_filtrada_horario = vazao_media_por_horario_df['vazão (L/s)'].mean()
print("\n Qmedia filtrada horario", Qmedia_filtrada_horario)

# Encontrando a vazão MÁXIMA após filtragem
Qmax_k2 = vazao_media_por_horario_df['vazão (L/s)'].max()
print("\n Qmax k2: \n", Qmax_k2)

# k2
k2 = Qmax_k2/Qmedia_filtrada_horario
print("\n k2: ", k2)


# ---------------------------------------------------- k3 ----------------------------------------------------

# Encontrando a vazão MÍNIMA após filtragem
Qmin_k3 = vazao_media_por_horario_df['vazão (L/s)'].min()
print("\n qmin k3: \n", Qmin_k3)

# Valor de k3
k3 = Qmin_k3/Qmedia_filtrada_horario
print("\n k3: ", k3)


# -------------------------------------------------------------- GRÁFICO k2 e k3

# Plotando os dados de vazão ao longo do tempo
plt.figure(figsize=(14, 6))

# Converter a lista em uma série do pandas
#vazao_media_por_horario_series = pd.Series(vazao_media_por_horario.df)

# Plotar os dados de vazão ao longo do tempo
x = vazao_media_por_horario_df['hora'].astype(str)
y = vazao_media_por_horario_df['vazão (L/s)']
plt.plot(x, y, label='Vazão', color='blue')

# Plotando a linha da vazão média
plt.axhline(y=Qmedia_filtrada_horario, color='red', linestyle='--', label='Vazão Média')

# Obtendo a hora correspondente a VAZÃO MAXIMA
#linha_vazao_max = vazao_media_por_horario_df[vazao_media_por_horario_df == Qmax_k2]
hora_vazao_max = vazao_media_por_horario_df.loc[vazao_media_por_horario_df['vazão (L/s)'].idxmax(), 'hora']
print("\n hora da vazao maxima diaria (para k2): ", hora_vazao_max)
# Plotar o ponto de vazão máxima
plt.scatter(str(hora_vazao_max), Qmax_k2, color='red', label='Vazão máxima')


# Obtendo a data correspondente a VAZÃO MINIMA
#linha_vazao_min = vazao_media_por_horario_df[vazao_media_por_horario_df == Qmin_k3]
hora_vazao_min = vazao_media_por_horario_df.loc[vazao_media_por_horario_df['vazão (L/s)'].idxmin(), 'hora']
print("\n hora da vazao minima diaria (para k3): ", hora_vazao_min)
# Plotar o ponto de vazão mínima
plt.scatter(str(hora_vazao_min), Qmin_k3, color='green', label='Vazão mínima')

# Adicionando título e rótulos dos eixos
plt.title('Variação do consumo ao longo de 1 dia (k2 e k3)')
plt.xlabel('Hora do dia', fontsize = 18)
plt.ylabel('Vazão (L/s)', fontsize = 18)

# Adicionando legenda
plt.legend(fontsize=13)

# Rotacionando os rótulos do eixo x para facilitar a leitura
plt.xticks(rotation=90)

# Exibindo o gráfico
plt.grid(True)
plt.tight_layout()
plt.show()


# ---------------------------------------- Análise do consumo diário pelo dia da semana ----------------------------------------------

# Função para processar dados de cada dia
def processar_dia(dia, dados):
    # Filtrando os dados para o dia específico
    dados_dia = dados[dados['dia_da_semana'] == dia]

    # Média e desvio padrão por hora
    media_horaria = dados_dia.groupby('hora')['vazão (L/s)'].mean()
    desvio_horario = dados_dia.groupby('hora')['vazão (L/s)'].std()

    # Determinando os limites
    lim_inf = media_horaria - desv * desvio_horario
    lim_sup = media_horaria + desv * desvio_horario

    # Filtrando os dados para manter os valores dentro dos limites
    dados_filtrados = []
    for horario in dados_dia['hora'].unique():
        dados_horario = dados_dia[dados_dia['hora'] == horario]
        filtro_limite = (dados_horario['vazão (L/s)'] >= lim_inf[horario]) & (dados_horario['vazão (L/s)'] <= lim_sup[horario])
        dados_filtrados.append(dados_horario[filtro_limite])

    dados_filtrados_concat = pd.concat(dados_filtrados)
    return dados_filtrados_concat.groupby('hora')['vazão (L/s)'].mean()

# Dicionário para armazenar as médias de vazões por hora para cada dia
dias_da_semana = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
medias_por_dia_da_semana = {}

# Processando os dados para cada dia da semana
for dia in dias_da_semana:
    medias_por_dia_da_semana[dia] = processar_dia(dia, dados)

# Configurações do gráfico
plt.figure(figsize=(14, 6))  # Tamanho do gráfico

# Plotar as curvas de média das vazões por hora para cada dia da semana
for dia, medias in medias_por_dia_da_semana.items():
    # Converter os índices (horas) para strings
    horas_str = [str(hora) for hora in medias.index]
    plt.plot(horas_str, medias.values, label=dia)

# Adicionar rótulos aos eixos
plt.xlabel('Hora do dia', fontsize=18)
plt.ylabel('Vazão média (L/s)', fontsize=18)

# Adicionar um título ao gráfico
plt.title('Consumo médio diário ao longo dos dias da semana')

plt.grid(True)

# Rotacionar as informações do eixo x para melhor visualização
plt.xticks(rotation=90)

# Adicionar uma legenda
plt.legend(fontsize=13)

# Mostrar o gráfico
plt.tight_layout()  # Ajustar layout para evitar sobreposição de legendas
plt.show()

