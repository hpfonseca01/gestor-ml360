from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

DB_PATH = BASE_DIR / "gestor_ml360.duckdb"

SOFIFA_BASE_URL = "https://sofifa.com"
SOFIFA_PLAYERS_URL = f"{SOFIFA_BASE_URL}/players"

# Ligas monitoradas (IDs do SoFIFA)
LIGAS = {
    "premier_league": 13,
    "la_liga": 53,
    "bundesliga": 19,
    "serie_a": 31,
    "ligue_1": 16,
    "brasileiro": 83,
}

# Versão atual do jogo (atualizar a cada patch)
GAME_VERSION = "EAFC26"

KAGGLE_DATASET_IDS = [
    "flynn28/eafc26-player-database",
    "rovnez/fc-26-fifa-26-player-data",
]
