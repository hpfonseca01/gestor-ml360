"""
Cruzamento entre dados do jogo (EAFC26) e dados reais (FBref).
O maior desafio é o match de nomes entre as duas fontes.
"""
import pandas as pd
from difflib import SequenceMatcher
from .cleaner import normalizar_nome


def _similaridade(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def match_por_nome(
    df_jogo: pd.DataFrame,
    df_real: pd.DataFrame,
    limiar: float = 0.82,
) -> pd.DataFrame:
    """
    Faz o cruzamento entre jogadores do jogo e da vida real por similaridade de nome.

    Args:
        df_jogo: DataFrame com dados do EAFC26 (precisa ter 'nome_normalizado')
        df_real: DataFrame com dados do FBref (precisa ter 'nome_normalizado')
        limiar: similaridade mínima para considerar match (0 a 1)

    Returns:
        DataFrame com os dois datasets mergeados + coluna de similaridade
    """
    if "nome_normalizado" not in df_jogo.columns:
        df_jogo = df_jogo.copy()
        df_jogo["nome_normalizado"] = df_jogo["nome"].apply(normalizar_nome)

    if "nome_normalizado" not in df_real.columns:
        df_real = df_real.copy()
        nome_col = next((c for c in df_real.columns if "player" in c or "nome" in c), None)
        if nome_col:
            df_real["nome_normalizado"] = df_real[nome_col].apply(normalizar_nome)

    nomes_reais = df_real["nome_normalizado"].tolist()
    matches = []

    for _, jogador in df_jogo.iterrows():
        nome_jogo = jogador.get("nome_normalizado", "")
        melhor_sim = 0.0
        melhor_idx = None

        for i, nome_real in enumerate(nomes_reais):
            sim = _similaridade(nome_jogo, nome_real)
            if sim > melhor_sim:
                melhor_sim = sim
                melhor_idx = i

        if melhor_sim >= limiar and melhor_idx is not None:
            matches.append({
                "sofifa_id": jogador.get("sofifa_id"),
                "nome_jogo": jogador.get("nome"),
                "idx_real": melhor_idx,
                "similaridade": melhor_sim,
            })

    if not matches:
        return pd.DataFrame()

    df_matches = pd.DataFrame(matches)
    df_real_matched = df_real.iloc[df_matches["idx_real"].tolist()].reset_index(drop=True)

    sufixos_jogo = {
        c: f"{c}_jogo" for c in df_jogo.columns if c in df_real_matched.columns
        and c not in ["sofifa_id", "nome_normalizado"]
    }
    df_jogo_renamed = df_jogo.rename(columns=sufixos_jogo)

    resultado = pd.concat(
        [
            df_jogo_renamed.loc[
                df_jogo["sofifa_id"].isin(df_matches["sofifa_id"])
            ].reset_index(drop=True),
            df_real_matched,
            df_matches[["similaridade"]].reset_index(drop=True),
        ],
        axis=1,
    )

    return resultado.sort_values("similaridade", ascending=False)


def merge_por_mapeamento(
    df_jogo: pd.DataFrame,
    df_real: pd.DataFrame,
    mapeamento: pd.DataFrame,
) -> pd.DataFrame:
    """
    Usa tabela de mapeamento já verificada (da tabela mapeamento_jogadores do DB).
    Mais preciso que o match por similaridade.
    """
    mapeamento_verificado = mapeamento[mapeamento["verificado"] == True]

    df = df_jogo.merge(
        mapeamento_verificado[["sofifa_id", "fbref_id"]],
        on="sofifa_id",
        how="inner",
    )
    df = df.merge(df_real, left_on="fbref_id", right_on="player_id", how="left")
    return df
