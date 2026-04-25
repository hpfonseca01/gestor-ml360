"""
Script principal para atualizar a base de dados.
Execute após cada patch/update do EAFC26.

Uso:
    python atualizar_dados.py --sofifa --fbref --patch "6.0.1"
    python atualizar_dados.py --sofifa --patch "6.0.1"  # só jogo
    python atualizar_dados.py --fbref                   # só dados reais
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.sofifa import coletar_jogadores, salvar_csv as salvar_sofifa
from src.collectors.fbref import coletar_todas_ligas, salvar_csv as salvar_fbref
from src.processors.cleaner import limpar_dataframe_sofifa, limpar_dataframe_fbref
from src.database.manager import DBManager


def atualizar_sofifa(db: DBManager, patch: str = None):
    print("\n=== Coletando dados do SoFIFA ===")
    df_raw = coletar_jogadores(paginas=10)
    salvar_sofifa(df_raw, "sofifa_jogadores_raw.csv")

    df_limpo = limpar_dataframe_sofifa(df_raw)
    db.inserir_jogadores_jogo(df_limpo, patch_versao=patch)
    print(f"SoFIFA: {len(df_limpo)} jogadores atualizados.")


def atualizar_fbref(db: DBManager):
    print("\n=== Coletando dados reais (FBref) ===")
    df_raw = coletar_todas_ligas()
    salvar_fbref(df_raw, "fbref_stats_raw.csv")

    df_limpo = limpar_dataframe_fbref(df_raw)
    db.inserir_jogadores_reais(df_limpo)
    print(f"FBref: {len(df_limpo)} registros atualizados.")


def main():
    parser = argparse.ArgumentParser(description="Atualiza a base de dados gestor-ml360")
    parser.add_argument("--sofifa", action="store_true", help="Atualiza dados do EAFC26")
    parser.add_argument("--fbref", action="store_true", help="Atualiza dados reais (FBref)")
    parser.add_argument("--patch", type=str, default=None, help="Versão do patch (ex: 6.0.1)")
    args = parser.parse_args()

    if not args.sofifa and not args.fbref:
        print("Informe pelo menos uma fonte: --sofifa ou --fbref")
        parser.print_help()
        sys.exit(1)

    with DBManager() as db:
        if args.sofifa:
            atualizar_sofifa(db, patch=args.patch)
        if args.fbref:
            atualizar_fbref(db)

    print("\nAtualização concluída.")


if __name__ == "__main__":
    main()
