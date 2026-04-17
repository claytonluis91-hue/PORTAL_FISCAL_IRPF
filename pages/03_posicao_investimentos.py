import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_investimentos import gerar_discriminacao_acao_fii, calcular_preco_medio_b3, verificar_limite_mensal_in1888
from utils.api_client import buscar_dados_acao_b3, validar_criptomoeda_cmc

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
    
    if st.button("Gerar Discriminação Automática (Ações/FIIs)", type="primary"):
        bens_atualizados = bens_editados.copy()
        
        for index, row in bens_atualizados.iterrows():
            ticker = str(row.get('Ticker', '')).strip()
            if ticker and pd.notna(ticker) and ticker != "None":
                
                # Busca API apenas se não preenchido
                if pd.isna(row.get('Nome da Empresa')) or not str(row.get('Nome da Empresa')).strip():
                     completions = buscar_dados_acao_b3(ticker)
                     bens_atualizados.at[index, 'Nome da Empresa'] = completions.get('nome', '')
                
                qtde = row.get('Quantidade', 0)
                qtde = int(qtde) if pd.notna(qtde) else 0
                
                custo = row.get('Custo Total', 0.0)
                custo = float(custo) if pd.notna(custo) else 0.0
                
                cnpj = str(row.get('CNPJ', '')) if pd.notna(row.get('CNPJ')) else ''
                nome = str(row.get('Nome da Empresa', '')) if pd.notna(row.get('Nome da Empresa')) else ''
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
