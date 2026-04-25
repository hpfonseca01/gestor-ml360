"""
Coletor de dados reais de desempenho via FBref.
Usa pandas.read_html() para ler as tabelas HTML do site.
"""
import time
import pandas as pd
import requests
from pathlib import Path
from config.settings import RAW_DIR

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# IDs das ligas no FBref
LIGAS_FBREF = {
    "premier_league":  9,
    "la_liga":         12,
    "bundesliga":      20,
    "serie_a":         11,
    "ligue_1":         13,
    "brasileiro":      24,
}

# Tipos de stats disponíveis no FBref
STAT_TYPES = {
    "standard":  "stats",
    "shooting":  "shooting",
    "passing":   "passing",
    "defense":   "defense",
    "possession": "possession",
}

TEMPORADA_ATUAL = "2025-2026"


def _url_liga(liga_id: int, stat: str, temporada: str) -> str:
    ano_inicio, ano_fim = temporada.split("-")
    return (
        f"https://fbref.com/en/comps/{liga_id}/{ano_inicio}-{ano_fim[-2:]}/"
        f"{stat}/{ano_inicio}-{ano_fim[-2:]}-stats"
    )


def _ler_tabela_fbref(url: str) -> pd.DataFrame | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        time.sleep(4)  # respeitar rate limit do FBref

        tabelas = pd.read_html(resp.text, header=[0, 1])
        for df in tabelas:
            # A tabela de jogadores tem coluna "Player"
            if "Player" in df.columns.get_level_values(-1):
                df.columns = [
                    "_".join(str(c) for c in col).strip("_").lower().replace(" ", "_")
                    if isinstance(col, tuple) else str(col).lower()
                    for col in df.columns
                ]
                df = df[df.get("unnamed:_1_level_0_player", df.get("player", pd.Series())) != "Player"]
                df = df.dropna(how="all")
                return df
    except Exception as e:
        print(f"Erro ao ler {url}: {e}")
    return None


def coletar_stats_liga(
    liga: str,
    stat_type: str = "standard",
    temporada: str = TEMPORADA_ATUAL,
) -> pd.DataFrame | None:
    """
    Coleta estatísticas de uma liga e tipo de stat específico do FBref.

    Args:
        liga: chave da liga (ex: 'premier_league')
        stat_type: tipo de stat ('standard', 'shooting', 'passing', 'defense', 'possession')
        temporada: temporada no formato '2025-2026'

    Returns:
        DataFrame com as estatísticas ou None se falhar
    """
    liga_id = LIGAS_FBREF.get(liga)
    if not liga_id:
        raise ValueError(f"Liga '{liga}' não encontrada. Disponíveis: {list(LIGAS_FBREF)}")

    stat_path = STAT_TYPES.get(stat_type, stat_type)
    url = _url_liga(liga_id, stat_path, temporada)
    print(f"Coletando {liga} - {stat_type}: {url}")

    df = _ler_tabela_fbref(url)
    if df is not None:
        df["liga"] = liga
        df["temporada"] = temporada
        df["stat_type"] = stat_type
    return df


def coletar_todas_ligas(
    stat_type: str = "standard",
    temporada: str = TEMPORADA_ATUAL,
) -> pd.DataFrame:
    """
    Coleta estatísticas de todas as ligas configuradas.
    """
    dfs = []
    for liga in LIGAS_FBREF:
        df = coletar_stats_liga(liga, stat_type, temporada)
        if df is not None and len(df) > 0:
            dfs.append(df)
            print(f"  {liga}: {len(df)} jogadores")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def salvar_csv(df: pd.DataFrame, nome_arquivo: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RAW_DIR / nome_arquivo
    df.to_csv(caminho, index=False)
    print(f"Salvo em: {caminho}")
    return caminho


if __name__ == "__main__":
    df = coletar_todas_ligas()
    print(f"\nTotal: {len(df)} registros")
    salvar_csv(df, "fbref_stats.csv")
