"""Visualização Streamlit — votação por seção (recorte zonal João Pessoa)."""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "saida" / "votacao_secao_2026_JP_zonal_detalhado.csv"
TRE_FONTES = "https://apps.tre-pb.jus.br/logistica-consultas/locais-votacao"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)


def main() -> None:
    st.set_page_config(page_title="Votação JP — recorte zonal", layout="wide")
    st.title("Votação por seção — João Pessoa (recorte zonal)")
    st.caption(
        "Dados TSE (VOTACAO_SECAO) enriquecidos com bairro/colégio da planilha zonal. "
        f"Referência de locais: [TRE-PB]({TRE_FONTES})."
    )

    if not DATA_PATH.is_file():
        st.error(
            f"Arquivo não encontrado: `{DATA_PATH}`. "
            "Execute `python mapear_votacao_zonal.py` antes de abrir o app."
        )
        st.stop()

    df = load_data(DATA_PATH)

    st.sidebar.header("Filtros")
    bairros = sorted(df["JP_BAIRRO"].dropna().unique())
    cargos = sorted(df["DS_CARGO"].dropna().unique())
    sel_bairro = st.sidebar.multiselect("Bairro (JP)", bairros, default=[])
    sel_cargo = st.sidebar.multiselect("Cargo", cargos, default=[])
    busca = st.sidebar.text_input("Buscar candidato/votável (nome)", "")

    filtered = df.copy()
    if sel_bairro:
        filtered = filtered[filtered["JP_BAIRRO"].isin(sel_bairro)]
    if sel_cargo:
        filtered = filtered[filtered["DS_CARGO"].isin(sel_cargo)]
    if busca.strip():
        mask = filtered["NM_VOTAVEL"].astype(str).str.contains(
            busca.strip(), case=False, na=False
        )
        filtered = filtered[mask]

    qt = pd.to_numeric(filtered["QT_VOTOS"], errors="coerce").fillna(0)
    n_sec = filtered[["NR_ZONA", "NR_SECAO"]].drop_duplicates().shape[0]
    n_col = filtered["JP_COD_COLEGIO"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de votos (filtro)", f"{int(qt.sum()):,}".replace(",", "."))
    c2.metric("Linhas", f"{len(filtered):,}".replace(",", "."))
    c3.metric("Seções", n_sec)
    c4.metric("Colégios (JP)", n_col)

    if "LOCAL_DIVERGENTE" in filtered.columns:
        n_div = int(filtered["LOCAL_DIVERGENTE"].sum())
        if n_div:
            st.warning(
                f"{n_div} linha(s) com local TSE diferente do código na planilha zonal "
                "(coluna `LOCAL_DIVERGENTE`)."
            )

    display_cols = [
        "JP_BAIRRO",
        "JP_COLEGIO",
        "NR_ZONA",
        "NR_SECAO",
        "DS_CARGO",
        "NM_VOTAVEL",
        "QT_VOTOS",
        "NR_LOCAL_VOTACAO",
        "JP_COD_COLEGIO",
        "LOCAL_DIVERGENTE",
        "NM_LOCAL_VOTACAO",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    st.subheader("Detalhamento")
    st.dataframe(filtered[display_cols], use_container_width=True, height=480)

    st.download_button(
        "Baixar CSV filtrado",
        data=filtered.to_csv(index=False, sep=";", encoding="utf-8-sig"),
        file_name="votacao_jp_zonal_filtrado.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
