"""
Coletor de dados reais via StatsBomb Open Data (GitHub).
Agrega eventos de partidas em stats por jogador (gols, assistências, xG, xA).
"""
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

warnings.filterwarnings("ignore")
from statsbombpy import sb

from config.settings import RAW_DIR

COMPETICOES = {
    "bundesliga_2324": (9,  281, "bundesliga", "2023/2024"),
    "ligue1_2223":     (7,  235, "ligue_1",    "2022/2023"),
    "laliga_2021":     (11, 90,  "la_liga",    "2020/2021"),
    "laliga_1920":     (11, 42,  "la_liga",    "2019/2020"),
}


def _agregar_partida(match_id: int) -> pd.DataFrame:
    """Extrai e agrega stats de uma partida por jogador."""
    try:
        ev = sb.events(match_id=match_id)
    except Exception:
        return pd.DataFrame()

    ev = ev[ev["player"].notna() & ev["team"].notna()]

    # --- Chutes ---
    shots = ev[ev["type"] == "Shot"].copy()
    for col in ["shot_outcome", "shot_statsbomb_xg"]:
        if col not in shots.columns:
            shots[col] = np.nan

    df_shots = shots.groupby(["player", "team"]).agg(
        chutes=("type", "count"),
        gols=("shot_outcome", lambda x: (x == "Goal").sum()),
        xg=("shot_statsbomb_xg", "sum"),
    ).reset_index()

    # --- Passes ---
    passes = ev[ev["type"] == "Pass"].copy()

    # Garantir que colunas opcionais existam antes de usar
    for col in ["pass_goal_assist", "pass_shot_assist", "pass_length", "pass_outcome"]:
        if col not in passes.columns:
            passes[col] = np.nan

    df_passes = passes.groupby(["player", "team"]).agg(
        assistencias=("pass_goal_assist", lambda x: x.fillna(False).astype(bool).sum()),
        passes_chave=("pass_shot_assist", lambda x: x.fillna(False).astype(bool).sum()),
        total_passes=("type", "count"),
    ).reset_index()

    # Passes progressivos (avançam mais de 10m e são completos)
    passes["prog"] = (passes["pass_length"].fillna(0) > 10) & (passes["pass_outcome"].isna())
    df_prog_passes = passes[passes["prog"]].groupby(["player", "team"]).size().reset_index(name="progressive_passes")

    # --- Carries ---
    carries = ev[ev["type"] == "Carry"].copy()
    carries["start_x"] = carries["location"].apply(lambda x: x[0] if isinstance(x, list) else np.nan)
    carries["end_x"] = carries["carry_end_location"].apply(lambda x: x[0] if isinstance(x, list) else np.nan)
    carries["prog_carry"] = (carries["end_x"] - carries["start_x"]) > 5
    df_carries = carries[carries["prog_carry"].fillna(False)].groupby(["player", "team"]).size().reset_index(name="progressive_carries")

    # --- Minutos jogados (via substitution + period) ---
    mins = _calcular_minutos(ev)

    # --- Merge tudo ---
    base = ev[["player", "team"]].drop_duplicates()

    for df_merge in [df_shots, df_passes, df_prog_passes, df_carries, mins]:
        if not df_merge.empty:
            base = base.merge(df_merge, on=["player", "team"], how="left")

    base = base.fillna(0)
    return base


def _calcular_minutos(ev: pd.DataFrame) -> pd.DataFrame:
    """Estima minutos jogados por jogador a partir dos eventos de substituição."""
    subs = ev[ev["type"] == "Substitution"][["team", "player", "minute"]].copy()
    subs = subs.rename(columns={"player": "substituto_saiu", "minute": "minuto_saiu"})

    # Jogadores que saíram: minutos = minuto_saiu
    # Jogadores que não saíram: 90 minutos
    todos = ev[["player", "team"]].drop_duplicates()
    saiu = subs.rename(columns={"substituto_saiu": "player"})[["player", "team", "minuto_saiu"]]
    df = todos.merge(saiu, on=["player", "team"], how="left")
    df["minutos"] = df["minuto_saiu"].fillna(90)
    return df[["player", "team", "minutos"]]


def coletar_competicao(chave: str) -> pd.DataFrame:
    """
    Coleta e agrega stats de todos os jogos de uma competição.
    """
    if chave not in COMPETICOES:
        raise ValueError(f"Disponíveis: {list(COMPETICOES)}")

    comp_id, season_id, liga, temporada = COMPETICOES[chave]
    matches = sb.matches(competition_id=comp_id, season_id=season_id)
    print(f"\nColetando {chave}: {len(matches)} partidas...")

    dfs = []
    for match_id in tqdm(matches["match_id"].tolist(), desc=chave):
        df_partida = _agregar_partida(match_id)
        if not df_partida.empty:
            dfs.append(df_partida)

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Agregar por jogador
    colunas_soma = ["minutos", "chutes", "gols", "xg", "assistencias",
                    "passes_chave", "total_passes", "progressive_passes", "progressive_carries"]
    agg_dict = {c: "sum" for c in colunas_soma if c in df.columns}
    agg_dict["team"] = "last"

    df_agg = df.groupby("player").agg(agg_dict).reset_index()
    df_agg = df_agg.rename(columns={"player": "nome", "team": "time"})

    # Contar partidas (número de jogos em que apareceu)
    partidas_por_jogador = df.groupby("player").size().reset_index(name="partidas")
    partidas_por_jogador = partidas_por_jogador.rename(columns={"player": "nome"})
    df_agg = df_agg.merge(partidas_por_jogador, on="nome", how="left")

    df_agg["liga"] = liga
    df_agg["temporada"] = temporada
    df_agg["fonte"] = "statsbomb"
    df_agg["nome_normalizado"] = df_agg["nome"].str.lower().str.strip()

    # Stats por 90 minutos
    min90 = (df_agg["minutos"] / 90).replace(0, np.nan)
    df_agg["xg_por_90"] = (df_agg["xg"] / min90).round(2).fillna(0)
    df_agg["xa_por_90"] = (df_agg.get("xa", pd.Series(0, index=df_agg.index)) / min90).round(2).fillna(0)

    # Arredondar xg/xa
    df_agg["xg"] = df_agg["xg"].round(2)

    return df_agg.sort_values("xg", ascending=False)


def coletar_tudo(competicoes: list[str] = None) -> pd.DataFrame:
    """Coleta todas (ou as selecionadas) as competições disponíveis."""
    chaves = competicoes or list(COMPETICOES.keys())
    dfs = []
    for chave in chaves:
        try:
            df = coletar_competicao(chave)
            if not df.empty:
                dfs.append(df)
                print(f"  {chave}: {len(df)} jogadores")
        except Exception as e:
            print(f"Erro em {chave}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def salvar_csv(df: pd.DataFrame, nome_arquivo: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RAW_DIR / nome_arquivo
    df.to_csv(caminho, index=False)
    print(f"Salvo em: {caminho}")
    return caminho
