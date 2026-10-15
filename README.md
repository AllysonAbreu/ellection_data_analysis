# Análise de Dados Eleitorais — João Pessoa

Projeto de estudo e análise dos resultados eleitorais por seção em João Pessoa (PB). O fluxo cruza os arquivos de votação do Tribunal Superior Eleitoral (TSE) com uma planilha de locais e seções de interesse, gera uma base detalhada e disponibiliza os dados em um painel interativo feito com Streamlit.

## Objetivo e escopo

O recorte considera o primeiro turno, o estado da Paraíba (`SG_UF=PB`) e o município de João Pessoa (`CD_MUNICIPIO=20516`). A planilha zonal delimita os locais incluídos, portanto o resultado não representa todas as seções do município.

O script combina os resultados estaduais com os registros presidenciais do arquivo nacional, associa os metadados da planilha por zona e local de votação e calcula o total de votos presidenciais por zona, local e seção. A saída mantém os votos individuais em `QT_VOTOS` e `DS_CARGO`, além da coluna `QT_VOTOS_PRESIDENTE`, que repete o total da seção nas linhas correspondentes. Para somar esse total, use uma única ocorrência por zona, local e seção; não some a coluna linha a linha.

## Dados de entrada

Coloque os arquivos abaixo em `primeiro_turno/`:

- `votacao_secao_2026_PB.csv`: resultados do TSE para a Paraíba.
- `votacao_secao_2026_BR.csv`: resultados nacionais, usados para carregar os votos presidenciais.
- `dados_primeiro_turno_2026_jp_zonal.xlsx`: planilha de locais e seções; o script lê a aba `Analitico_por_escola` e as colunas `COLEGIO`, `BAIRRO`, `SECOES`, `COD_COLEGIO` e `ZONA`.

**Pasta de dados no Google Drive:** [Clique aqui](https://drive.google.com/drive/folders/1mrXqOu5CjXQzZwfTEz-0IBg9V6YeinRB?usp=drive_link).

Os arquivos brutos são grandes e ficam fora do controle de versão. O CSV detalhado gerado pelo projeto é salvo em `primeiro_turno/saida/`.

## Instalação

No PowerShell, a partir da raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r primeiro_turno/requirements.txt
```

## Gerar a base

Com os arquivos de entrada na pasta `primeiro_turno/`, execute na raiz:

```powershell
python primeiro_turno/mapear_votacao_zonal.py
```

O arquivo `primeiro_turno/saida/votacao_secao_2026_JP_zonal_detalhado.csv` contém os registros por cargo e candidato associados aos locais da planilha, incluindo os votos presidenciais. Para informar caminhos diferentes, use:

```powershell
python primeiro_turno/mapear_votacao_zonal.py `
	--csv primeiro_turno/votacao_secao_2026_PB.csv `
	--csv-presidente primeiro_turno/votacao_secao_2026_BR.csv `
	--xlsx primeiro_turno/dados_primeiro_turno_2026_jp_zonal.xlsx `
	--saida primeiro_turno/saida
```

O cruzamento com a planilha usa `NR_ZONA` e `NR_LOCAL_VOTACAO`; a totalização presidencial usa `NR_ZONA`, `NR_LOCAL_VOTACAO` e `NR_SECAO`.

## Painel Streamlit

Depois de gerar a base, inicie o painel a partir da pasta `primeiro_turno/`:

```powershell
cd primeiro_turno
streamlit run app.py
```

O painel permite filtrar por seção, bairro, local, cargo, legenda e nome. A visão geral usa os registros presidenciais como referência de comparecimento quando eles estão disponíveis; os gráficos e a tabela acompanham os filtros aplicados.

## Testes

Instale as dependências de desenvolvimento e execute a suíte a partir da raiz:

```powershell
python -m pip install -r primeiro_turno/requirements-dev.txt
python -m pytest -q
```

Os testes usam arquivos temporários e dados sintéticos; não exigem baixar a base real do TSE ou a planilha zonal.

## Estrutura

- `primeiro_turno/mapear_votacao_zonal.py`: leitura, filtragem, cruzamento e exportação dos dados.
- `primeiro_turno/app.py`: painel de exploração dos resultados.
- `primeiro_turno/test_mapear_votacao_zonal.py` e `primeiro_turno/test_app.py`: testes automatizados do processamento e do painel.
- `primeiro_turno/saida/`: base detalhada gerada para o painel.
- `primeiro_turno/README.md`: instruções adicionais do módulo de primeiro turno.
