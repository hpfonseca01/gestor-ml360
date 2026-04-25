# Como alimentar a base com dados reais

## Fonte 1 — EAFC26 (dados do jogo) via Kaggle

### Download manual (sem login)
1. Acesse: https://www.kaggle.com/datasets/rovnez/fc-26-fifa-26-player-data
2. Clique em **Download** (canto superior direito)
3. Extraia o ZIP — você terá um arquivo como `fc26_players.csv`
4. Coloque em `data/raw/`

### Carregar no banco
```bash
python atualizar_dados.py --csv data/raw/fc26_players.csv --tipo eafc --patch "6.0.1"
```

### Alternativa (Kaggle CLI — automatizado)
```bash
# 1. Crie conta em kaggle.com → Account → API → Create New Token
# 2. Salve o kaggle.json em ~/.kaggle/kaggle.json
# 3. Instale: pip install kaggle
# 4. Baixe:
kaggle datasets download -d rovnez/fc-26-fifa-26-player-data -p data/raw/ --unzip
python atualizar_dados.py --csv data/raw/fc26_players.csv --tipo eafc --patch "6.0.1"
```

---

## Fonte 2 — Stats reais via FBref (manual)

### Como exportar do FBref
1. Acesse a página de stats da liga, ex:
   - Premier League: https://fbref.com/en/comps/9/stats/Premier-League-Stats
   - La Liga: https://fbref.com/en/comps/12/stats/La-Liga-Stats
   - Bundesliga: https://fbref.com/en/comps/20/stats/Bundesliga-Stats
   - Serie A: https://fbref.com/en/comps/11/stats/Serie-A-Stats
   - Ligue 1: https://fbref.com/en/comps/13/stats/Ligue-1-Stats
   - Brasileirão: https://fbref.com/en/comps/24/stats/Serie-A-Stats

2. Na tabela de jogadores, clique em **"Share & more"** (ícone acima da tabela)
3. Clique em **"Get table as CSV (for Excel)"**
4. Selecione todo o texto exibido (Ctrl+A) e cole em um arquivo `.csv`
5. Salve em `data/raw/`, ex: `fbref_premier_league_standard.csv`

### Carregar no banco
```bash
# Carregar uma liga específica
python atualizar_dados.py --csv data/raw/fbref_premier_league_standard.csv --tipo fbref --liga premier_league

# Ou carregar todos os CSVs da pasta de uma vez
# (nomeie os arquivos com o nome da liga, ex: fbref_bundesliga.csv, fbref_serie_a.csv)
python atualizar_dados.py --pasta data/raw/ --patch "6.0.1"
```

---

## Fonte 3 — SoFIFA (scraping local)

O scraping funciona apenas rodando na **sua máquina local** (não em servidor cloud).

```bash
# Na sua máquina local:
python atualizar_dados.py --scrape-sofifa --patch "6.0.1"
```

---

## Fluxo completo recomendado após cada patch do jogo

```bash
# 1. Baixe o CSV do Kaggle (ou use a Kaggle CLI)
# 2. Exporte stats das ligas que você acompanha no FBref

# 3. Carregue tudo de uma vez
python atualizar_dados.py \
  --csv data/raw/fc26_players.csv --tipo eafc --patch "6.0.2"

python atualizar_dados.py \
  --csv data/raw/fbref_premier_league.csv --tipo fbref --liga premier_league

# 4. Abra o notebook para análise
jupyter notebook notebooks/01_exploracao_inicial.ipynb
```

---

## Estrutura esperada dos arquivos

| Arquivo | Tipo | Colunas obrigatórias |
|---|---|---|
| `fc26_players.csv` | eafc | `sofifa_id`, `short_name`, `overall`, `potential` |
| `fbref_*.csv` | fbref | `Player`, `Squad`, `Gls`, `Ast`, `xG` |

O sistema detecta o formato automaticamente se você omitir `--tipo`.
