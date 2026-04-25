"""
Módulo de scouting e análise de jogadores.
Identifica promessas, jogadores subvalorizados e candidatos a upgrade.
"""
import pandas as pd
import numpy as np


def calcular_score_promessa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula um score de promessa baseado em:
    - Gap entre potencial e overall (quanto pode crescer no jogo)
    - Idade (mais jovem = mais tempo para crescer)

    Útil para: comprar barato antes de um upgrade de nota.
    """
    df = df.copy()
    df["gap_potencial"] = df["potencial"] - df["overall"]
    df["score_promessa"] = (
        df["gap_potencial"] * 2.0
        + (30 - df["idade"].clip(upper=30)) * 1.5
    ).clip(lower=0)

    return df.sort_values("score_promessa", ascending=False)


def calcular_score_subvalorizado(df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica jogadores com bom desempenho real mas overall baixo no jogo.
    Candidatos a upgrade futuro de nota.

    Requer DataFrame mergeado com colunas do jogo + colunas reais (xG, xA, etc.)
    """
    df = df_merged.copy()

    colunas_necessarias = ["overall", "xg", "xa"]
    faltando = [c for c in colunas_necessarias if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes no DataFrame: {faltando}")

    for col in ["xg", "xa", "overall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["overall", "xg"])

    df["xg_norm"] = _normalizar(df["xg"])
    df["xa_norm"] = _normalizar(df["xa"].fillna(0))
    df["overall_norm"] = _normalizar(df["overall"])

    df["score_real"] = df["xg_norm"] * 0.6 + df["xa_norm"] * 0.4
    df["score_subvalorizado"] = df["score_real"] - df["overall_norm"]

    return df.sort_values("score_subvalorizado", ascending=False)


def identificar_candidatos_upgrade(
    df_historico: pd.DataFrame,
    df_jogo: pd.DataFrame,
    df_real: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Combina análise histórica de ratings com desempenho real
    para identificar quem tem mais chance de receber upgrade no próximo patch.

    Critérios:
    1. Nunca teve downgrade (rating estável ou crescente)
    2. Potencial > overall (ainda tem espaço no jogo)
    3. Bom desempenho real (se dados disponíveis)
    """
    upgrades = df_historico[df_historico["variacao"] > 0]["sofifa_id"].unique()
    sem_downgrade = ~df_historico[df_historico["variacao"] < 0]["sofifa_id"].isin(
        df_historico["sofifa_id"]
    )

    candidatos = df_jogo[
        (df_jogo["sofifa_id"].isin(upgrades) | ~df_jogo["sofifa_id"].isin(
            df_historico["sofifa_id"]
        ))
        & (df_jogo["potencial"] > df_jogo["overall"])
    ].copy()

    candidatos["score_candidato"] = (
        (candidatos["potencial"] - candidatos["overall"]) * 1.5
        + (30 - candidatos["idade"].clip(upper=30))
    )

    if df_real is not None and "xg" in df_real.columns:
        candidatos = candidatos.merge(
            df_real[["sofifa_id", "xg", "xa"]],
            on="sofifa_id",
            how="left",
        )
        candidatos["score_candidato"] += (
            candidatos["xg"].fillna(0) * 3
            + candidatos["xa"].fillna(0) * 2
        )

    return candidatos.sort_values("score_candidato", ascending=False)


def resumo_por_liga(df: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas agregadas por liga."""
    if "liga" not in df.columns:
        return pd.DataFrame()

    return df.groupby("liga").agg(
        total_jogadores=("sofifa_id", "count"),
        overall_medio=("overall", "mean"),
        potencial_medio=("potencial", "mean"),
        idade_media=("idade", "mean"),
        top_overall=("overall", "max"),
    ).round(1).sort_values("overall_medio", ascending=False)


def _normalizar(serie: pd.Series) -> pd.Series:
    mn, mx = serie.min(), serie.max()
    if mx == mn:
        return pd.Series(np.zeros(len(serie)), index=serie.index)
    return (serie - mn) / (mx - mn)
