from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import pandas as pd
from datetime import datetime
import os
import time

# Configuração do WebDriver
options = Options()
options.headless = True
driver = webdriver.Chrome()

# Acessar o site
driver.get('https://rpachallengeocr.azurewebsites.net')

# Função para ler e minerar as linhas da tabela
def coletar_dados_tabela():
    dados = []
    while True:
        linhas_tabela = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        for linha in linhas_tabela:
            colunas = linha.find_elements(By.TAG_NAME, 'td')
            if len(colunas) >= 4: # verifica a quantidade de colunas na tabela do site
                numero = colunas[0].text
                id_fatura = colunas[1].text
                data_vencimento = colunas[2].text
                url_elemento = colunas[3].find_elements(By.TAG_NAME, 'a')
                url = url_elemento[0].get_attribute('href') if url_elemento else None
                dados.append({
                    'Número da Fatura': numero,
                    'ID da Fatura': id_fatura,
                    'Data da Fatura': data_vencimento,
                    'URL da Fatura': url
                })
        
        # Tenta encontrar o botão de "próxima página"
        try:
            botao_proxima = driver.find_element(By.CSS_SELECTOR, 'a.next')
            if 'disabled' in botao_proxima.get_attribute('class'):
                break
            botao_proxima.click() 
            time.sleep(2) # Aqui seria melhor um WebDriverWait
        except:
            break 
    
    return dados

# Função para baixar as faturas
def baixar_faturas(dados, caminho_download, ids_validos):
    if not os.path.exists(caminho_download):
        os.makedirs(caminho_download)
    
    for item in dados:
        if item['ID da Fatura'] in ids_validos and item['URL da Fatura']:
            resposta = requests.get(item['URL da Fatura'])
            nome_arquivo = os.path.join(caminho_download, f"{item['ID da Fatura']}.jpg")
            with open(nome_arquivo, 'wb') as f:
                f.write(resposta.content)

# Função para salvar os dados em CSV
def salvar_csv(dados, caminho_csv):
    df = pd.DataFrame(dados)
    df.to_csv(caminho_csv, index=False)

# Filtragem para incluir somente as faturas com vencimento igual ou anterior a 01-08-2024
def filtrar_dados(dados, data_limite):
    data_limite = datetime.strptime(data_limite, '%d-%m-%Y')
    dados_filtrados = [item for item in dados if datetime.strptime(item['Data da Fatura'], '%d-%m-%Y') <= data_limite]
    return dados_filtrados

# Lê o CSV e obtém a lista de IDs válidos
def obter_ids_validos_csv(caminho_csv):
    df = pd.read_csv(caminho_csv)
    return set(df['ID da Fatura'].astype(str))

# Executar as funções
dados = coletar_dados_tabela()
dados_filtrados = filtrar_dados(dados, '01-08-2024')
salvar_csv(dados_filtrados, 'faturas.csv')

# Obter IDs válidos do CSV
ids_validos = obter_ids_validos_csv('faturas.csv')

# Baixar as faturas
baixar_faturas(dados_filtrados, 'faturas', ids_validos)

# Fechar o WebDriver
driver.quit()