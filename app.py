import streamlit as st

# Configuração global da página
st.set_page_config(
    page_title="Portal Fiscal IRPF",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("🏛️ Portal Fiscal IRPF")
    st.sidebar.markdown("Automatize suas declarações com segurança.")
    
    # Navegação usando a nova API do Streamlit
    pages = {
        "Auditoria e Checklists": [
            st.Page("pages/01_variacao_patrimonial.py", title="Variação Patrimonial", icon="⚖️"),
        ],
        "Cálculos Impostos": [
            st.Page("pages/02_calculo_mei.py", title="Cálculo MEI", icon="🏢"),
            st.Page("pages/03_posicao_investimentos.py", title="Posição de Investimentos", icon="📈"),
        ]
    }
    
    pg = st.navigation(pages)
    
    # Rodapé da sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 Portal Fiscal IRPF - Versão Limpa e Segura")
    
    pg.run()

if __name__ == "__main__":
    main()
