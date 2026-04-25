"""
Gerador de dados de amostra realistas do EAFC26.
Usado para demonstrar e testar o pipeline sem depender de scraping.
"""
import pandas as pd
import numpy as np


JOGADORES_EAFC26 = [
    # (nome, idade, overall, potencial, posicao, time, liga, nacionalidade, valor_eur)
    ("Kylian Mbappé", 26, 91, 93, "ST", "Real Madrid", "la_liga", "França", 180_000_000),
    ("Erling Haaland", 24, 92, 95, "ST", "Manchester City", "premier_league", "Noruega", 200_000_000),
    ("Vinicius Jr.", 24, 90, 93, "LW", "Real Madrid", "la_liga", "Brasil", 180_000_000),
    ("Rodri", 28, 91, 91, "CDM", "Manchester City", "premier_league", "Espanha", 150_000_000),
    ("Jude Bellingham", 21, 88, 94, "CAM", "Real Madrid", "la_liga", "Inglaterra", 180_000_000),
    ("Bukayo Saka", 23, 87, 92, "RW", "Arsenal", "premier_league", "Inglaterra", 150_000_000),
    ("Lamine Yamal", 17, 82, 95, "RW", "Barcelona", "la_liga", "Espanha", 120_000_000),
    ("Florian Wirtz", 21, 86, 93, "CAM", "Bayer Leverkusen", "bundesliga", "Alemanha", 130_000_000),
    ("Pedri", 22, 87, 92, "CM", "Barcelona", "la_liga", "Espanha", 130_000_000),
    ("Phil Foden", 24, 88, 92, "CAM", "Manchester City", "premier_league", "Inglaterra", 140_000_000),
    ("Raphinha", 27, 84, 86, "RW", "Barcelona", "la_liga", "Brasil", 80_000_000),
    ("Federico Valverde", 26, 86, 89, "CM", "Real Madrid", "la_liga", "Uruguai", 120_000_000),
    ("Gavi", 20, 85, 91, "CM", "Barcelona", "la_liga", "Espanha", 100_000_000),
    ("Endrick", 18, 78, 91, "ST", "Real Madrid", "la_liga", "Brasil", 80_000_000),
    ("Xavi Simons", 22, 83, 91, "CAM", "RB Leipzig", "bundesliga", "Holanda", 80_000_000),
    ("Jamal Musiala", 21, 86, 92, "CAM", "Bayern München", "bundesliga", "Alemanha", 130_000_000),
    ("Leroy Sané", 28, 84, 85, "LW", "Bayern München", "bundesliga", "Alemanha", 60_000_000),
    ("Harry Kane", 31, 90, 90, "ST", "Bayern München", "bundesliga", "Inglaterra", 80_000_000),
    ("Joshua Kimmich", 29, 87, 88, "CDM", "Bayern München", "bundesliga", "Alemanha", 80_000_000),
    ("Thibaut Courtois", 32, 90, 89, "GK", "Real Madrid", "la_liga", "Bélgica", 60_000_000),
    ("Alisson", 32, 89, 88, "GK", "Liverpool", "premier_league", "Brasil", 60_000_000),
    ("Mohamed Salah", 32, 89, 89, "RW", "Liverpool", "premier_league", "Egito", 50_000_000),
    ("Alexis Mac Allister", 26, 84, 87, "CM", "Liverpool", "premier_league", "Argentina", 80_000_000),
    ("Dominik Szoboszlai", 23, 83, 88, "CAM", "Liverpool", "premier_league", "Hungria", 70_000_000),
    ("Gabriel Magalhães", 26, 84, 87, "CB", "Arsenal", "premier_league", "Brasil", 80_000_000),
    ("Declan Rice", 26, 86, 89, "CDM", "Arsenal", "premier_league", "Inglaterra", 100_000_000),
    ("Martin Ødegaard", 26, 87, 89, "CAM", "Arsenal", "premier_league", "Noruega", 120_000_000),
    ("William Saliba", 23, 84, 90, "CB", "Arsenal", "premier_league", "França", 90_000_000),
    ("Marcus Rashford", 27, 83, 85, "LW", "Manchester United", "premier_league", "Inglaterra", 60_000_000),
    ("Bruno Fernandes", 30, 86, 86, "CAM", "Manchester United", "premier_league", "Portugal", 60_000_000),
    ("Cole Palmer", 22, 85, 91, "CAM", "Chelsea", "premier_league", "Inglaterra", 100_000_000),
    ("Nicolas Jackson", 23, 80, 86, "ST", "Chelsea", "premier_league", "Senegal", 60_000_000),
    ("Noni Madueke", 22, 80, 87, "RW", "Chelsea", "premier_league", "Inglaterra", 50_000_000),
    ("Brahim Díaz", 25, 82, 85, "CAM", "Real Madrid", "la_liga", "Espanha", 50_000_000),
    ("Dani Olmo", 26, 84, 87, "CAM", "Barcelona", "la_liga", "Espanha", 70_000_000),
    ("Robert Lewandowski", 36, 87, 85, "ST", "Barcelona", "la_liga", "Polônia", 20_000_000),
    ("Toni Kroos", 34, 87, 85, "CM", "Real Madrid", "la_liga", "Alemanha", 15_000_000),
    ("Frenkie de Jong", 27, 84, 86, "CM", "Barcelona", "la_liga", "Holanda", 70_000_000),
    ("João Félix", 24, 82, 87, "ST", "Chelsea", "premier_league", "Portugal", 60_000_000),
    ("Vitor Roque", 19, 74, 88, "ST", "Betis", "la_liga", "Brasil", 40_000_000),
    ("Warren Zaire-Emery", 18, 78, 91, "CM", "PSG", "ligue_1", "França", 50_000_000),
    ("Bradley Barcola", 22, 81, 88, "LW", "PSG", "ligue_1", "França", 60_000_000),
    ("Ousmane Dembélé", 27, 86, 87, "RW", "PSG", "ligue_1", "França", 60_000_000),
    ("Marco Asensio", 28, 82, 83, "CAM", "PSG", "ligue_1", "Espanha", 25_000_000),
    ("Sandro Tonali", 24, 82, 88, "CM", "Newcastle", "premier_league", "Itália", 70_000_000),
    ("Alexander Isak", 25, 85, 89, "ST", "Newcastle", "premier_league", "Suécia", 100_000_000),
    ("Nicolás González", 26, 80, 83, "LW", "Fiorentina", "serie_a", "Argentina", 35_000_000),
    ("Khvicha Kvaratskhelia", 23, 86, 91, "LW", "PSG", "ligue_1", "Geórgia", 80_000_000),
    ("Victor Osimhen", 25, 87, 89, "ST", "Galatasaray", "la_liga", "Nigéria", 80_000_000),
    ("Ademola Lookman", 26, 83, 86, "LW", "Atalanta", "serie_a", "Nigéria", 60_000_000),
    # Brasileiros
    ("Rodrygo", 23, 85, 90, "RW", "Real Madrid", "la_liga", "Brasil", 100_000_000),
    ("Gabriel Jesus", 27, 82, 83, "ST", "Arsenal", "premier_league", "Brasil", 50_000_000),
    ("Casemiro", 32, 84, 82, "CDM", "Manchester United", "premier_league", "Brasil", 30_000_000),
    ("Richarlison", 27, 82, 84, "ST", "Tottenham", "premier_league", "Brasil", 50_000_000),
    ("Lucas Paquetá", 27, 83, 85, "CAM", "West Ham", "premier_league", "Brasil", 60_000_000),
    ("João Gomes", 23, 78, 84, "CDM", "Wolverhampton", "premier_league", "Brasil", 35_000_000),
    ("Andreas Pereira", 28, 79, 80, "CAM", "Fulham", "premier_league", "Brasil", 20_000_000),
    ("Antony", 24, 78, 82, "RW", "Manchester United", "premier_league", "Brasil", 40_000_000),
]


def gerar_dataset_eafc26(patch: str = "6.0.0") -> pd.DataFrame:
    """Gera DataFrame de amostra com dados realistas do EAFC26."""
    np.random.seed(42)
    registros = []

    for i, (nome, idade, overall, potencial, posicao, time, liga, nac, valor) in enumerate(JOGADORES_EAFC26):
        sofifa_id = f"SFI{200000 + i}"
        registros.append({
            "sofifa_id": sofifa_id,
            "nome": nome,
            "idade": idade,
            "overall": overall,
            "potencial": potencial,
            "posicao": posicao,
            "time": time,
            "liga": liga,
            "nacionalidade": nac,
            "valor_eur": valor,
            "salario_eur": int(valor * np.random.uniform(0.003, 0.008)),
            "ritmo": min(99, overall + np.random.randint(-10, 15)),
            "finalizacao": min(99, overall + np.random.randint(-10, 15)),
            "passe": min(99, overall + np.random.randint(-10, 15)),
            "drible": min(99, overall + np.random.randint(-10, 15)),
            "defesa": min(99, overall + np.random.randint(-20, 5)),
            "fisico": min(99, overall + np.random.randint(-15, 10)),
            "versao_jogo": "EAFC26",
            "patch_versao": patch,
            "nome_normalizado": nome.lower(),
        })

    return pd.DataFrame(registros)


def gerar_stats_reais() -> pd.DataFrame:
    """Gera DataFrame de amostra com stats reais realistas."""
    np.random.seed(99)
    registros = []

    for nome, idade, overall, potencial, posicao, time, liga, _, _ in JOGADORES_EAFC26:
        # Stats aproximados baseados no overall do jogo
        partidas = np.random.randint(20, 38)
        minutos = partidas * np.random.randint(60, 90)
        gols_base = max(0, (overall - 75) / 5) if posicao in ("ST", "LW", "RW", "CAM") else 0
        gols = max(0, int(np.random.normal(gols_base * partidas / 38, 3)))
        assist = max(0, int(np.random.normal(gols_base * 0.7 * partidas / 38, 2)))

        registros.append({
            "nome": nome,
            "nome_normalizado": nome.lower(),
            "time": time,
            "liga": liga,
            "temporada": "2025-2026",
            "partidas": partidas,
            "minutos": minutos,
            "gols": gols,
            "assistencias": assist,
            "xg": round(max(0, np.random.normal(gols * 0.95, 1.5)), 2),
            "xa": round(max(0, np.random.normal(assist * 0.95, 1.0)), 2),
            "xg_por_90": round(max(0, np.random.normal(gols / (minutos / 90), 0.1)), 2) if minutos > 0 else 0,
            "xa_por_90": round(max(0, np.random.normal(assist / (minutos / 90), 0.1)), 2) if minutos > 0 else 0,
            "progressive_carries": np.random.randint(20, 200),
            "progressive_passes": np.random.randint(30, 300),
            "fonte": "sample",
        })

    return pd.DataFrame(registros)
