import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_investimentos import gerar_discriminacao_acao_fii, calcular_preco_medio_b3, verificar_limite_mensal_in1888
from utils.api_client import buscar_dados_acao_b3, validar_criptomoeda_cmc, buscar_cotacao_historica_dezembro

st.set_page_config(page_title="Posição de Investimentos", page_icon="📈", layout="wide")

st.title("📈 Posição de Investimentos (Ações, FIIs e Cripto)")
st.markdown("Apure o seu Preço Médio e gere o texto para a ficha de Bens e Direitos.")
st.markdown("---")

aba1, aba2, aba3 = st.tabs(["📊 Importação B3", "✍️ Lançamento Manual (Ações/FIIs)", "₿ Criptoativos"])

with aba1:
    st.subheader("Processar Planilha Área do Investidor (B3)")
    arquivo_b3 = st.file_uploader("Envie a planilha de movimentações (Excel/CSV)", type=["xlsx", "csv"])
    
    if arquivo_b3:
        # Apenas mock/base para ler o dataframe
        try:
            if arquivo_b3.name.endswith(".csv"):
                df_b3 = pd.read_csv(arquivo_b3)
            else:
                df_b3 = pd.read_excel(arquivo_b3)
                
            with st.expander("Ver dados brutos extraídos"):
                 st.dataframe(df_b3.head())
                 
            with st.spinner("Processando FIFO B3..."):
                 df_resultado = calcular_preco_medio_b3(df_b3)
                 
            if df_resultado.empty:
                 st.warning("Não encontrei movimentações válidas de compra e venda na planilha.")
            else:
                 st.success("✅ Posição Final Consolidada (Base Custo Médio)")
                 st.dataframe(
                     df_resultado, 
                     use_container_width=True,
                     column_config={
                         "Quantidade Final": st.column_config.NumberColumn(format="%d"),
                         "Preco Medio": st.column_config.NumberColumn(format="R$ %.2f"),
                         "Custo Total Acumulado": st.column_config.NumberColumn(format="R$ %.2f")
                     }
                 )
                 
        except Exception as e:
            st.error(f"Erro ao processar as regras neste arquivo: {e}")

with aba2:
    st.subheader("Bens e Direitos (Cód. 31/73)")
    st.markdown("Lançamento manual a partir de informes de corretoras/bancos.")
    
    with st.expander("🔍 Consultar Cotação de Fechamento (Dezembro)", expanded=False):
         st.caption("Verifique o preço real da ação/FII no fechamento do ano para auxiliar nas suas conciliações.")
         c_ticker, c_ano, c_btn = st.columns([2, 1, 1])
         with c_ticker:
              hist_ticker = st.text_input("Ticker B3 (Ex: PETR4)", key="hist_ticker")
         with c_ano:
              hist_ano = st.number_input("Ano Base", min_value=2000, max_value=2030, value=2024, step=1, key="hist_ano")
         with c_btn:
              st.write("")
              st.write("")
              if st.button("Buscar Cotação"):
                   if hist_ticker:
                        cotacao = buscar_cotacao_historica_dezembro(hist_ticker, hist_ano)
                        if cotacao > 0:
                             st.success(f"O fechamento de {hist_ticker.upper()} em Dez/{hist_ano} foi **R$ {cotacao:.2f}**")
                        else:
                             st.error("Não encontrei cotação para o ano ou ticker especificado.")
    
    st.markdown("---")
    
    # Inicializa o estado se não existir
    if 'bens_manuais' not in st.session_state:
        st.session_state['bens_manuais'] = pd.DataFrame(
            columns=['Ticker', 'Quantidade', 'Custo Total', 'CNPJ', 'Nome da Empresa', 'Instituição Custodiante', 'Discriminação Sugerida']
        )
    
    # Exibe o data_editor
    bens_editados = st.data_editor(
        st.session_state['bens_manuais'],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Quantidade": st.column_config.NumberColumn(min_value=0, step=1),
            "Custo Total": st.column_config.NumberColumn(min_value=0.0, format="R$ %.2f")
        }
    )
    
    # Preenchimento automático on the fly (quando Ticker é inserido)
    houve_alteracao = False
    for index, row in bens_editados.iterrows():
        ticker = str(row.get('Ticker', '')).strip()
        if ticker and ticker != "None":
            nome_vazio = pd.isna(row.get('Nome da Empresa')) or not str(row.get('Nome da Empresa')).strip()
            cnpj_vazio = pd.isna(row.get('CNPJ')) or not str(row.get('CNPJ')).strip()
            
            if nome_vazio or cnpj_vazio:
                completions = buscar_dados_acao_b3(ticker)
                if nome_vazio and completions.get('nome'):
                     bens_editados.at[index, 'Nome da Empresa'] = completions.get('nome', '')
                     houve_alteracao = True
                if cnpj_vazio and completions.get('cnpj'):
                     bens_editados.at[index, 'CNPJ'] = completions.get('cnpj', '')
                     houve_alteracao = True
                     
    if houve_alteracao:
        st.session_state['bens_manuais'] = bens_editados
        st.rerun()
    
    if st.button("Gerar Discriminação Automática (Ações/FIIs)", type="primary"):
        bens_atualizados = bens_editados.copy()
        
        for index, row in bens_atualizados.iterrows():
            ticker = str(row.get('Ticker', '')).strip()
            if ticker and pd.notna(ticker) and ticker != "None":
                
                # Usar preenchimento já existente do grid
                nome = str(row.get('Nome da Empresa', '')) if pd.notna(row.get('Nome da Empresa')) else ''
                cnpj = str(row.get('CNPJ', '')) if pd.notna(row.get('CNPJ')) else ''
                
                # Fallback API se estiver vazio de alguma forma contornando a view
                if not nome or not cnpj:
                     completions = buscar_dados_acao_b3(ticker)
                     nome = nome or completions.get('nome', '')
                     cnpj = cnpj or completions.get('cnpj', '')
                     bens_atualizados.at[index, 'Nome da Empresa'] = nome
                     bens_atualizados.at[index, 'CNPJ'] = cnpj
                
                qtde = row.get('Quantidade', 0)
                qtde = int(qtde) if pd.notna(qtde) else 0
                
                custo = row.get('Custo Total', 0.0)
                custo = float(custo) if pd.notna(custo) else 0.0
                
                custodiante = str(row.get('Instituição Custodiante', '')) if pd.notna(row.get('Instituição Custodiante')) else 'A CORRETORA'
                
                if qtde > 0:
                    texto = gerar_discriminacao_acao_fii(ticker, qtde, custo, cnpj, nome, custodiante)
                    bens_atualizados.at[index, 'Discriminação Sugerida'] = texto
                    
        st.session_state['bens_manuais'] = bens_atualizados
        st.rerun()

with aba3:
    st.subheader("Criptoativos (Cód. 81, 82, 83, 89)")
    
    col_crypto1, col_crypto2 = st.columns(2)
    with col_crypto1:
         codigo_bem = st.selectbox("Código do Bem", ["81 - Bitcoin (BTC)", "82 - Altcoins", "83 - Stablecoins", "89 - NFTs/Outros"])
         local_custodia = st.selectbox("Local de Custódia", ["Exchange no Brasil", "Exchange no Exterior", "Wallet Privada"])
         
    with col_crypto2:
         simbolo = st.text_input("Símbolo (Ex: BTC, ETH)", max_chars=10)
         transacionado_mes = st.number_input("Soma das alienações mensais (Vendas/Permutas) R$", min_value=0.0, step=1000.0)
         
    if st.button("Validar Cripto e Obrigações Mensais"):
         if simbolo:
             val_data = validar_criptomoeda_cmc(simbolo)
             if val_data.get('valido'):
                 st.success(f"Criptoativo Válido: {val_data.get('nome')} ({simbolo.upper()})")
                 if 'aviso' in val_data:
                      st.info(val_data['aviso'])
             else:
                 msg_erro = val_data.get('erro', 'Símbolo não encontrado.')
                 st.error(f"Erro na validação: {msg_erro}")
                 
         if transacionado_mes > 35000.00:
             st.warning("⚠️ ALERTA IN 1.888: Suas movimentações neste mês superaram R$ 35.000,00. Você está obrigado a realizar a declaração mensal no e-CAC e deverá apurar GCAP (Ganho de Capital) se houver lucro.")
         else:
             st.success("Tudo certo: Limite de isenção de ganhos até R$ 35k atingido para alienações mensais (Não dispensa declaração anual do saldo).")
