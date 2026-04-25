"""
Gerenciador do banco de dados DuckDB.
Responsável por criar, popular e consultar as tabelas do projeto.
"""
import duckdb
import pandas as pd
from pathlib import Path
from config.settings import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Colunas com DEFAULT no schema (não precisam ser inseridas explicitamente)
COLUNAS_AUTO = {"data_coleta", "id"}


class DBManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path))
        self._inicializar_schema()

    def _inicializar_schema(self):
        self.conn.execute(SCHEMA_PATH.read_text())

    def _colunas_tabela(self, tabela: str) -> list[str]:
        result = self.conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [tabela],
        ).fetchall()
        return [r[0] for r in result if r[0] not in COLUNAS_AUTO]

    def _filtrar_df(self, df: pd.DataFrame, tabela: str) -> pd.DataFrame:
        colunas_validas = self._colunas_tabela(tabela)
        colunas = [c for c in df.columns if c in colunas_validas]
        return df[colunas].copy() if colunas else df.copy()

    def inserir_jogadores_jogo(self, df: pd.DataFrame, patch_versao: str = None):
        """
        Insere ou atualiza dados dos jogadores do EAFC26.
        Registra histórico de variação de rating automaticamente.
        """
        df = df.copy()
        if patch_versao:
            df["patch_versao"] = patch_versao

        # Registrar histórico de variações antes de atualizar
        for _, row in df.iterrows():
            sofifa_id = row.get("sofifa_id")
            if not sofifa_id:
                continue
            atual = self.conn.execute(
                "SELECT overall FROM jogadores_jogo WHERE sofifa_id = ?", [sofifa_id]
            ).fetchone()
            if atual:
                variacao = int(row.get("overall") or 0) - int(atual[0] or 0)
                self.conn.execute(
                    """
                    INSERT INTO historico_ratings (sofifa_id, overall, potencial, versao_jogo, variacao)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [sofifa_id, row.get("overall"), row.get("potencial"),
                     row.get("versao_jogo"), variacao],
                )

        df_ins = self._filtrar_df(df, "jogadores_jogo")

        # DuckDB upsert: DELETE + INSERT para garantir consistência
        ids = df_ins["sofifa_id"].dropna().tolist()
        if ids:
            placeholders = ", ".join(["?"] * len(ids))
            self.conn.execute(
                f"DELETE FROM jogadores_jogo WHERE sofifa_id IN ({placeholders})", ids
            )

        colunas = ", ".join(df_ins.columns)
        self.conn.execute(
            f"INSERT INTO jogadores_jogo ({colunas}) SELECT {colunas} FROM df_ins"
        )
        print(f"{len(df_ins)} jogadores inseridos/atualizados.")

    def inserir_jogadores_reais(self, df: pd.DataFrame):
        df_ins = self._filtrar_df(df, "jogadores_reais")
        colunas = ", ".join(df_ins.columns)
        self.conn.execute(
            f"INSERT INTO jogadores_reais ({colunas}) SELECT {colunas} FROM df_ins"
        )
        print(f"{len(df_ins)} registros de stats reais inseridos.")

    def buscar_jogadores(
        self,
        nome: str = None,
        liga: str = None,
        overall_min: int = None,
        potencial_min: int = None,
        posicao: str = None,
    ) -> pd.DataFrame:
        """Busca jogadores com filtros opcionais."""
        condicoes = []
        params = []

        if nome:
            condicoes.append("LOWER(nome) LIKE ?")
            params.append(f"%{nome.lower()}%")
        if liga:
            condicoes.append("LOWER(liga) = ?")
            params.append(liga.lower())
        if overall_min:
            condicoes.append("overall >= ?")
            params.append(overall_min)
        if potencial_min:
            condicoes.append("potencial >= ?")
            params.append(potencial_min)
        if posicao:
            condicoes.append("posicao = ?")
            params.append(posicao)

        where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
        return self.conn.execute(
            f"SELECT * FROM jogadores_jogo {where} ORDER BY overall DESC", params
        ).df()

    def historico_jogador(self, sofifa_id: str) -> pd.DataFrame:
        return self.conn.execute(
            "SELECT * FROM historico_ratings WHERE sofifa_id = ? ORDER BY data_registro",
            [sofifa_id],
        ).df()

    def jogadores_com_upgrade(self, min_variacao: int = 1) -> pd.DataFrame:
        return self.conn.execute(
            """
            SELECT h.sofifa_id, j.nome, j.posicao, j.liga, j.time,
                   h.variacao, h.overall, h.data_registro
            FROM historico_ratings h
            JOIN jogadores_jogo j ON h.sofifa_id = j.sofifa_id
            WHERE h.variacao >= ?
            ORDER BY h.variacao DESC, h.data_registro DESC
            """,
            [min_variacao],
        ).df()

    def executar_query(self, sql: str, params: list = None) -> pd.DataFrame:
        return self.conn.execute(sql, params or []).df()

    def fechar(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()
