import pandas as pd
import pytest

from mapear_votacao_zonal import (
    _digits_to_int,
    adicionar_total_presidente,
    carregar_lookup_excel,
    carregar_votacao_csv,
    carregar_votacao_presidente,
    main,
)


def _linha_tse(
    cargo="Deputado Estadual",
    votos="5",
    zona="10",
    local="100",
    secao="1",
    municipio="20516",
    uf="PB",
    turno="1",
    nome="CANDIDATO",
    votavel="13",
):
    return {
        "SG_UF": uf,
        "NR_TURNO": turno,
        "CD_MUNICIPIO": municipio,
        "NR_ZONA": zona,
        "NR_LOCAL_VOTACAO": local,
        "NR_SECAO": secao,
        "DS_CARGO": cargo,
        "NR_VOTAVEL": votavel,
        "NM_VOTAVEL": nome,
        "QT_VOTOS": votos,
    }


def _gravar_csv_tse(caminho, linhas):
    pd.DataFrame(linhas).to_csv(
        caminho, sep=";", index=False, encoding="latin-1"
    )


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("Zona 70", 70),
        ("00100", 100),
        ("sem número", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_digits_to_int_normaliza_valores(valor, esperado):
    assert _digits_to_int(valor) == esperado


def test_carregar_lookup_excel_normaliza_chaves_e_remove_duplicatas(tmp_path):
    caminho = tmp_path / "lookup.xlsx"
    dados = pd.DataFrame(
        [
            {
                "ZONA": "Zona 10",
                "COD_COLEGIO": "Local 100",
                "COLEGIO": "Escola A",
                "BAIRRO": "Bairro Azul",
                "SECOES": "1, 2",
            },
            {
                "ZONA": "Zona 10",
                "COD_COLEGIO": "Local 100",
                "COLEGIO": "Escola A",
                "BAIRRO": "Bairro Azul",
                "SECOES": "1, 2",
            },
        ]
    )
    dados.to_excel(caminho, sheet_name="Analitico_por_escola", index=False)

    resultado = carregar_lookup_excel(caminho)

    assert resultado.to_dict("records") == [
        {
            "NR_ZONA": 10,
            "NR_LOCAL_VOTACAO": 100,
            "COLEGIO": "Escola A",
            "BAIRRO": "Bairro Azul",
            "SECOES": "1, 2",
        }
    ]


def test_carregar_lookup_excel_rejeita_colunas_ausentes(tmp_path):
    caminho = tmp_path / "lookup_incompleto.xlsx"
    pd.DataFrame({"COLEGIO": ["Escola A"]}).to_excel(
        caminho, sheet_name="Analitico_por_escola", index=False
    )

    with pytest.raises(ValueError, match="Colunas ausentes no Excel"):
        carregar_lookup_excel(caminho)


def test_carregar_votacao_csv_filtra_municipio_uf_e_turno(tmp_path):
    caminho = tmp_path / "votacao_pb.csv"
    _gravar_csv_tse(
        caminho,
        [
            _linha_tse(votos="#NULO"),
            _linha_tse(municipio="99999"),
            _linha_tse(uf="PE"),
            _linha_tse(turno="2"),
        ],
    )

    resultado = carregar_votacao_csv(caminho)

    assert len(resultado) == 1
    assert resultado.iloc[0]["QT_VOTOS"] == 0
    assert resultado.iloc[0]["NR_SECAO"] == 1


def test_carregar_votacao_presidente_filtra_cargo_e_recorte(tmp_path):
    caminho = tmp_path / "votacao_br.csv"
    _gravar_csv_tse(
        caminho,
        [
            _linha_tse(cargo=" presidente ", nome="PRESIDENTE A", votos="12"),
            _linha_tse(cargo="Deputado Estadual"),
            _linha_tse(cargo="Presidente", turno="2"),
            _linha_tse(cargo="Presidente", municipio="99999"),
        ],
    )

    resultado = carregar_votacao_presidente(caminho)

    assert resultado["DS_CARGO"].tolist() == [" presidente "]
    assert resultado["NM_VOTAVEL"].tolist() == ["PRESIDENTE A"]
    assert resultado["QT_VOTOS"].tolist() == [12]


def test_adicionar_total_presidente_gera_coluna_e_soma_por_local():
    votacao = pd.DataFrame(
        [
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 1,
                "DS_CARGO": "Deputado Estadual",
                "NR_VOTAVEL": "13",
                "NM_VOTAVEL": "CANDIDATO A",
                "QT_VOTOS": 8,
            },
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 1,
                "DS_CARGO": "Deputado Estadual",
                "NR_VOTAVEL": "17",
                "NM_VOTAVEL": "CANDIDATO B",
                "QT_VOTOS": 2,
            },
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 2,
                "DS_CARGO": "Deputado Estadual",
                "NR_VOTAVEL": "13",
                "NM_VOTAVEL": "CANDIDATO A",
                "QT_VOTOS": 5,
            },
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 3,
                "DS_CARGO": "Deputado Estadual",
                "NR_VOTAVEL": "13",
                "NM_VOTAVEL": "CANDIDATO A",
                "QT_VOTOS": 1,
            },
        ]
    )

    presidente = pd.DataFrame(
        [
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 1,
                "DS_CARGO": "Presidente",
                "NR_VOTAVEL": "22",
                "NM_VOTAVEL": "PRESIDENTE X",
                "QT_VOTOS": 15,
            },
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 1,
                "DS_CARGO": "Presidente",
                "NR_VOTAVEL": "44",
                "NM_VOTAVEL": "PRESIDENTE Y",
                "QT_VOTOS": 10,
            },
            {
                "NR_ZONA": 10,
                "NR_LOCAL_VOTACAO": 100,
                "NR_SECAO": 2,
                "DS_CARGO": "Presidente",
                "NR_VOTAVEL": "66",
                "NM_VOTAVEL": "PRESIDENTE Z",
                "QT_VOTOS": 7,
            },
        ]
    )

    resultado = adicionar_total_presidente(votacao, presidente)

    assert "QT_VOTOS_PRESIDENTE" in resultado.columns
    total_por_secao = resultado.groupby("NR_SECAO")["QT_VOTOS_PRESIDENTE"].first().to_dict()
    assert total_por_secao == {1: 25, 2: 7, 3: 0}


@pytest.mark.parametrize(
    "presidente",
    [
        None,
        pd.DataFrame(),
        pd.DataFrame({"NR_ZONA": [10], "NR_LOCAL_VOTACAO": [100]}),
    ],
)
def test_adicionar_total_presidente_sem_chaves_completas_preenche_zero(presidente):
    votacao = pd.DataFrame(
        [{"NR_ZONA": 10, "NR_LOCAL_VOTACAO": 100, "NR_SECAO": 1}]
    )

    resultado = adicionar_total_presidente(votacao, presidente)

    assert resultado["QT_VOTOS_PRESIDENTE"].tolist() == [0]


def test_main_gera_csv_com_votos_presidenciais_e_total_por_secao(
    tmp_path, monkeypatch, capsys
):
    caminho_pb = tmp_path / "votacao_pb.csv"
    caminho_br = tmp_path / "votacao_br.csv"
    caminho_excel = tmp_path / "lookup.xlsx"
    pasta_saida = tmp_path / "saida"

    _gravar_csv_tse(
        caminho_pb,
        [
            _linha_tse(votos="8", nome="CANDIDATO ESTADUAL"),
            _linha_tse(votos="30", municipio="99999"),
        ],
    )
    _gravar_csv_tse(
        caminho_br,
        [
            _linha_tse(
                cargo="Presidente", votos="15", nome="PRESIDENTE A", votavel="22"
            ),
            _linha_tse(
                cargo="Presidente", votos="10", nome="PRESIDENTE B", votavel="44"
            ),
            _linha_tse(cargo="Presidente", turno="2", votos="50"),
        ],
    )
    pd.DataFrame(
        [
            {
                "ZONA": "10",
                "COD_COLEGIO": "100",
                "COLEGIO": "Escola A",
                "BAIRRO": "Bairro Azul",
                "SECOES": "1",
            }
        ]
    ).to_excel(caminho_excel, sheet_name="Analitico_por_escola", index=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "mapear_votacao_zonal.py",
            "--csv",
            str(caminho_pb),
            "--csv-presidente",
            str(caminho_br),
            "--xlsx",
            str(caminho_excel),
            "--saida",
            str(pasta_saida),
        ],
    )

    main()

    caminho_saida = pasta_saida / "votacao_secao_2026_JP_zonal_detalhado.csv"
    resultado = pd.read_csv(caminho_saida, sep=";", encoding="utf-8-sig")
    linhas_presidente = resultado[resultado["DS_CARGO"] == "Presidente"]

    assert len(resultado) == 3
    assert set(linhas_presidente["NM_VOTAVEL"]) == {"PRESIDENTE A", "PRESIDENTE B"}
    assert linhas_presidente["QT_VOTOS"].sum() == 25
    assert resultado["QT_VOTOS_PRESIDENTE"].eq(25).all()
    assert resultado["COLEGIO"].eq("Escola A").all()
    assert "Linhas geradas: 3" in capsys.readouterr().out
