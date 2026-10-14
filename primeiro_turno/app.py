from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "saida" / "votacao_secao_2026_JP_zonal_detalhado.csv"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)


def main() -> None:
    st.set_page_config(page_title="Painel de Votação — João Pessoa", layout="wide")
    st.title(" Análise de Votação por Zona e Local (João Pessoa)")

    if not DATA_PATH.is_file():
        st.error(f"Arquivo não encontrado em `{DATA_PATH}`. Execute primeiro o script de mapeamento.")
        st.stop()

    df = load_data(DATA_PATH)

    st.sidebar.header("Filtros de Pesquisa")

    # Filtros baseados em COLEGIO, BAIRRO e SECOES (provenientes do Excel/CSV)
    sel_bairro = st.sidebar.multiselect("Bairro", sorted(df["BAIRRO"].dropna().astype(str).unique()))
    sel_colegio = st.sidebar.multiselect("Colégio", sorted(df["COLEGIO"].dropna().astype(str).unique()))
    sel_secao = st.sidebar.multiselect("Seção / Agrupamento", sorted(df["SECOES"].dropna().astype(str).unique()))

    # Filtros baseados em DS_CARGO, NR_VOTAVEL e NM_VOTAVEL
    sel_cargo = st.sidebar.multiselect("Cargo (DS_CARGO)", sorted(df["DS_CARGO"].dropna().astype(str).unique()))
    sel_nr_votavel = st.sidebar.multiselect("Número Votável (NR_VOTAVEL)", sorted(df["NR_VOTAVEL"].dropna().astype(str).unique()))
    busca_nome = st.sidebar.text_input("Nome do Votável / Candidato (NM_VOTAVEL)", "")

    # Aplicação dos filtros no dataframe
    filtered = df.copy()
    if sel_bairro:
        filtered = filtered[filtered["BAIRRO"].isin(sel_bairro)]
    if sel_colegio:
        filtered = filtered[filtered["COLEGIO"].isin(sel_colegio)]
    if sel_secao:
        filtered = filtered[filtered["SECOES"].isin(sel_secao)]
    if sel_cargo:
        filtered = filtered[filtered["DS_CARGO"].isin(sel_cargo)]
    if sel_nr_votavel:
        filtered = filtered[filtered["NR_VOTAVEL"].astype(str).isin(sel_nr_votavel)]
    if busca_nome.strip():
        filtered = filtered[filtered["NM_VOTAVEL"].astype(str).str.contains(busca_nome.strip(), case=False, na=False)]

    # --- INFORMAÇÕES CONSOLIDADAS (Métricas Globais) ---
    st.subheader("📊 Visão Consolidada")
    col1, col2, col3, col4 = st.columns(4)
    
    total_votos = filtered["QT_VOTOS"].sum()
    total_colegios = filtered["COLEGIO"].nunique()
    total_bairros = filtered["BAIRRO"].nunique()
    total_candidatos = filtered["NM_VOTAVEL"].nunique()

    col1.metric("Total de Votos (Filtrados)", f"{int(total_votos):,}".replace(",", "."))
    col2.metric("Colégios Mapeados", total_colegios)
    col3.metric("Bairros Alcançados", total_bairros)
    col4.metric("Votáveis / Candidatos", total_candidatos)

    st.markdown("---")

    # --- DETALHAMENTO ANALÍTICO ---
    st.subheader("📋 Dados Analíticos")

    # Colunas principais a serem exibidas
    cols_destaque = ["DS_CARGO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS", "COLEGIO", "BAIRRO", "SECOES", "NR_ZONA", "NR_LOCAL_VOTACAO"]
    cols_existentes = [c for c in cols_destaque if c in filtered.columns]

    st.dataframe(filtered[cols_existentes], use_container_width=True, height=450)

    # Botão para exportação dos dados analisados
    st.download_button(
        label="📥 Baixar Dados Analíticos Filtrados (CSV)",
        data=filtered[cols_existentes].to_csv(index=False, sep=";", encoding="utf-8-sig"),
        file_name="dados_analiticos_filtrados.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()