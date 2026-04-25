"""
Script principal para atualizar a base de dados.

Modos de uso:

  # 1. Carregar CSV do Kaggle (EAFC26) que você baixou manualmente
  python atualizar_dados.py --csv data/raw/fc26_players.csv --tipo eafc --patch "6.0.1"

  # 2. Carregar CSV do FBref que você exportou manualmente
  python atualizar_dados.py --csv data/raw/fbref_premier_league.csv --tipo fbref --liga premier_league

  # 3. Carregar VÁRIOS CSVs de uma pasta
  python atualizar_dados.py --pasta data/raw/ --patch "6.0.1"

  # 4. Scraping direto (só funciona rodando localmente, não em servidor)
  python atualizar_dados.py --scrape-sofifa --patch "6.0.1"
  python atualizar_dados.py --scrape-fbref
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.loaders import carregar_eafc_kaggle, carregar_fbref_csv, detectar_formato
from src.database.manager import DBManager


def carregar_csv(db: DBManager, caminho: Path, tipo: str = None, liga: str = None, patch: str = None):
    if tipo is None:
        tipo = detectar_formato(caminho)
        print(f"Formato detectado automaticamente: {tipo}")

    if tipo == "eafc" or tipo == "kaggle_eafc":
        df = carregar_eafc_kaggle(caminho, patch_versao=patch)
        db.inserir_jogadores_jogo(df, patch_versao=patch)

    elif tipo == "fbref":
        df = carregar_fbref_csv(caminho, liga=liga)
        db.inserir_jogadores_reais(df)

    else:
        print(f"Formato desconhecido para {caminho.name}. Use --tipo eafc ou --tipo fbref")


def carregar_pasta(db: DBManager, pasta: Path, patch: str = None):
    csvs = list(pasta.glob("*.csv"))
    if not csvs:
        print(f"Nenhum CSV encontrado em {pasta}")
        return

    print(f"{len(csvs)} CSVs encontrados em {pasta}")
    for csv in csvs:
        print(f"\nProcessando: {csv.name}")
        tipo = detectar_formato(csv)
        liga = _inferir_liga_do_nome(csv.name)
        carregar_csv(db, csv, tipo=tipo, liga=liga, patch=patch)


def _inferir_liga_do_nome(nome: str) -> str | None:
    nome = nome.lower()
    mapa = {
        "premier":      "premier_league",
        "laliga":       "la_liga",
        "la_liga":      "la_liga",
        "bundesliga":   "bundesliga",
        "serie_a":      "serie_a",
        "seriea":       "serie_a",
        "ligue":        "ligue_1",
        "brasileiro":   "brasileiro",
    }
    for chave, liga in mapa.items():
        if chave in nome:
            return liga
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza a base de dados gestor-ml360",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--csv",   type=Path, help="Path de um CSV específico para carregar")
    parser.add_argument("--pasta", type=Path, help="Pasta com vários CSVs para carregar")
    parser.add_argument("--tipo",  choices=["eafc", "fbref"], help="Formato do CSV (detectado auto se omitido)")
    parser.add_argument("--liga",  type=str, help="Liga (ex: premier_league) — necessário para CSVs FBref")
    parser.add_argument("--patch", type=str, default=None, help="Versão do patch (ex: 6.0.1)")

    # Opções de scraping (só funcionam localmente)
    parser.add_argument("--scrape-sofifa", action="store_true", help="Scraping do SoFIFA (requer execução local)")
    parser.add_argument("--scrape-fbref",  action="store_true", help="Scraping do FBref (requer execução local)")

    args = parser.parse_args()

    if not any([args.csv, args.pasta, args.scrape_sofifa, args.scrape_fbref]):
        parser.print_help()
        sys.exit(1)

    with DBManager() as db:
        if args.csv:
            carregar_csv(db, args.csv, tipo=args.tipo, liga=args.liga, patch=args.patch)

        if args.pasta:
            carregar_pasta(db, args.pasta, patch=args.patch)

        if args.scrape_sofifa:
            from src.collectors.sofifa import coletar_jogadores, salvar_csv
            from src.processors.cleaner import limpar_dataframe_sofifa
            df = coletar_jogadores(paginas=10)
            salvar_csv(df, "sofifa_jogadores_raw.csv")
            df = limpar_dataframe_sofifa(df)
            db.inserir_jogadores_jogo(df, patch_versao=args.patch)

        if args.scrape_fbref:
            from src.collectors.fbref import coletar_todas_ligas, salvar_csv
            from src.processors.cleaner import limpar_dataframe_fbref
            df = coletar_todas_ligas()
            salvar_csv(df, "fbref_stats_raw.csv")
            df = limpar_dataframe_fbref(df)
            db.inserir_jogadores_reais(df)

    print("\nConcluído.")


if __name__ == "__main__":
    main()
