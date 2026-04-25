"""
Limpeza e normalização dos dados coletados.
"""
import re
import pandas as pd


def limpar_valor_monetario(valor: str) -> float | None:
    """Converte '€45.5M' ou '€500K' para float em euros."""
    if pd.isna(valor) or not isinstance(valor, str):
        return None
    valor = valor.replace("€", "").replace(",", "").strip()
    multiplicadores = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for sufixo, mult in multiplicadores.items():
        if valor.endswith(sufixo):
            try:
                return float(valor[:-1]) * mult
            except ValueError:
                return None
    try:
        return float(valor)
    except ValueError:
        return None


def normalizar_nome(nome: str) -> str:
    """Normaliza nomes para comparação: remove acentos, lowercase, strip."""
    if not isinstance(nome, str):
        return ""
    nome = nome.lower().strip()
    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a", "ä": "a",
        "é": "e", "ê": "e", "è": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "õ": "o", "ô": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ç": "c", "ñ": "n",
    }
    for orig, rep in substituicoes.items():
        nome = nome.replace(orig, rep)
    return re.sub(r"\s+", " ", nome)


def limpar_dataframe_sofifa(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    colunas_numericas = ["overall", "potencial", "idade", "altura_cm", "peso_kg",
                         "ritmo", "finalizacao", "passe", "drible", "defesa", "fisico"]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["valor_eur", "salario_eur"]:
        if col in df.columns:
            df[col] = df[col].apply(limpar_valor_monetario)

    if "nome" in df.columns:
        df["nome_normalizado"] = df["nome"].apply(normalizar_nome)

    df = df.drop_duplicates(subset=["sofifa_id"]) if "sofifa_id" in df.columns else df
    return df


def limpar_dataframe_fbref(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    colunas_numericas = ["partidas", "minutos", "gols", "assistencias",
                         "xg", "xa", "xg_por_90", "xa_por_90",
                         "progressive_carries", "progressive_passes"]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    nome_col = next((c for c in df.columns if "player" in c or "nome" in c), None)
    if nome_col:
        df["nome_normalizado"] = df[nome_col].apply(normalizar_nome)

    return df
