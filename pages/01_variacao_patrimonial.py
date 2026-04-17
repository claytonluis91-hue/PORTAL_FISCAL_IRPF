import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.regras_patrimonio import calcular_variacao_patrimonial
from utils.api_client import gerar_insights_patrimonio_gemini

st.set_page_config(page_title="Variação Patrimonial", page_icon="⚖️", layout="wide")

st.title("⚖️ Variação Patrimonial e Auditoria")
st.markdown("Audite seu aumento de bens em relação à renda gerada. Receba ajuda da **Inteligência Artificial (Gemini)** se houver saldo insuficiente.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Evolução de Bens (Patrimônio)")
    st.info("Valores totais declarados na ficha de *Bens e Direitos* subtraindo *Dívidas*.")
    patrimonio_inicial = st.number_input("Patrimônio em 31/12 do Ano Anterior (R$)", min_value=0.0, step=1000.0)
    patrimonio_final = st.number_input("Patrimônio em 31/12 do Ano Atual (R$)", min_value=0.0, step=1000.0)
    
    st.subheader("2. Composição de Caixa (Renda vs Despesas)")
    rendimentos = st.number_input("Total de Rendimentos (Tributáveis + Isentos + Exclusivos) (R$)", min_value=0.0, step=1000.0)
    despesas = st.number_input("Total de Despesas / Pagamentos Efetuados (R$)", min_value=0.0, step=1000.0)

with col2:
    st.subheader("📊 Resultado da Auditoria")
    if st.button("Calcular Consistência", type="primary"):
        resultado = calcular_variacao_patrimonial(patrimonio_inicial, patrimonio_final, rendimentos, despesas)
        
        aumento = resultado['aumento_patrimonial']
        disp = resultado['disponibilidade']
        dif = resultado['diferenca']
        
        st.metric("Aumento Patrimonial no Ano", f"R$ {aumento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Caixa Disponível para Justificar (Renda Líquida)", f"R$ {disp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("---")
        if resultado['a_descoberto']:
            st.error(f"⚠️ **Atenção:** Variação Patrimonial a Descoberto em **R$ {dif:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            st.warning("O aumento da sua riqueza foi MAIOR do que o seu caixa justificável. Isso atrai a malha fina fiscal.")
            
            # Aqui acionamos a IA
            with st.spinner("🧠 Analisando possíveis erros com Inteligência Artificial (Gemini)..."):
                insights = gerar_insights_patrimonio_gemini(resultado)
                with st.expander("💡 Dicas do Auditor IA (Gemini)", expanded=True):
                    st.write(insights)
        else:
            if aumento <= disp:
                 sobra = disp - aumento
                 st.success(f"✅ Consistente! O caixa cobre a sua evolução de bens. Sobrou declarados R$ {sobra:,.2f} em caixa presumido.".replace(",", "X").replace(".", ",").replace("X", "."))

