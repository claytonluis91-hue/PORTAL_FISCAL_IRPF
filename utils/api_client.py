import os
import requests
import yfinance as yf
import streamlit as st
from dotenv import load_dotenv
from typing import Dict, Optional, Any

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
