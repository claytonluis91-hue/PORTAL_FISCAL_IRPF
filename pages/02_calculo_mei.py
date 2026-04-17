import streamlit as st
import sys
import os

# Ajuste de path para importação local, muito comum em multi-page sem empacotamento completo.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_mei import processar_calculo_mei

import io
from fpdf import FPDF
from utils.api_client import buscar_dados_cnpj

st.set_page_config(page_title="Cálculo MEI", page_icon="🏢", layout="wide")

def gerar_pdf_mei(cnpj, razao, ano, receita_bruta, despesas, lucro, isento, tributavel, inss_anual):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16, style="B")
    pdf.cell(0, 10, "INFORME DE RENDIMENTOS MEI", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, f"Dados da Empresa", ln=True)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, f"CNPJ: {cnpj if cnpj else 'Não informado'}", ln=True)
    pdf.cell(0, 8, f"Razão Social: {razao if razao else 'Não informado'}", ln=True)
    pdf.cell(0, 8, f"Ano-Base: {ano}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, f"Valores Apurados", ln=True)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, f"Receita Bruta Total: R$ {receita_bruta:,.2f}", ln=True)
    pdf.cell(0, 8, f"Despesas Comprovadas: R$ {despesas:,.2f}", ln=True)
    pdf.cell(0, 8, f"INSS (Previdência Oficial / DAS): R$ {inss_anual:,.2f}", ln=True)
    pdf.cell(0, 8, f"Lucro Evidenciado (Base de Calculo): R$ {lucro:,.2f}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, f"Distribuição para IRPF", ln=True)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, f"Parcela Isenta (Rendimentos Isentos): R$ {isento:,.2f}", ln=True)
    pdf.cell(0, 8, f"Parcela Tributável (Rend. Rec. P.J.): R$ {tributavel:,.2f}", ln=True)
    
    return bytes(pdf.output())

st.title("🏢 Apuração de Lucro MEI")
st.markdown("Calcule a Parcela Isenta e Tributável do seu Microempreendedor Individual.")
st.markdown("---")

# Seção CNPJ
with st.expander("🔍 Busca de Empresa (Opcional)", expanded=True):
    c_cnpj, c_btn = st.columns([3, 1])
    with c_cnpj:
        cnpj_input = st.text_input("Digite o CNPJ do MEI (Apenas números)", key="cnpj_mei")
    with c_btn:
        st.write("")
        st.write("")
        if st.button("Buscar Dados CNPJ"):
             if cnpj_input:
                 with st.spinner("Consultando na Receita (BrasilAPI)..."):
                     dados_cnpj = buscar_dados_cnpj(cnpj_input)
                     if dados_cnpj.get('razao_social'):
                         st.session_state['razao_input'] = dados_cnpj['razao_social']
                         st.session_state['tem_comercio'] = dados_cnpj['tem_comercio']
                         st.session_state['tem_servico'] = dados_cnpj['tem_servico']
                         st.success(f"Empresa: {dados_cnpj['razao_social']}")
                     else:
                         st.error("CNPJ não encontrado.")

razao_atual = st.session_state.get('razao_input', '')
s_comercio = st.session_state.get('tem_comercio', False)
s_servico = st.session_state.get('tem_servico', False)
is_misto_api = s_comercio and s_servico

col1, col2 = st.columns(2)

with col1:
    st.subheader("Entrada de Dados")
    razao_social = st.text_input("Razão Social", value=razao_atual, key="razao_input")
    
    is_misto = st.checkbox("A empresa atua em formato HÍBRIDO (Comércio + Serviços)?", value=is_misto_api)
    
    if is_misto:
        st.info("Formato Híbrido ativado. Informe o faturamento separado.")
        ramo = "Híbrido/Misto"
        receita_comercio = st.number_input("Receita de Comércio (8%) (R$)", min_value=0.0, step=1000.0, format="%.2f")
        receita_servico = st.number_input("Receita de Serviços (32%) (R$)", min_value=0.0, step=1000.0, format="%.2f")
        receita_bruta = receita_comercio + receita_servico
    else:
        ramo = st.selectbox(
            "Ramo de Atividade Predominante",
            ["Comércio/Indústria", "Transporte de Passageiros", "Serviços"]
        )
        receita_bruta = st.number_input("Receita Bruta Total Anual (R$)", min_value=0.0, step=1000.0, format="%.2f")
        receita_comercio = 0.0
        receita_servico = 0.0
        
    despesas = st.number_input("Despesas Comprovadas com NFe/Recibos + Guias DAS (R$)", min_value=0.0, step=100.0, format="%.2f")
    
    st.markdown("---")
    st.markdown("**Cálculo Rápido de INSS / Pagamentos Previdência:**")
    salario_min = st.number_input("Valor do Salário Mínimo do Ano (ex: 1518 p/ 2025)", value=1518.0)
    inss_anual = (salario_min * 0.05) * 12
    st.caption(f"Valor estimado do INSS pago nas Guias DAS (5% de {salario_min} x 12m) = **R$ {inss_anual:,.2f}**. Esse valor constará no Relatório.")

with col2:
    st.subheader("Resultados e Fichas IRPF")
    if st.button("Calcular Lucro", type="primary"):
        if receita_bruta == 0:
             st.warning("Insira uma Receita Bruta maior que zero.")
        else:
             resultado = processar_calculo_mei(receita_bruta, despesas, ramo, receita_comercio, receita_servico)
             
             lucro = resultado['lucro_total']
             isento = resultado['parcela_isenta']
             tributavel = resultado['parcela_tributavel']
             
             st.metric("Lucro Evidenciado (Receita - Despesas)", f"R$ {lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             
             st.success(f"**Parcela Isenta:** R$ {isento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             st.info(f"👉 **Lançar em:** Ficha 'Rendimentos Isentos e Não Tributáveis' - Cód. 13 (Rendimento de sócio ou titular de microempresa...)")
             
             st.warning(f"**Parcela Tributável:** R$ {tributavel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             st.info(f"👉 **Lançar em:** Ficha 'Rendimentos Tributáveis Recebidos de Pessoa Jurídica' - Informar o CNPJ do seu próprio MEI.")
             
             try:
                 pdf_data = gerar_pdf_mei(cnpj_input if 'cnpj_input' in locals() else '', razao_social, 2025, receita_bruta, despesas, lucro, isento, tributavel, inss_anual)
                 st.download_button(
                     label="📄 Baixar Informe de Rendimentos (PDF)",
                     data=pdf_data,
                     file_name="informe_rendimentos_mei.pdf",
                     mime="application/pdf",
                     type="secondary"
                 )
             except Exception as e:
                 st.error(f"Erro ao gerar PDF: {e}")
