"""
Gerenciador do banco de dados DuckDB.
Responsável por criar, popular e consultar as tabelas do projeto.
"""
import duckdb
import pandas as pd
from pathlib import Path
from config.settings import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DBManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path))
        self._inicializar_schema()

    def _inicializar_schema(self):
        schema_sql = SCHEMA_PATH.read_text()
        self.conn.execute(schema_sql)

    def inserir_jogadores_jogo(self, df: pd.DataFrame, patch_versao: str = None):
        """
        Insere ou atualiza dados dos jogadores do EAFC26.
        Registra histórico de variação de rating automaticamente.
        """
        df = df.copy()
        if patch_versao:
            df["patch_versao"] = patch_versao

        for _, row in df.iterrows():
            sofifa_id = row.get("sofifa_id")
            if not sofifa_id:
                continue

            atual = self.conn.execute(
                "SELECT overall FROM jogadores_jogo WHERE sofifa_id = ?", [sofifa_id]
            ).fetchone()

            if atual:
                variacao = int(row.get("overall", 0) or 0) - int(atual[0] or 0)
                self.conn.execute(
                    """
                    INSERT INTO historico_ratings (sofifa_id, overall, potencial, versao_jogo, variacao)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [sofifa_id, row.get("overall"), row.get("potencial"),
                     row.get("versao_jogo"), variacao],
                )

        colunas = [c for c in df.columns if c in self._colunas_tabela("jogadores_jogo")]
        df_filtrado = df[colunas] if colunas else df

        self.conn.execute(
            "INSERT OR REPLACE INTO jogadores_jogo SELECT * FROM df_filtrado"
        )
        print(f"{len(df_filtrado)} jogadores inseridos/atualizados.")

    def inserir_jogadores_reais(self, df: pd.DataFrame):
        colunas = [c for c in df.columns if c in self._colunas_tabela("jogadores_reais")]
        df_filtrado = df[colunas] if colunas else df
        self.conn.execute(
            "INSERT INTO jogadores_reais SELECT * FROM df_filtrado"
        )
        print(f"{len(df_filtrado)} registros de stats reais inseridos.")

    def _colunas_tabela(self, tabela: str) -> list[str]:
        result = self.conn.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tabela}'"
        ).fetchall()
        return [r[0] for r in result]

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
        query = f"SELECT * FROM jogadores_jogo {where} ORDER BY overall DESC"

        return self.conn.execute(query, params).df()

    def historico_jogador(self, sofifa_id: str) -> pd.DataFrame:
        return self.conn.execute(
            "SELECT * FROM historico_ratings WHERE sofifa_id = ? ORDER BY data_registro",
            [sofifa_id],
        ).df()

    def jogadores_com_upgrade(self, min_variacao: int = 1) -> pd.DataFrame:
        """Retorna jogadores que tiveram upgrade recente."""
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
