from pathlib import Path

MAIN_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = MAIN_DIR / "app" / "data"
WEIGHTS_PATH = DATA_DIR / "optimized_weights.json"
