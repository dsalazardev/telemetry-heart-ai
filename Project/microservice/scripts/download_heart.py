"""Descarga el dataset UCI Heart Disease (Cleveland) a `app/data/heart.csv`.

Dataset clasico de prediccion de enfermedad cardiaca: 13 features + `target`
binario (0 = sin enfermedad, 1 = enfermedad). NOTA: es una tarea BINARIA,
distinta del triaje ordinal de 3 niveles del microservicio; sirve como
baseline/EDA con datos reales, no se integra al flujo de priorizacion.

Uso:
    python scripts/download_heart.py
o desde un notebook:
    from scripts.download_heart import download_heart_dataset
    df = download_heart_dataset()
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

# Ruta de salida canonica (relativa a la raiz del microservicio).
DEFAULT_OUT = Path("app/data/heart.csv")

# Columnas del fichero procesado de Cleveland (sin cabecera en el origen).
COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]

# Mirror oficial UCI del subset procesado de Cleveland.
UCI_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "heart-disease/processed.cleveland.data"
)


def _binarize_target(series: pd.Series) -> pd.Series:
    """num ∈ {0..4} -> 0 (sano) / 1 (enfermedad)."""
    return (pd.to_numeric(series, errors="coerce").fillna(0) > 0).astype(int)


def _from_ucimlrepo() -> pd.DataFrame | None:
    """Intenta via paquete `ucimlrepo` (id=45). None si no esta disponible."""
    try:
        from ucimlrepo import fetch_ucirepo
    except ImportError:
        return None
    try:
        heart = fetch_ucirepo(id=45)
        df = heart.data.features.copy()
        df["target"] = _binarize_target(heart.data.targets.iloc[:, 0])
        return df
    except Exception as exc:  # noqa: BLE001 — caer al fallback por red/formato
        print(f"[warn] ucimlrepo fallo ({exc}); usando descarga directa UCI.")
        return None


def _from_uci_url(url: str = UCI_URL) -> pd.DataFrame:
    """Descarga y parsea el .data crudo de Cleveland."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw), header=None, names=COLUMNS, na_values="?")
    # 'ca' y 'thal' traen faltantes ('?'): imputacion simple por moda.
    for col in ("ca", "thal"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].mode().iloc[0])
    df["target"] = _binarize_target(df["target"])
    return df


def download_heart_dataset(out_path: str | Path = DEFAULT_OUT) -> pd.DataFrame:
    """Descarga el dataset, lo guarda en `out_path` y devuelve el DataFrame.

    Estrategia: `ucimlrepo` (preferido, limpio) -> descarga directa UCI.
    """
    df = _from_ucimlrepo()
    if df is None:
        df = _from_uci_url()

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"[ok] heart.csv guardado en {out} (shape={df.shape})")
    print(f"     columnas: {df.columns.tolist()}")
    print(f"     target (0/1): {df['target'].value_counts().to_dict()}")
    return df


if __name__ == "__main__":
    download_heart_dataset()
