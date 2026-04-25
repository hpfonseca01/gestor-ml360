"""
Coletor de dados do SoFIFA.
Extrai ratings, atributos e histórico de upgrades/downgrades dos jogadores.
"""
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm

from config.settings import SOFIFA_PLAYERS_URL, RAW_DIR

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get_page(url: str, params: dict = None) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    time.sleep(1.5)
    return BeautifulSoup(resp.text, "lxml")


def _parse_players_table(soup: BeautifulSoup) -> list[dict]:
    table = soup.find("table", {"id": "player-table"})
    if not table:
        return []

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) < 5:
            continue

        player_tag = cols[1].find("a")
        row = {
            "sofifa_id": player_tag["href"].split("/")[2] if player_tag else None,
            "nome": player_tag.get_text(strip=True) if player_tag else None,
            "idade": cols[2].get_text(strip=True),
            "overall": cols[3].get_text(strip=True),
            "potencial": cols[4].get_text(strip=True),
            "time": cols[5].get_text(strip=True) if len(cols) > 5 else None,
            "posicao": cols[0].get_text(strip=True),
            "valor": cols[6].get_text(strip=True) if len(cols) > 6 else None,
        }
        rows.append(row)
    return rows


def coletar_jogadores(liga_id: int = None, paginas: int = 5) -> pd.DataFrame:
    """
    Coleta jogadores do SoFIFA, opcionalmente filtrando por liga.

    Args:
        liga_id: ID da liga no SoFIFA (None = todas as ligas)
        paginas: número de páginas a coletar (60 jogadores por página)

    Returns:
        DataFrame com os jogadores coletados
    """
    todos = []
    offset = 0

    for _ in tqdm(range(paginas), desc="Coletando páginas SoFIFA"):
        params = {"offset": offset}
        if liga_id:
            params["lg[]"] = liga_id

        soup = _get_page(SOFIFA_PLAYERS_URL, params=params)
        jogadores = _parse_players_table(soup)

        if not jogadores:
            break

        todos.extend(jogadores)
        offset += 60

    df = pd.DataFrame(todos)
    df["overall"] = pd.to_numeric(df["overall"], errors="coerce")
    df["potencial"] = pd.to_numeric(df["potencial"], errors="coerce")
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    return df


def coletar_perfil_jogador(sofifa_id: str) -> dict:
    """
    Coleta o perfil completo de um jogador específico do SoFIFA.

    Args:
        sofifa_id: ID do jogador no SoFIFA

    Returns:
        Dicionário com todos os atributos do jogador
    """
    url = f"https://sofifa.com/player/{sofifa_id}"
    soup = _get_page(url)

    perfil = {"sofifa_id": sofifa_id}

    nome_tag = soup.find("h1")
    if nome_tag:
        perfil["nome"] = nome_tag.get_text(strip=True)

    for section in soup.find_all("div", class_="block-quarter"):
        label = section.find("label")
        value = section.find("span")
        if label and value:
            perfil[label.get_text(strip=True).lower().replace(" ", "_")] = (
                value.get_text(strip=True)
            )

    return perfil


def salvar_csv(df: pd.DataFrame, nome_arquivo: str) -> Path:
    """Salva DataFrame em CSV na pasta data/raw."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RAW_DIR / nome_arquivo
    df.to_csv(caminho, index=False)
    print(f"Salvo em: {caminho}")
    return caminho


if __name__ == "__main__":
    df = coletar_jogadores(paginas=3)
    print(f"Jogadores coletados: {len(df)}")
    salvar_csv(df, "sofifa_jogadores.csv")
