from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "saida" / "votacao_secao_2026_JP_zonal_detalhado.csv"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)
    df["QT_VOTOS"] = pd.to_numeric(df["QT_VOTOS"], errors="coerce").fillna(0)
    
    # Extrai a legenda do partido (2 primeiros dígitos)
    df["NR_LEGENDA"] = df["NR_VOTAVEL"].astype(str).str.extract(r"^(\d{2})")
    
    # Identificador único de seção eleitoral
    df["CHAVE_SECAO"] = (
        df["NR_ZONA"].astype(str) + "_" + df["NR_SECAO"].astype(str)
    )
    return df


def main() -> None:
    st.set_page_config(page_title="Painel de Votação — João Pessoa", layout="wide")
    st.title("🗳️ Painel de Análise Eleitoral por Seção — João Pessoa")

    if not DATA_PATH.is_file():
        st.error(f"Arquivo não encontrado em `{DATA_PATH}`. Execute o script de mapeamento primeiro.")
        st.stop()

    df = load_data(DATA_PATH)

    st.sidebar.header("🔍 Filtros de Pesquisa")

    # 1. Filtro por Seções
    secoes_unicas = sorted(df["NR_SECAO"].dropna().astype(int).unique())
    sel_secao = st.sidebar.multiselect("Seção Eleitoral (NR_SECAO)", secoes_unicas)

    # 2. Demais Filtros de Localidade e Candidatura
    sel_bairro = st.sidebar.multiselect("Bairro", sorted(df["BAIRRO"].dropna().astype(str).unique()))
    sel_colegio = st.sidebar.multiselect("Local / Colégio", sorted(df["COLEGIO"].dropna().astype(str).unique()))
    cargos_disponiveis = sorted(df["DS_CARGO"].dropna().astype(str).unique())
    sel_cargo = st.sidebar.multiselect("Cargo", cargos_disponiveis)
    sel_legenda = st.sidebar.multiselect("Legenda do Partido (2 dígitos)", sorted(df["NR_LEGENDA"].dropna().unique()))
    busca_nome = st.sidebar.text_input("Nome do Candidato / Votável", "")

    # Aplicação dinâmica dos filtros
    filtered = df.copy()
    if sel_secao:
        filtered = filtered[filtered["NR_SECAO"].isin(sel_secao)]
    if sel_bairro:
        filtered = filtered[filtered["BAIRRO"].isin(sel_bairro)]
    if sel_colegio:
        filtered = filtered[filtered["COLEGIO"].isin(sel_colegio)]
    if sel_cargo:
        filtered = filtered[filtered["DS_CARGO"].isin(sel_cargo)]
    if sel_legenda:
        filtered = filtered[filtered["NR_LEGENDA"].isin(sel_legenda)]
    if busca_nome.strip():
        filtered = filtered[filtered["NM_VOTAVEL"].astype(str).str.contains(busca_nome.strip(), case=False, na=False)]

    # --- SESSÃO CONSOLIDADA BASEADA NAS SEÇÕES FILTRADAS ---
    st.subheader("📊 Estatísticas Consolidadas (Base: Seção Eleitoral)")

    total_votos_filtrados = filtered["QT_VOTOS"].sum()
    votos_brancos = filtered[filtered["NR_VOTAVEL"].astype(str) == "95"]["QT_VOTOS"].sum()
    votos_nulos = filtered[filtered["NR_VOTAVEL"].astype(str) == "96"]["QT_VOTOS"].sum()
    votos_validos = total_votos_filtrados - (votos_brancos + votos_nulos)
    total_secoes_ativas = filtered["CHAVE_SECAO"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Seções Mapeadas", total_secoes_ativas)
    c2.metric("Total de Votos na Seleção", f"{int(total_votos_filtrados):,}".replace(",", "."))
    c3.metric("Votos Válidos", f"{int(votos_validos):,}".replace(",", "."))
    c4.metric("Votos Brancos", f"{int(votos_brancos):,}".replace(",", "."))
    c5.metric("Votos Nulos", f"{int(votos_nulos):,}".replace(",", "."))

    st.markdown("---")

    # --- GRÁFICOS INTERATIVOS ---
    st.subheader("📈 Desempenho e Distribuição")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Ranking de Candidatos / Votáveis mais votados na seleção
        candidatos_df = filtered[~filtered["NR_VOTAVEL"].astype(str).isin(["95", "96"])]
        votos_cand = (
            candidatos_df.groupby("NM_VOTAVEL")["QT_VOTOS"]
            .sum()
            .reset_index()
            .sort_values(by="QT_VOTOS", ascending=False)
            .head(10)
        )
        fig_cand = px.bar(
            votos_cand,
            x="QT_VOTOS",
            y="NM_VOTAVEL",
            orientation="h",
            title="Top Candidatos Mais Votados",
            labels={"QT_VOTOS": "Total de Votos", "NM_VOTAVEL": "Candidato"},
            color="QT_VOTOS",
            color_continuous_scale="Blues",
        )
        fig_cand.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_cand, use_container_width=True)

    with col_chart2:
        # Gráfico de Pizza de Distribuição de Votos por Bairro
        votos_bairro = (
            filtered.groupby("BAIRRO")["QT_VOTOS"]
            .sum()
            .reset_index()
            .sort_values(by="QT_VOTOS", ascending=False)
        )
        fig_bairro = px.pie(
            votos_bairro,
            names="BAIRRO",
            values="QT_VOTOS",
            title="Distribuição dos Votos por Bairro",
            hole=0.4,
        )
        st.plotly_chart(fig_bairro, use_container_width=True)

    st.markdown("---")

    # --- TABELA ANALÍTICA ---
    st.subheader("📋 Detalhamento Analítico por Seção")

    renomear_colunas = {
        "NR_ZONA": "Zona Eleitoral",
        "NR_SECAO": "Seção Eleitoral",
        "DS_CARGO": "Cargo",
        "NR_LEGENDA": "Legenda",
        "NR_VOTAVEL": "Nº Votável",
        "NM_VOTAVEL": "Nome Votável / Candidato",
        "QT_VOTOS": "Qtd Votos",
        "COLEGIO": "Local de Votação",
        "BAIRRO": "Bairro",
    }

    cols_exibir = [c for c in renomear_colunas.keys() if c in filtered.columns]
    df_exibicao = filtered[cols_exibir].rename(columns=renomear_colunas)

    st.dataframe(df_exibicao, use_container_width=True, height=400)


if __name__ == "__main__":
    main()