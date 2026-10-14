#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cruza planilha zonal JP (TRE-PB) com VOTACAO_SECAO do TSE (PB). Ver leiame.pdf."""

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
SHEET_CONSOLIDADO = "Consolidado_por_totais"
CD_MUNICIPIO_JP = "20516"
OUTPUT_CSV_NAME = "votacao_secao_2026_JP_zonal_detalhado.csv"
REPORT_NAME = "relatorio_mapeamento.txt"

INT_COLS_CSV = [
    "ANO_ELEICAO",
    "CD_TIPO_ELEICAO",
    "NR_TURNO",
    "CD_ELEICAO",
    "CD_MUNICIPIO",
    "NR_ZONA",
    "NR_SECAO",
    "CD_CARGO",
    "NR_VOTAVEL",
    "QT_VOTOS",
    "NR_LOCAL_VOTACAO",
    "SQ_CANDIDATO",
]


def _digits_to_int(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = re.sub(r"\D", "", str(value))
    return int(s) if s else None


def carregar_lookup_zonal(xlsx_path: Path) -> tuple[pd.DataFrame, dict]:
    """Normaliza aba Analitico_por_escola e explode SECOES por (zona, secao)."""
    raw = pd.read_excel(xlsx_path, sheet_name=SHEET_ANALITICO, dtype=str)
    required = {
        "COLEGIO",
        "ENDERECO",
        "BAIRRO",
        "COD_COLEGIO",
        "ZONA",
        "SECOES",
        "QTD_ELEITORES",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Colunas ausentes na planilha zonal: {sorted(missing)}")

    rows: list[dict] = []
    for _, row in raw.iterrows():
        zona = _digits_to_int(row["ZONA"])
        cod = _digits_to_int(row["COD_COLEGIO"])
        qtd = _digits_to_int(row["QTD_ELEITORES"])
        secoes_raw = str(row["SECOES"] or "")
        for part in secoes_raw.split(","):
            sec = _digits_to_int(part.strip())
            if zona is None or sec is None or cod is None:
                continue
            rows.append(
                {
                    "NR_ZONA": zona,
                    "NR_SECAO": sec,
                    "JP_COLEGIO": row["COLEGIO"],
                    "JP_ENDERECO": row["ENDERECO"],
                    "JP_BAIRRO": row["BAIRRO"],
                    "JP_COD_COLEGIO": cod,
                    "JP_QTD_ELEITORES_COLEGIO": qtd,
                }
            )

    lookup = pd.DataFrame(rows)
    if lookup.empty:
        raise ValueError("Nenhuma secao encontrada na planilha zonal.")

    dupes = lookup.duplicated(subset=["NR_ZONA", "NR_SECAO"], keep=False)
    if dupes.any():
        n = int(dupes.sum())
        raise ValueError(
            f"Chave (NR_ZONA, NR_SECAO) duplicada na planilha zonal ({n} linhas)."
        )

    consolidado = pd.read_excel(xlsx_path, sheet_name=SHEET_CONSOLIDADO, header=None)
    meta: dict = {"total_eleitores_planilha": None}
    for i in range(len(consolidado)):
        label = str(consolidado.iloc[i, 0]).strip()
        if label == "Total_eleitores" and consolidado.shape[1] > 1:
            meta["total_eleitores_planilha"] = _digits_to_int(consolidado.iloc[i, 1])

    por_colegio = (
        raw.assign(JP_COD_COLEGIO=raw["COD_COLEGIO"].map(_digits_to_int))
        .groupby("JP_COD_COLEGIO", dropna=True)["QTD_ELEITORES"]
        .apply(lambda s: sum(_digits_to_int(x) or 0 for x in s))
        .sum()
    )
    meta["soma_qtd_eleitores_analitico"] = int(por_colegio)

    return lookup, meta


def carregar_votacao_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin-1",
        dtype=str,
        na_values=["#NULO", "#NE"],
        keep_default_na=False,
    )
    for col in INT_COLS_CSV:
        if col not in df.columns:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col].isin([-1, -3]), col] = pd.NA

    mask = (
        (df["SG_UF"] == "PB")
        & (df["NR_TURNO"] == 1)
        & (df["CD_MUNICIPIO"].astype(str) == CD_MUNICIPIO_JP)
    )
    return df.loc[mask].copy()


def mapear(votacao: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    merged = votacao.merge(lookup, on=["NR_ZONA", "NR_SECAO"], how="inner")
    merged["LOCAL_DIVERGENTE"] = merged["NR_LOCAL_VOTACAO"] != merged["JP_COD_COLEGIO"]
    return merged


def escrever_relatorio(
    path: Path,
    lookup: pd.DataFrame,
    votacao_jp: pd.DataFrame,
    resultado: pd.DataFrame,
    meta: dict,
) -> None:
    keys_lookup = set(zip(lookup["NR_ZONA"], lookup["NR_SECAO"]))
    keys_csv = set(
        zip(
            votacao_jp["NR_ZONA"].dropna().astype(int),
            votacao_jp["NR_SECAO"].dropna().astype(int),
        )
    )
    keys_result = set(
        zip(
            resultado["NR_ZONA"].dropna().astype(int),
            resultado["NR_SECAO"].dropna().astype(int),
        )
    )
    sem_csv = sorted(keys_lookup - keys_csv)
    sem_lookup = sorted(keys_csv - keys_lookup)

    lines = [
        "Relatorio de mapeamento - Joao Pessoa (zonal x TSE VOTACAO_SECAO)",
        "=" * 60,
        f"Secoes na planilha zonal: {len(keys_lookup)}",
        f"Secoes JP (turno 1) no CSV TSE: {len(keys_csv)}",
        f"Secoes apos inner join: {len(keys_result)}",
        f"Linhas exportadas: {len(resultado)}",
        f"Linhas com LOCAL_DIVERGENTE=True: {int(resultado['LOCAL_DIVERGENTE'].sum())}",
        "",
        "Validacao eleitores (planilha):",
        f"  Total_eleitores (aba consolidado): {meta.get('total_eleitores_planilha')}",
        f"  Soma QTD_ELEITORES (aba analitico): {meta.get('soma_qtd_eleitores_analitico')}",
        "",
    ]
    if sem_csv:
        lines.append(f"Secoes no Excel sem votacao no CSV ({len(sem_csv)}):")
        for z, s in sem_csv[:20]:
            lines.append(f"  zona={z} secao={s}")
        if len(sem_csv) > 20:
            lines.append(f"  ... e mais {len(sem_csv) - 20}")
        lines.append("")
    if sem_lookup:
        lines.append(
            f"(Informativo) Secoes JP no CSV fora do recorte zonal: {len(sem_lookup)}"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mapeia VOTACAO_SECAO PB ao recorte zonal JP.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.saida.mkdir(parents=True, exist_ok=True)

    lookup, meta = carregar_lookup_zonal(args.xlsx)
    votacao_jp = carregar_votacao_csv(args.csv)
    resultado = mapear(votacao_jp, lookup)

    out_csv = args.saida / OUTPUT_CSV_NAME
    resultado.to_csv(out_csv, index=False, encoding="utf-8-sig", sep=";")

    report_path = args.saida / REPORT_NAME
    escrever_relatorio(report_path, lookup, votacao_jp, resultado, meta)

    print(f"Arquivo gerado: {out_csv}")
    print(f"Relatorio: {report_path}")
    print(f"Linhas: {len(resultado)} | Secoes: {resultado[['NR_ZONA', 'NR_SECAO']].drop_duplicates().shape[0]}")


if __name__ == "__main__":
    main()
