"""
Coletor de dados reais de desempenho via FBref (usando a biblioteca soccerdata).
Coleta estatísticas como gols, assistências, xG, xA, pressões, etc.
"""
import pandas as pd
import soccerdata as sd
from pathlib import Path
from config.settings import RAW_DIR

LIGAS_FBREF = {
    "premier_league": "ENG-Premier League",
    "la_liga": "ESP-La Liga",
    "bundesliga": "GER-Bundesliga",
    "serie_a": "ITA-Serie A",
    "ligue_1": "FRA-Ligue 1",
    "brasileiro": "BRA-Brasileirao",
}

TEMPORADA_ATUAL = "2025-2026"


def coletar_stats_jogadores(liga: str, temporada: str = TEMPORADA_ATUAL) -> pd.DataFrame:
    """
    Coleta estatísticas padrão dos jogadores de uma liga via FBref.

    Args:
        liga: chave da liga (ex: 'premier_league')
        temporada: temporada no formato '2025-2026'

    Returns:
        DataFrame com as estatísticas dos jogadores
    """
    nome_liga = LIGAS_FBREF.get(liga)
    if not nome_liga:
        raise ValueError(f"Liga '{liga}' não encontrada. Disponíveis: {list(LIGAS_FBREF)}")

    fbref = sd.FBref(leagues=nome_liga, seasons=temporada)
    df = fbref.read_player_season_stats(stat_type="standard")
    df = df.reset_index()
    return df


def coletar_stats_avancadas(liga: str, temporada: str = TEMPORADA_ATUAL) -> pd.DataFrame:
    """
    Coleta stats avançadas: xG, xA, progressive carries/passes.
    """
    nome_liga = LIGAS_FBREF.get(liga)
    if not nome_liga:
        raise ValueError(f"Liga '{liga}' não encontrada.")

    fbref = sd.FBref(leagues=nome_liga, seasons=temporada)

    stats = {}
    for stat_type in ["shooting", "passing", "goal_shot_creation", "defense", "possession"]:
        try:
            df = fbref.read_player_season_stats(stat_type=stat_type)
            stats[stat_type] = df.reset_index()
        except Exception as e:
            print(f"Aviso: não foi possível coletar '{stat_type}': {e}")

    if not stats:
        return pd.DataFrame()

    base = stats.get("shooting", list(stats.values())[0])
    colunas_chave = ["player", "team", "season"]

    for stat_type, df in stats.items():
        if stat_type == "shooting":
            continue
        colunas_extras = [c for c in df.columns if c not in base.columns or c in colunas_chave]
        base = base.merge(
            df[[c for c in colunas_chave if c in df.columns] + colunas_extras],
            on=[c for c in colunas_chave if c in base.columns and c in df.columns],
            how="left",
            suffixes=("", f"_{stat_type}"),
        )

    return base


def coletar_todas_ligas(temporada: str = TEMPORADA_ATUAL) -> pd.DataFrame:
    """
    Coleta estatísticas padrão de todas as ligas configuradas.
    """
    dfs = []
    for liga in LIGAS_FBREF:
        try:
            print(f"Coletando {liga}...")
            df = coletar_stats_jogadores(liga, temporada)
            df["liga"] = liga
            dfs.append(df)
        except Exception as e:
            print(f"Erro ao coletar {liga}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def salvar_csv(df: pd.DataFrame, nome_arquivo: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RAW_DIR / nome_arquivo
    df.to_csv(caminho, index=False)
    print(f"Salvo em: {caminho}")
    return caminho


if __name__ == "__main__":
    df = coletar_todas_ligas()
    print(f"Jogadores coletados: {len(df)}")
    salvar_csv(df, "fbref_stats.csv")
