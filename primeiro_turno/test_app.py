import shutil
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import app as painel


def _gravar_csv_painel(caminho):
    pd.DataFrame(
        [
            {
                "NR_ZONA": 10,
                "NR_SECAO": 1,
                "DS_CARGO": "Presidente",
                "NR_VOTAVEL": "22",
                "NM_VOTAVEL": "PRESIDENTE A",
                "QT_VOTOS": "8",
                "QT_VOTOS_PRESIDENTE": "8",
                "COLEGIO": "Escola A",
                "BAIRRO": "Bairro Azul",
            },
            {
                "NR_ZONA": 10,
                "NR_SECAO": 1,
                "DS_CARGO": "Deputado Estadual",
                "NR_VOTAVEL": "13",
                "NM_VOTAVEL": "CANDIDATO B",
                "QT_VOTOS": "5",
                "QT_VOTOS_PRESIDENTE": "8",
                "COLEGIO": "Escola A",
                "BAIRRO": "Bairro Azul",
            },
        ]
    ).to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")


def test_load_data_converte_votos_e_cria_chaves(tmp_path):
    caminho = tmp_path / "votacao.csv"
    pd.DataFrame(
        [
            {
                "NR_ZONA": 10,
                "NR_SECAO": 1,
                "NR_VOTAVEL": "22123",
                "QT_VOTOS": "inválido",
                "QT_VOTOS_PRESIDENTE": "8",
            },
            {
                "NR_ZONA": 10,
                "NR_SECAO": 2,
                "NR_VOTAVEL": "13",
                "QT_VOTOS": "5",
                "QT_VOTOS_PRESIDENTE": "",
            },
        ]
    ).to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    painel.load_data.clear()

    resultado = painel.load_data(caminho)

    assert resultado["QT_VOTOS"].tolist() == [0, 5]
    assert resultado["QT_VOTOS_PRESIDENTE"].tolist() == [8, 0]
    assert resultado["NR_LEGENDA"].tolist() == ["22", "13"]
    assert resultado["CHAVE_SECAO"].tolist() == ["10_1", "10_2"]


def test_main_renderiza_painel_e_aplica_filtro_de_cargo(tmp_path):
    pasta_app = tmp_path / "painel"
    pasta_saida = pasta_app / "saida"
    pasta_saida.mkdir(parents=True)
    caminho_app = pasta_app / "app.py"
    shutil.copyfile(Path(painel.__file__), caminho_app)
    caminho = pasta_saida / "votacao_secao_2026_JP_zonal_detalhado.csv"
    _gravar_csv_painel(caminho)

    resultado = AppTest.from_file(str(caminho_app)).run()

    assert not resultado.exception
    filtro_cargo = next(
        widget for widget in resultado.multiselect if widget.label == "Cargo"
    )
    filtro_cargo.set_value(["Deputado Estadual"]).run()

    assert not resultado.exception
    metrica_votos = next(
        metrica
        for metrica in resultado.metric
        if metrica.label == "Total de Votos (Filtro)"
    )
    assert metrica_votos.value == "5"