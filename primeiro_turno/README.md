# Mapeamento votação por seção — João Pessoa (recorte zonal)

Cruzamento entre a planilha zonal de locais de votação (`dados_primeiro_turno_2026_jp_zonal.xlsx`) e o arquivo oficial do TSE `VOTACAO_SECAO` (`votacao_secao_2026_PB.csv`), seguindo o leiaute descrito em `leiame.pdf`.

## Pré-requisitos

- Python 3.10+
- Arquivos de entrada na pasta do projeto (não versionados por padrão por serem grandes):
  - `votacao_secao_2026_PB.csv`
  - `dados_primeiro_turno_2026_jp_zonal.xlsx`

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Gerar o CSV detalhado

```bash
python mapear_votacao_zonal.py
```

Opções:

```bash
python mapear_votacao_zonal.py --csv votacao_secao_2026_PB.csv --xlsx dados_primeiro_turno_2026_jp_zonal.xlsx --saida saida/
```

Saídas:

| Arquivo | Descrição |
|---------|-----------|
| `saida/votacao_secao_2026_JP_zonal_detalhado.csv` | Linhas TSE (João Pessoa, 1º turno) **somente** para seções presentes na planilha zonal |
| `saida/relatorio_mapeamento.txt` | Contagens, validação de eleitores e divergências de local |

### Chave de cruzamento

- **Join:** `NR_ZONA` + `NR_SECAO`
- **Filtros TSE:** `SG_UF=PB`, `NR_TURNO=1`, `CD_MUNICIPIO=20516` (João Pessoa)
- **Flag:** `LOCAL_DIVERGENTE` quando `NR_LOCAL_VOTACAO` (TSE) ≠ `JP_COD_COLEGIO` (planilha)

### Colunas adicionadas (prefixo `JP_`)

| Coluna | Origem |
|--------|--------|
| `JP_BAIRRO` | Bairro na planilha zonal |
| `JP_COLEGIO` | Nome do colégio na planilha |
| `JP_ENDERECO` | Endereço na planilha |
| `JP_COD_COLEGIO` | Código do local (`COD_COLEGIO`) |
| `JP_QTD_ELEITORES_COLEGIO` | Eleitores aptos no colégio (planilha) |
| `LOCAL_DIVERGENTE` | Booleano de consistência com o TSE |

Demais colunas seguem o dicionário `VOTACAO_SECAO` no `leiame.pdf` (`QT_VOTOS`, `DS_CARGO`, `NM_VOTAVEL`, etc.).

### Limitação

A planilha zonal cobre **331 seções** (38 colégios, 114.633 eleitores), não todo o município (~1.714 seções no TSE). O recorte reflete o mapeamento da campanha, não a totalidade de João Pessoa.

Fonte dos locais (aba `Fonte` do Excel): [TRE-PB — locais de votação](https://apps.tre-pb.jus.br/logistica-consultas/locais-votacao).

## App Streamlit

Com o CSV gerado em `saida/`:

```bash
streamlit run app.py
```

Filtros por bairro, cargo e candidato; métricas de votos e download do recorte filtrado.

## Deploy no Streamlit Community Cloud

1. Envie este repositório ao GitHub (inclua `saida/votacao_secao_2026_JP_zonal_detalhado.csv`, `app.py`, `requirements.txt`).
2. Em [share.streamlit.io](https://share.streamlit.io), conecte o repositório.
3. **Main file:** `app.py`
4. **Requirements:** `requirements.txt`

O app procura o CSV em `saida/votacao_secao_2026_JP_zonal_detalhado.csv` relativo à raiz do repositório.
