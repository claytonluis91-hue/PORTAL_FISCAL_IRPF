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
    
    try:
        ativo = yf.Ticker(ticker_sa)
        info = ativo.info
        
        if "shortName" in info or "longName" in info:
            nome = info.get("longName") or info.get("shortName") or ticker
            # CNPJ geralmente não vem fácil no yfinance, é uma limitação conhecida.
            # Idealmente, poderíamos cruzar com a API de dados abertos da CVM ou Brapi.
            # Como a Brapi é paga ou instável na versão free, manteremos blank para ser preenchido manualmente
            # a menos que integramos a Brapi.
            return {"nome": nome, "cnpj": ""}
        else:
            return {"nome": "", "cnpj": ""}
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return {"nome": "", "cnpj": ""}

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
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
         print(f"Erro no Gemini: {e}")
         return f"Infelizmente houve um erro com a Inteligência Artificial: {str(e)}"

