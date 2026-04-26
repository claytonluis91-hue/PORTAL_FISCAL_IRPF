import os
import requests
import yfinance as yf
import streamlit as st
from dotenv import load_dotenv
from typing import Dict, Optional, Any
import google.generativeai as genai

load_dotenv()

COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_dados_acao_b3(ticker: str) -> Dict[str, Any]:
    """
    Busca informações da Ação/FII via yfinance.
    Adiciona o sufixo .SA (padrão do Yahoo Finance para B3) automaticamente.
    """
    if not ticker:
        return {"nome": "", "cnpj": ""}
        
    ticker_sa = f"{ticker.upper()}.SA" if not ticker.upper().endswith(".SA") else ticker.upper()
    
    # Base local com CNPJs mais buscados do IRPF para facilitar a vida do usuário.
    # (Como as APIs gratuitas não retornam CNPJ).
    cnpjs_conhecidos = {
        "PETR3": "33.000.167/0001-01", "PETR4": "33.000.167/0001-01",
        "VALE3": "33.592.510/0001-54", "ITUB4": "60.872.504/0001-23",
        "ITUB3": "60.872.504/0001-23", "BBDC3": "60.746.948/0001-12",
        "BBDC4": "60.746.948/0001-12", "BBAS3": "00.000.000/0001-91",
        "WEGE3": "84.429.695/0001-11", "MXRF11": "11.187.351/0001-90",
        "HGLG11": "11.728.688/0001-47", "KNRI11": "12.005.956/0001-65",
        "BTLG11": "11.839.293/0001-09", "TAEE11": "07.859.971/0001-30"
    }
    
    cnpj_encontrado = cnpjs_conhecidos.get(ticker.upper(), "")
    
    try:
        ativo = yf.Ticker(ticker_sa)
        info = ativo.info
        
        if "shortName" in info or "longName" in info:
            nome = info.get("longName") or info.get("shortName") or ticker
            return {"nome": nome, "cnpj": cnpj_encontrado}
        else:
            return {"nome": "", "cnpj": cnpj_encontrado}
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return {"nome": "", "cnpj": cnpj_encontrado}

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_cotacao_historica_dezembro(ticker: str, ano: int) -> float:
    """
    Busca a cotação de fechamento do último dia útil do ano informado.
    """
    if not ticker:
        return 0.0
        
    ticker_sa = f"{ticker.upper()}.SA" if not ticker.upper().endswith(".SA") else ticker.upper()
    
    try:
        ativo = yf.Ticker(ticker_sa)
        # Pega do dia 20 até 31 de dezembro para garantir que cairá em dia útil
        historico = ativo.history(start=f"{ano}-12-20", end=f"{ano}-12-31")
        
        if not historico.empty:
            fechamento_final = historico.iloc[-1]['Close']
            return float(fechamento_final)
        return 0.0
    except Exception as e:
        print(f"Erro ao buscar cotação final de {ano} para {ticker}: {e}")
        return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def validar_criptomoeda_cmc(symbol: str) -> Dict[str, Any]:
    """
    Usa o CoinMarketCap para validar a sigla da moeda.
    Requer COINMARKETCAP_API_KEY no .env.
    """
    if not symbol:
        return {"valido": False, "nome": ""}
        
    if not COINMARKETCAP_API_KEY:
        # Fallback se não tiver chave configurada: retornar válido para não bloquear o usuário.
        return {"valido": True, "nome": symbol.upper(), "aviso": "Chave CMC ausente, validação suspensa."}

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
    }
    parameters = {"symbol": symbol.upper()}

    try:
        response = requests.get(url, headers=headers, params=parameters, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and symbol.upper() in data["data"]:
                nome = data["data"][symbol.upper()]["name"]
                return {"valido": True, "nome": nome}
            else:
                 return {"valido": False, "nome": ""}
        else:
            return {"valido": False, "nome": "", "erro": response.json().get('status', {}).get('error_message')}
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao CoinMarketCap: {e}")
        return {"valido": False, "nome": ""}

def gerar_insights_patrimonio_gemini(dados_variacao: dict) -> str:
    """
    Aciona a API do Gemini Pro para dar sugestões sobre Evolução Patrimonial a Descoberto.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        gemini_key = st.secrets["GEMINI_API_KEY"]
        
    if not gemini_key:
        return "A API Key do Gemini (GEMINI_API_KEY) não foi configurada. Configure no arquivo .env ou nos Secrets do Streamlit para usar esta função."
    
    genai.configure(api_key=gemini_key)
    
    prompt = f"""
    Atue como um auditor fiscal especialista em Imposto de Renda no Brasil (IRPF).
    Analise o seguinte cenário de um contribuinte:
    - Aumento Patrimonial (Diferença entre o Ano Atual e o Anterior): R$ {dados_variacao.get('aumento_patrimonial', 0):,.2f}
    - Disponibilidade de Caixa (Renda gerada menos as Despesas informadas): R$ {dados_variacao.get('disponibilidade', 0):,.2f}
    - Furo de Caixa (Diferença não justificada): R$ {dados_variacao.get('diferenca', 0):,.2f}
    
    O contribuinte está com o patrimônio "a descoberto" (evolução patrimonial incompatível com a renda).
    Liste, de forma cordial, em bullet points, quais são as 3 ou 4 causas mais comuns de erro de preenchimento que podem causar este furo (Ex: esqueceu de lançar lucros isentos, alienação de bens, doações recebidas, resgate de FGTS, financiamentos etc). Dê uma resposta direta e concisa.
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
         erro_str = str(e)
         print(f"Erro no Gemini: {erro_str}")
         
         if "429" in erro_str or "quota" in erro_str.lower():
             return "⌛ **Aviso de Limite (Google AI):** Você sobrecarregou o limite do plano gratuito do Google (que permite apenas algumas checagens por minuto). Por favor, aguarde cerca de 30 a 40 segundos e clique em Calcular novamente!"
             
         if "404" in erro_str or "not found" in erro_str.lower():
             try:
                 available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                 model_list_str = "\\n- ".join(available)
                 return f"**Erro 404: Modelo não encontrado.** \\nO Google mudou os nomes das APIs. Por favor, avise o engenheiro que a lista de modelos suportados atualmente por esta sua chave é: \\n- {model_list_str}"
             except Exception as sub_e:
                 return f"Erro ao tentar listar modelos: {sub_e}\\nErro original: {erro_str}"
                 
         return f"Infelizmente houve um erro com a Inteligência Artificial: {erro_str}"

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_dados_cnpj(cnpj: str) -> Dict[str, Any]:
    """
    Busca dados na BrasilAPI (Gratuita).
    Retorna Razão Social e checa CNAEs para inferir se há atuação mista (Comércio + Serviços).
    """
    # Remove pontuação
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj_limpo) != 14:
        return {"razao_social": "", "tem_comercio": False, "tem_servico": False}
        
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            razao = dados.get('razao_social', '')
            
            # Checagem rudimentar em textos de CNAE (Fiscal Principal e Secundários)
            textos_cnae = [str(dados.get('cnae_fiscal_descricao', '')).lower()]
            for sec in dados.get('cnaes_secundarios', []):
                textos_cnae.append(str(sec.get('descricao', '')).lower())
            
            tem_comercio = False
            tem_servico = False
            
            for t in textos_cnae:
                if 'comércio' in t or 'comercio' in t or 'venda' in t or 'varejista' in t:
                    tem_comercio = True
                if 'serviço' in t or 'servico' in t or 'manutenção' in t or 'reparação' in t or 'locação' in t:
                    tem_servico = True
                    
            return {
                "razao_social": razao,
                "tem_comercio": tem_comercio,
                "tem_servico": tem_servico
            }
    except Exception as e:
        print(f"Erro ao consultar CNPJ na BrasilAPI: {e}")
        
    return {"razao_social": "", "tem_comercio": False, "tem_servico": False}

