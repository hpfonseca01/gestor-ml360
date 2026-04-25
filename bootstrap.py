"""
Bootstrap do Gestor ML360 — execute na sua máquina Windows.

Como usar:
    1. Abra o PowerShell em C:\\gestor-ml360
    2. Execute: python bootstrap.py

O script vai:
    - Instalar as dependências
    - Baixar o dataset EAFC26 do Kaggle
    - Coletar stats reais da temporada atual via FBref
    - Popular o banco de dados DuckDB
"""
import subprocess
import sys
import os
import getpass
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATASET_EAFC26 = "flynn28/eafc26-player-database"
PATCH_ATUAL = "6.0.0"


def rodar(cmd: str, descricao: str = "") -> bool:
    print(f"  → {descricao or cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("   ", result.stdout.strip()[:300])
    if result.returncode != 0:
        print(f"   ERRO: {result.stderr.strip()[:300]}")
        return False
    return True


def instalar_dependencias():
    print("\n[1/4] Instalando dependências...")
    pacotes = [
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "duckdb>=0.10.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "thefuzz>=0.22.0",
        "kaggle",
    ]
    rodar(f'pip install {" ".join(pacotes)} -q', "instalando pacotes")


def configurar_kaggle() -> bool:
    """Configura o token do Kaggle via variável de ambiente."""
    print("\n[2/4] Configurando Kaggle...")

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        print("  Informe seu token do Kaggle (KGAT_...)")
        print("  (Gere em: kaggle.com → Settings → API → Create New Token)")
        token = getpass.getpass("  Token: ").strip()

    if not token:
        print("  Token não informado. Pulando download do Kaggle.")
        return False

    os.environ["KAGGLE_API_TOKEN"] = token
    print("  Token configurado.")
    return True


def baixar_eafc26() -> list[Path]:
    """Baixa o dataset EAFC26 do Kaggle."""
    print("\n[3/4] Baixando EAFC26 do Kaggle...")
    raw_dir = BASE_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    ok = rodar(
        f'kaggle datasets download -d {DATASET_EAFC26} -p "{raw_dir}" --unzip',
        f"kaggle download: {DATASET_EAFC26}"
    )

    csvs = list(raw_dir.glob("*.csv"))
    if csvs:
        print(f"  Encontrados: {[f.name for f in csvs]}")
    else:
        print("  Nenhum CSV encontrado. Verifique o token.")
    return csvs


def coletar_stats_atuais():
    """Coleta stats da temporada atual via FBref (funciona na máquina local)."""
    print("\n[4/4] Coletando stats reais da temporada atual (FBref)...")
    sys.path.insert(0, str(BASE_DIR))

    from src.collectors.fbref import coletar_todas_ligas, salvar_csv

    df = coletar_todas_ligas(temporada="2025-2026")

    if df.empty:
        print("  Aviso: FBref não retornou dados. Verifique a conexão.")
        return None

    caminho = salvar_csv(df, "fbref_stats_2025_2026.csv")
    print(f"  {len(df)} jogadores coletados → {caminho}")
    return df


def popular_banco(csvs_eafc: list[Path], df_real=None):
    """Carrega os dados coletados no banco DuckDB."""
    print("\n[5/5] Populando banco de dados...")
    sys.path.insert(0, str(BASE_DIR))

    from src.collectors.loaders import carregar_eafc_kaggle
    from src.processors.cleaner import limpar_dataframe_fbref
    from src.database.manager import DBManager

    db_path = BASE_DIR / "gestor_ml360.duckdb"
    if db_path.exists():
        db_path.unlink()
        print("  Banco anterior removido")

    with DBManager(db_path) as db:
        # Dados do jogo (EAFC26)
        for csv in csvs_eafc:
            print(f"  Carregando {csv.name}...")
            df = carregar_eafc_kaggle(csv, patch_versao=PATCH_ATUAL)
            db.inserir_jogadores_jogo(df, patch_versao=PATCH_ATUAL)

        # Dados reais
        if df_real is not None and not df_real.empty:
            df_limpo = limpar_dataframe_fbref(df_real)
            db.inserir_jogadores_reais(df_limpo)

        # Resumo
        n_jogo = db.executar_query("SELECT COUNT(*) as n FROM jogadores_jogo")["n"].iloc[0]
        n_real = db.executar_query("SELECT COUNT(*) as n FROM jogadores_reais")["n"].iloc[0]
        print(f"\n  Banco populado com sucesso:")
        print(f"    Jogadores EAFC26 (jogo): {n_jogo:,}")
        print(f"    Stats reais (FBref):     {n_real:,}")

    return db_path


def main():
    print("=" * 55)
    print("  GESTOR ML360 — SETUP INICIAL")
    print("=" * 55)

    instalar_dependencias()
    tem_kaggle = configurar_kaggle()

    csvs_eafc = []
    if tem_kaggle:
        csvs_eafc = baixar_eafc26()

    if not csvs_eafc:
        print("\n  Sem CSV do Kaggle. Usando dados de amostra por enquanto.")
        print("  Para usar dados reais depois:")
        print("    python atualizar_dados.py --csv data/raw/<arquivo>.csv --tipo eafc")
        from src.collectors.sample_data import gerar_dataset_eafc26
        df_sample = gerar_dataset_eafc26()
        sample_path = BASE_DIR / "data" / "raw" / "eafc26_sample.csv"
        df_sample.to_csv(sample_path, index=False)
        csvs_eafc = [sample_path]

    df_real = coletar_stats_atuais()
    db_path = popular_banco(csvs_eafc, df_real)

    print("\n" + "=" * 55)
    print("  Setup concluído!")
    print(f"  Banco: {db_path}")
    print("\n  Próximos passos:")
    print("    jupyter notebook notebooks/01_exploracao_inicial.ipynb")
    print("    python atualizar_dados.py --help")
    print("=" * 55)


if __name__ == "__main__":
    main()
