import streamlit as st
import sys
import os
import io
from fpdf import FPDF
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_patrimonio import calcular_variacao_patrimonial
from utils.api_client import gerar_insights_patrimonio_gemini

st.set_page_config(page_title="Variação Patrimonial", page_icon="⚖️", layout="wide")

def limpar_markdown(texto_md):
    """Remove caracteres markdown básicos para o PDF não bugar"""
    t = texto_md.replace("**", "").replace("__", "")
    t = t.replace("#", "").replace("*", "-")
    return t

def gerar_laudo_pdf(nome, cpf, bens_ant, div_ant, pl_ant, bens_atu, div_atu, pl_atu, 
                    r_trib, r_ise, r_exc, desp, rend_liquido, aumento, a_desc, dif, ia_text):
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cabeçalho
    pdf.set_font("helvetica", size=14, style="B")
    pdf.cell(0, 10, "PORTAL FISCAL IRPF - LAUDO DE ANÁLISE DE VARIAÇÃO PATRIMONIAL", ln=True, align="C")
    pdf.ln(5)
    
    # Dados Contribuinte
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, "1. Identificação do Contribuinte", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 7, f"Nome/Razão: {nome if nome else '____________________________________________'}", ln=True)
    pdf.cell(0, 7, f"CPF/CNPJ: {cpf if cpf else '__________________'}", ln=True)
    pdf.ln(3)
    
    # Patrimônio
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, "2. Evolução de Patrimônio", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 6, f"+ Total de Bens (31/12/2024): R$ {bens_ant:,.2f}", ln=True)
    pdf.cell(0, 6, f"- Total de Dívidas (31/12/2024): R$ {div_ant:,.2f}", ln=True)
    pdf.cell(0, 6, f"= Patrimônio Líquido 2024: R$ {pl_ant:,.2f}", ln=True)
    pdf.ln(2)
    pdf.cell(0, 6, f"+ Total de Bens (31/12/2025): R$ {bens_atu:,.2f}", ln=True)
    pdf.cell(0, 6, f"- Total de Dívidas (31/12/2025): R$ {div_atu:,.2f}", ln=True)
    pdf.cell(0, 6, f"= Patrimônio Líquido 2025: R$ {pl_atu:,.2f}", ln=True)
    pdf.ln(2)
    pdf.set_font("helvetica", size=11, style="B")
    pdf.cell(0, 6, f"-> Aumento Patrimonial Real no Ano: R$ {aumento:,.2f}", ln=True)
    pdf.ln(3)
    
    # Caixa
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, "3. Fluxo de Caixa Declarado (Composição)", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 6, f"+ Rendimentos Tributáveis: R$ {r_trib:,.2f}", ln=True)
    pdf.cell(0, 6, f"+ Rendimentos Isentos: R$ {r_ise:,.2f}", ln=True)
    pdf.cell(0, 6, f"+ Rendimentos Exclusivos/Definitivos: R$ {r_exc:,.2f}", ln=True)
    pdf.cell(0, 6, f"- Despesas Informadas: R$ {desp:,.2f}", ln=True)
    pdf.set_font("helvetica", size=11, style="B")
    pdf.cell(0, 6, f"-> Caixa Disponível para Justificar Acréscimos: R$ {rend_liquido:,.2f}", ln=True)
    pdf.ln(5)
    
    # Conclusão
    pdf.set_font("helvetica", size=12, style="B")
    pdf.cell(0, 8, "4. Parecer e Auditoria Automática", ln=True)
    pdf.set_font("helvetica", size=11, style="B")
    if a_desc:
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, f"ATENÇÃO Risco de Malha: Aumento Patrimonial a Descoberto de R$ {dif:,.2f}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, txt="Parecer IA para revisão pontual pelo Contador:\n" + limpar_markdown(ia_text))
    else:
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 8, f"CONSISTENTE: Folga Financeira Positiva de R$ {abs(dif):,.2f}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
    return bytes(pdf.output())

st.title("⚖️ Variação Patrimonial e Mapeamento")
st.markdown("Auditaria detalhada em nível contábil de contas analíticas.")
st.markdown("---")

st.subheader("1. Identificação")
col_cpf, col_nome = st.columns([1, 2])
with col_cpf:
    cpf = st.text_input("CPF do Contribuinte", max_chars=14, help="Apenas verificação visual no PDF.")
with col_nome:
    nome = st.text_input("Nome Próprio / Razão Social")

st.markdown("---")
st.subheader("2. Evolução de Patrimônio (31/12/24 -> 31/12/25)")

col_b_1, col_b_2 = st.columns(2)
with col_b_1:
    st.info("**Ano Anterior (2024)**")
    c1, c2 = st.columns(2)
    bens_ant = c1.number_input("Bens Base (R$)", min_value=0.0, step=1000.0, format="%.2f", key="ba")
    div_ant = c2.number_input("Dívidas/Ônus (R$)", min_value=0.0, step=1000.0, format="%.2f", key="da")
    pat_ant = bens_ant - div_ant
    st.caption(f"**PL 24: R$ {pat_ant:,.2f}**")

with col_b_2:
    st.success("**Ano Atual (2025)**")
    c3, c4 = st.columns(2)
    bens_atu = c3.number_input("Bens Adquiridos/Finais (R$)", min_value=0.0, step=1000.0, format="%.2f", key="bt")
    div_atu = c4.number_input("Dívidas Finais (R$)", min_value=0.0, step=1000.0, format="%.2f", key="dt")
    pat_atu = bens_atu - div_atu
    st.caption(f"**PL 25: R$ {pat_atu:,.2f}**")

st.markdown("---")
st.subheader("3. Composição de Caixa Disponível")
col_rc1, col_rc2, col_rc3 = st.columns(3)

with col_rc1:
    r_trib = st.number_input("Rendimento Tributável PF/PJ/Rural", min_value=0.0, step=1000.0, format="%.2f")
with col_rc2:
    r_ise = st.number_input("Rendimento Isento/Não Tribut.',", min_value=0.0, step=1000.0, format="%.2f")
with col_rc3:
    r_exc = st.number_input("Rendimento Tributação Exclusiva", min_value=0.0, step=1000.0, format="%.2f")

despesas = st.number_input("Total de Pagamentos Efetuados / IR Retido na Fonte / Despesas Livro-Caixa", min_value=0.0, step=1000.0, format="%.2f")

st.markdown("---")
st.subheader("📊 Resultado da Auditoria e Emissão do Laudo")

if st.button("Calcular e Chamar IA (se necessário)", type="primary"):
    total_rendimentos = r_trib + r_ise + r_exc
    
    resultado = calcular_variacao_patrimonial(pat_ant, pat_atu, total_rendimentos, despesas)
    
    aumento = resultado['aumento_patrimonial']
    disp = resultado['disponibilidade']
    dif = resultado['diferenca']
    a_desc = resultado['a_descoberto']
    
    c_res1, c_res2 = st.columns(2)
    c_res1.metric("Aumento Patrimonial no Ano", f"R$ {aumento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c_res2.metric("Caixa Disponível para Justificar (Líquido)", f"R$ {disp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("---")
    insights = ""
    
    if a_desc:
        st.error(f"⚠️ **Atenção:** Variação Patrimonial a Descoberto em **R$ {dif:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.warning("O aumento da riqueza do seu cliente foi MAIOR do que o caixa justificável! (Isso atrai a Malha Fina).")
        
        with st.spinner("🧠 Analisando possíveis erros com Inteligência Artificial (Gemini)..."):
            insights = gerar_insights_patrimonio_gemini(resultado)
            with st.expander("💡 Laudo do Auditor IA (Visão Gemini)", expanded=True):
                st.write(insights)
    else:
        sobra = disp - aumento
        st.success(f"✅ Consistente! O caixa cobre a sua evolução de bens. Sobrou declarados R$ {sobra:,.2f} em caixa presumido.".replace(",", "X").replace(".", ",").replace("X", "."))
        insights = "Contabilidade Saudável. Evolução limpa e compatível com o Faturamento gerado no livro caixa."
        
    try:
         pdf_data = gerar_laudo_pdf(nome, cpf, bens_ant, div_ant, pat_ant, bens_atu, div_atu, pat_atu,
                                    r_trib, r_ise, r_exc, despesas, disp, aumento, a_desc, dif, insights)
         
         st.download_button(
             label="📄 Baixar Laudo de Evolução em PDF (PDF)",
             data=pdf_data,
             file_name=f"laudo_patrimonial_{cpf.replace('.', '').replace('-', '') if cpf else 'limpo'}.pdf",
             mime="application/pdf",
             type="secondary"
         )
    except Exception as e:
         st.error(f"Erro ao gerar Laudo Arquivístico: {e}")

