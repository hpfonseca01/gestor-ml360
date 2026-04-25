"""
Carregador de datasets do Kaggle para uso como base inicial dos dados do EAFC26.
Requer kaggle CLI configurado com API key (~/.kaggle/kaggle.json).
"""
import subprocess
import pandas as pd
from pathlib import Path
from config.settings import RAW_DIR, KAGGLE_DATASET_IDS


def baixar_dataset(dataset_id: str) -> Path:
    """
    Baixa um dataset do Kaggle para data/raw/.

    Args:
        dataset_id: ID no formato 'usuario/nome-dataset'

    Returns:
        Path da pasta onde o dataset foi extraído
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destino = RAW_DIR / dataset_id.split("/")[-1]
    destino.mkdir(exist_ok=True)

    print(f"Baixando {dataset_id}...")
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset_id, "-p", str(destino), "--unzip"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Erro ao baixar dataset: {result.stderr}")

    print(f"Download concluído: {destino}")
    return destino


def carregar_csv_eafc(pasta: Path) -> pd.DataFrame:
    """
    Carrega o CSV de jogadores EAFC26 de uma pasta baixada do Kaggle.

    Returns:
        DataFrame consolidado com os dados do jogo
    """
    csvs = list(pasta.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {pasta}")

    dfs = [pd.read_csv(f) for f in csvs]
    df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]

    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    return df


def baixar_e_carregar_todos() -> pd.DataFrame:
    """
    Baixa e carrega todos os datasets EAFC26 configurados no settings.
    """
    dfs = []
    for dataset_id in KAGGLE_DATASET_IDS:
        try:
            pasta = baixar_dataset(dataset_id)
            df = carregar_csv_eafc(pasta)
            df["fonte_kaggle"] = dataset_id
            dfs.append(df)
        except Exception as e:
            print(f"Erro com {dataset_id}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


if __name__ == "__main__":
    df = baixar_e_carregar_todos()
    print(f"Total de registros: {len(df)}")
    print(df.head())
