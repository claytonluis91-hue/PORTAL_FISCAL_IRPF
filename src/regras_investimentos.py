import pandas as pd
from typing import Optional

def calcular_preco_medio_b3(df_b3: pd.DataFrame) -> pd.DataFrame:
    """
    Função base para calcular preço médio de uma planilha importada da B3.
    (Versão inicial: Foca em processar a lista e consolidar saldos pelo valor financeiro)
    """
    if df_b3.empty:
        return df_b3
    
    # Validações mínimas de colunas (Data, Ticker, Operacao, Quantidade, Preço)
    # Assumindo formato padronizado B3
    # Lógica simplificada para a base - pode evoluir para FIFO real longo/curto
    # Para fins de hackathon/MVP: somar C/V
    
    # TODO: Implementar FIFO contábil estrito para abater do PM apenas as saídas pelo PM antigo
    posicoes = {}
    
    # Exemplo genérico estrutural:
    df_result = pd.DataFrame(columns=['Ticker', 'Quantidade Final', 'Preco Medio', 'Custo Total Acumulado'])
    return df_result


def gerar_discriminacao_acao_fii(ticker: str, qtde: int, custo_total: float, cnpj: str, nome: str, custodiante: str) -> str:
    """
    Gera sugerida a string de discriminação para Ações ou FIIs para a Dirpf.
    """
    tipo = "AÇÕES" if not ticker.endswith("11") else "COTAS DE FUNDO DE INVESTIMENTO"
    
    desc = f"{qtde} {tipo} DA EMPRESA/FUNDO {nome} (TICKER: {ticker}), "
    if cnpj:
         desc += f"CNPJ: {cnpj}, "
    
    custo_formatado = f"R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    desc += f"CUSTODIADAS EM: {custodiante}. VALOR DE AQUISIÇÃO: {custo_formatado}."
    
    return desc.upper()


def verificar_limite_mensal_in1888(df_cripto: pd.DataFrame) -> bool:
    """
    Avalia se o volume de transações mensais superou R$ 35k.
    Espera-se uma coluna 'Data' e 'Valor Total'.
    """
    if df_cripto.empty or 'Data' not in df_cripto.columns or 'Valor Total' not in df_cripto.columns:
         return False
         
    df_cripto['Data'] = pd.to_datetime(df_cripto['Data'])
    df_cripto['AnoMes'] = df_cripto['Data'].dt.to_period('M')
    
    mensal = df_cripto.groupby('AnoMes')['Valor Total'].sum()
    if any(mensal >= 35000.00):
        return True
        
    return False
