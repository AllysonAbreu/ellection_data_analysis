import pandas as pd

from mapear_votacao_zonal import adicionar_total_presidente


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
                "NR_SECAO": 2,
                "DS_CARGO": "Presidente",
                "NR_VOTAVEL": "44",
                "NM_VOTAVEL": "PRESIDENTE Y",
                "QT_VOTOS": 7,
            },
        ]
    )

    resultado = adicionar_total_presidente(votacao, presidente)

    assert "QT_VOTOS_PRESIDENTE" in resultado.columns
    total_por_secao = resultado.groupby("NR_SECAO")["QT_VOTOS_PRESIDENTE"].first().to_dict()
    assert total_por_secao == {1: 25, 2: 7}
