import pandas as pd
from typing import Optional

def calcular_preco_medio_b3(df_b3: pd.DataFrame) -> pd.DataFrame:
    """
    Motor FIFO de Custo Médio Ponderado para planilhas da Área do Investidor (B3).
    Espera colunas mapeadas ou aproximadas: 'Produto', 'Operação', 'Quantidade', 'Preço Unitário'.
    """
    if df_b3.empty:
        return pd.DataFrame()

    # Normalizar nomes de colunas esperadas na B3 (podem variar levemente)
    col_map = {c: c.upper().strip() for c in df_b3.columns}
    df_b3.rename(columns=col_map, inplace=True)
    
    # Identificar colunas reais baseadas em keywords
    col_produto = next((c for c in df_b3.columns if 'PRODUTO' in c or 'TICKER' in c or 'CÓDIGO' in c), None)
    col_operacao = next((c for c in df_b3.columns if 'OPERAÇÃO' in c or 'TIPO' in c or 'MOVIMENTAÇÃO' in c), None)
    col_qtde = next((c for c in df_b3.columns if 'QUANTIDADE' in c), None)
    col_preco = next((c for c in df_b3.columns if 'PREÇO' in c or 'VALOR' in c), None)

    if not all([col_produto, col_operacao, col_qtde, col_preco]):
         raise ValueError("A planilha B3 enviada não contém as colunas mínimas (Produto, Operação, Quantidade, Preço Unitário).")

    posicoes = {} # Dicionário {ticker: {'qtde': 0, 'custo_total': 0.0}}

    for _, row in df_b3.iterrows():
        # Limpar ticker extraindo geralmente a primeira palavra "PETR4 - PETROLEO..."
        raw_produto = str(row[col_produto]).strip()
        ticker = raw_produto.split(' ')[0] if ' ' in raw_produto else raw_produto
        ticker = ticker.split('-')[0]
        
        operacao = str(row[col_operacao]).upper().strip()
        
        try:
            qtde = float(str(row[col_qtde]).replace('.','').replace(',','.'))
            preco = float(str(row[col_preco]).replace('.','').replace(',','.'))
        except ValueError:
            continue # Pula linhas com cabeçalhos falsos ou totais
            
        valor_financeiro = qtde * preco

        if ticker not in posicoes:
            posicoes[ticker] = {'qtde': 0.0, 'custo_total': 0.0}

        # Aplicar regras de Custo Médio
        # Compra: Soma quantidade, soma custo financeiro. PM se recalcula naturalmente.
        if operacao.startswith('C') or 'COMPRA' in operacao:
             posicoes[ticker]['qtde'] += qtde
             posicoes[ticker]['custo_total'] += valor_financeiro
             
        # Venda: Subtrai quantidade. O custo debitado é proporcional ao Preço Médio!
        elif operacao.startswith('V') or 'VENDA' in operacao:
             # O Preço Médio atual:
             pm_atual = posicoes[ticker]['custo_total'] / posicoes[ticker]['qtde'] if posicoes[ticker]['qtde'] > 0 else 0
             posicoes[ticker]['qtde'] -= qtde
             
             # Se a pessoa vender tudo e sobrar residuo negativo, zeramos.
             if posicoes[ticker]['qtde'] <= 0.01:
                  posicoes[ticker]['qtde'] = 0.0
                  posicoes[ticker]['custo_total'] = 0.0
             else:
                  # O custo reduz na mesma proporção do PM
                  posicoes[ticker]['custo_total'] -= (qtde * pm_atual)

    # Transformar em DataFrame final ignorando zerados
    linhas = []
    for tck, dados in posicoes.items():
        if dados['qtde'] > 0:
            pm_final = dados['custo_total'] / dados['qtde']
            linhas.append({
                'Ticker': tck,
                'Quantidade Final': int(dados['qtde']),
                'Preco Medio': pm_final,
                'Custo Total Acumulado': dados['custo_total']
            })
            
    df_resultado = pd.DataFrame(linhas)
    return df_resultado



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
