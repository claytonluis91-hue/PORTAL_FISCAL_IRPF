import streamlit as st
import sys
import os

# Ajuste de path para importação local, muito comum em multi-page sem empacotamento completo.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_mei import processar_calculo_mei

st.set_page_config(page_title="Cálculo MEI", page_icon="🏢", layout="wide")

st.title("🏢 Apuração de Lucro MEI")
st.markdown("Calcule a Parcela Isenta e Tributável do seu Microempreendedor Individual.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entrada de Dados")
    ramo = st.selectbox(
        "Ramo de Atividade",
        ["Comércio/Indústria", "Transporte de Passageiros", "Serviços"]
    )
    
    receita_bruta = st.number_input("Receita Bruta Total Anual (R$)", min_value=0.0, step=1000.0, format="%.2f")
    despesas = st.number_input("Despesas Comprovadas com NFe/Recibos (R$)", min_value=0.0, step=100.0, format="%.2f")

with col2:
    st.subheader("Resultados e Fichas IRPF")
    if st.button("Calcular Lucro", type="primary"):
        if receita_bruta == 0:
             st.warning("Insira uma Receita Bruta maior que zero.")
        else:
             resultado = processar_calculo_mei(receita_bruta, despesas, ramo)
             
             lucro = resultado['lucro_total']
             isento = resultado['parcela_isenta']
             tributavel = resultado['parcela_tributavel']
             
             st.metric("Lucro Evidenciado (Receita - Despesas)", f"R$ {lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             
             st.success(f"**Parcela Isenta:** R$ {isento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             st.info(f"👉 **Lançar em:** Ficha 'Rendimentos Isentos e Não Tributáveis' - Cód. 13 (Rendimento de sócio ou titular de microempresa...)")
             
             st.warning(f"**Parcela Tributável:** R$ {tributavel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             st.info(f"👉 **Lançar em:** Ficha 'Rendimentos Tributáveis Recebidos de Pessoa Jurídica' - Informar o CNPJ do seu próprio MEI.")
