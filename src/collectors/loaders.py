"""
Loaders para CSVs reais de cada fonte.
Faz o mapeamento de colunas para o schema interno do projeto.

Uso:
    from src.collectors.loaders import carregar_eafc_kaggle, carregar_fbref_csv
    df = carregar_eafc_kaggle("data/raw/fc26_players.csv")
    df = carregar_fbref_csv("data/raw/fbref_premier_league_standard.csv", liga="premier_league")
"""
import pandas as pd
from pathlib import Path

# Mapeamento de colunas do Kaggle EAFC26 → schema interno
MAPA_KAGGLE_EAFC = {
    "sofifa_id":                    "sofifa_id",
    "short_name":                   "nome",
    "long_name":                    "nome_completo",
    "player_positions":             "posicao",
    "overall":                      "overall",
    "potential":                    "potencial",
    "value_eur":                    "valor_eur",
    "wage_eur":                     "salario_eur",
    "age":                          "idade",
    "height_cm":                    "altura_cm",
    "weight_kg":                    "peso_kg",
    "club_name":                    "time",
    "league_name":                  "liga_nome",
    "nationality_name":             "nacionalidade",
    "preferred_foot":               "pe_preferido",
    "weak_foot":                    "weak_foot",
    "skill_moves":                  "skill_moves",
    "pace":                         "ritmo",
    "shooting":                     "finalizacao",
    "passing":                      "passe",
    "dribbling":                    "drible",
    "defending":                    "defesa",
    "physic":                       "fisico",
}

# Mapeamento de ligas do Kaggle → chave interna
MAPA_LIGAS_KAGGLE = {
    "English Premier League":       "premier_league",
    "Spain Primera Division":       "la_liga",
    "German 1. Bundesliga":         "bundesliga",
    "Italian Serie A":              "serie_a",
    "French Ligue 1":               "ligue_1",
    "Brazilian Série A":            "brasileiro",
    "Portuguese Primeira Liga":     "primeira_liga",
    "Dutch Eredivisie":             "eredivisie",
}

# Mapeamento de colunas do FBref CSV manual → schema interno
MAPA_FBREF_CSV = {
    "Player":           "nome",
    "Nation":           "nacionalidade",
    "Pos":              "posicao",
    "Squad":            "time",
    "Comp":             "liga_nome",
    "Age":              "idade",
    "MP":               "partidas",
    "Min":              "minutos",
    "Gls":              "gols",
    "Ast":              "assistencias",
    "xG":               "xg",
    "xAG":              "xa",
    "Gls/90":           "gols_por_90",
    "Ast/90":           "assistencias_por_90",
    "xG/90":            "xg_por_90",
    "xAG/90":           "xa_por_90",
    "PrgC":             "progressive_carries",
    "PrgP":             "progressive_passes",
    "PrgR":             "progressive_runs",
}


def carregar_eafc_kaggle(caminho: str | Path, patch_versao: str = None) -> pd.DataFrame:
    """
    Carrega CSV do Kaggle (EAFC26) e mapeia para o schema interno.

    O CSV do Kaggle tem colunas como sofifa_id, short_name, overall, potential,
    pace, shooting, passing, dribbling, defending, physic, etc.

    Args:
        caminho: path para o arquivo CSV
        patch_versao: versão do patch do jogo (ex: '6.0.1')

    Returns:
        DataFrame pronto para inserir no banco via db.inserir_jogadores_jogo()
    """
    df = pd.read_csv(caminho, low_memory=False)
    print(f"CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")

    # Renomear apenas colunas que existem no CSV
    mapa = {k: v for k, v in MAPA_KAGGLE_EAFC.items() if k in df.columns}
    df = df.rename(columns=mapa)

    # Normalizar coluna de posição (pode vir como "ST, CF" — pegar só a primeira)
    if "posicao" in df.columns:
        df["posicao"] = df["posicao"].astype(str).str.split(",").str[0].str.strip()

    # Mapear nome da liga para chave interna
    if "liga_nome" in df.columns:
        df["liga"] = df["liga_nome"].map(MAPA_LIGAS_KAGGLE).fillna(
            df["liga_nome"].str.lower().str.replace(" ", "_")
        )

    # Normalizar sofifa_id para string
    if "sofifa_id" in df.columns:
        df["sofifa_id"] = df["sofifa_id"].astype(str)

    # Campos de controle
    df["versao_jogo"] = "EAFC26"
    if patch_versao:
        df["patch_versao"] = patch_versao

    # Normalizar nome para match com dados reais
    if "nome" in df.columns:
        df["nome_normalizado"] = df["nome"].str.lower().str.strip()

    print(f"Após mapeamento: {len(df)} jogadores prontos")
    return df


def carregar_fbref_csv(
    caminho: str | Path,
    liga: str = None,
    temporada: str = "2025-2026",
) -> pd.DataFrame:
    """
    Carrega CSV exportado manualmente do FBref (Share & more → Get table as CSV).

    O FBref exporta tabelas com cabeçalho duplo às vezes. Esta função
    detecta e trata os dois formatos (cabeçalho simples e duplo).

    Args:
        caminho: path para o arquivo CSV
        liga: chave da liga (ex: 'premier_league') — opcional se vier na coluna Comp
        temporada: temporada no formato '2025-2026'

    Returns:
        DataFrame pronto para inserir via db.inserir_jogadores_reais()
    """
    df = pd.read_csv(caminho)
    print(f"CSV FBref carregado: {len(df)} linhas")

    # Remover linhas de header repetido (FBref repete "Player" a cada 25 linhas) e linhas vazias
    if "Player" in df.columns:
        df = df[(df["Player"] != "Player") & df["Player"].notna()].copy()

    # Renomear colunas
    mapa = {k: v for k, v in MAPA_FBREF_CSV.items() if k in df.columns}
    df = df.rename(columns=mapa)

    # Colunas numéricas
    num_cols = [
        "partidas", "minutos", "gols", "assistencias",
        "xg", "xa", "xg_por_90", "xa_por_90",
        "progressive_carries", "progressive_passes",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Campos de controle
    df["temporada"] = temporada
    df["fonte"] = "fbref_manual"

    if liga:
        df["liga"] = liga
    elif "liga_nome" in df.columns:
        df["liga"] = df["liga_nome"].str.lower().str.replace(" ", "_")

    # Normalizar nome para match
    if "nome" in df.columns:
        df["nome_normalizado"] = df["nome"].str.lower().str.strip()

    print(f"Após mapeamento: {len(df)} jogadores prontos")
    return df



def detectar_formato(caminho: str | Path) -> str:
    """
    Tenta detectar automaticamente o formato do CSV.
    Retorna: 'kaggle_eafc', 'fbref', ou 'desconhecido'
    """
    df = pd.read_csv(caminho, nrows=2)
    colunas = set(df.columns)

    if "sofifa_id" in colunas and "overall" in colunas:
        return "kaggle_eafc"
    if "Player" in colunas and ("xG" in colunas or "Gls" in colunas):
        return "fbref"
    return "desconhecido"
