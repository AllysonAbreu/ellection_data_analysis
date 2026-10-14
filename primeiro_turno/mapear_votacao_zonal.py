#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cruza planilha zonal (Excel) com VOTACAO_SECAO (CSV TSE) via Zona e Código do Colégio/Local de Votação."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "votacao_secao_2026_PB.csv"
DEFAULT_XLSX = BASE_DIR / "dados_primeiro_turno_2026_jp_zonal.xlsx"
DEFAULT_OUT = BASE_DIR / "saida"
SHEET_ANALITICO = "Analitico_por_escola"
CD_MUNICIPIO_JP = "20516"
OUTPUT_CSV_NAME = "votacao_secao_2026_JP_zonal_detalhado.csv"


def _digits_to_int(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = re.sub(r"\D", "", str(value))
    return int(s) if s else None


def carregar_lookup_excel(xlsx_path: Path) -> pd.DataFrame:
    """Carrega dados do Excel e prepara chave (ZONA, COD_COLEGIO)."""
    raw = pd.read_excel(xlsx_path, sheet_name=SHEET_ANALITICO, dtype=str)
    
    # Validação de colunas esperadas no Excel
    expected = {"COLEGIO", "BAIRRO", "SECOES", "COD_COLEGIO", "ZONA"}
    missing = expected - set(raw.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no Excel: {sorted(missing)}")

    raw["NR_ZONA"] = raw["ZONA"].apply(_digits_to_int)
    raw["NR_LOCAL_VOTACAO"] = raw["COD_COLEGIO"].apply(_digits_to_int)

    # Mantém metadados do Excel para o cruzamento
    lookup = raw[[
        "NR_ZONA", 
        "NR_LOCAL_VOTACAO", 
        "COLEGIO", 
        "BAIRRO", 
        "SECOES"
    ]].drop_duplicates()

    return lookup


def carregar_votacao_csv(csv_path: Path) -> pd.DataFrame:
    """Carrega dados do CSV do TSE (filtrando João Pessoa, 1º turno)."""
    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin-1",
        dtype=str,
        na_values=["#NULO", "#NE"],
        keep_default_na=False,
    )

    df["NR_ZONA"] = pd.to_numeric(df["NR_ZONA"], errors="coerce")
    df["NR_LOCAL_VOTACAO"] = pd.to_numeric(df["NR_LOCAL_VOTACAO"], errors="coerce")
    df["QT_VOTOS"] = pd.to_numeric(df["QT_VOTOS"], errors="coerce").fillna(0)

    mask = (
        (df["SG_UF"] == "PB")
        & (df["NR_TURNO"].astype(str) == "1")
        & (df["CD_MUNICIPIO"].astype(str) == CD_MUNICIPIO_JP)
    )
    return df.loc[mask].copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.saida.mkdir(parents=True, exist_ok=True)

    lookup_excel = carregar_lookup_excel(args.xlsx)
    votacao_csv = carregar_votacao_csv(args.csv)

    # Cruzamento pelas chaves ZONA e LOCAL DE VOTAÇÃO
    resultado = votacao_csv.merge(
        lookup_excel, 
        on=["NR_ZONA", "NR_LOCAL_VOTACAO"], 
        how="inner"
    )

    out_csv = args.saida / OUTPUT_CSV_NAME
    resultado.to_csv(out_csv, index=False, encoding="utf-8-sig", sep=";")
    print(f"Mapeamento concluído! Linhas geradas: {len(resultado)} em '{out_csv}'")


if __name__ == "__main__":
    main()