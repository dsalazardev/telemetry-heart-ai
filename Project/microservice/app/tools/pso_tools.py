"""LangChain @tool que envuelve la ejecución offline de PSO.

Este tool es la única superficie que corre el optimizador (no se invoca en
`/predecir`; se usa desde LangGraph Studio, scripts de evaluación o admin
para regenerar `optimized_weights.json` y `convergence_curve.json`).
"""
from __future__ import annotations

import json
from logging import getLogger
from pathlib import Path

import numpy as np
import pandas as pd
from langchain_core.tools import tool

from app.services.optimizers.pso import PSOOptimizer
from app.services.triage_priority_service import build_feature_bundle

logger = getLogger(__name__)

DEFAULT_CSV = Path("app/data/synthetic_cases.csv")
DEFAULT_WEIGHTS_PATH = Path("app/data/triage_priority_weights.json")
DEFAULT_CURVE_PATH = Path("app/data/convergence_curve.json")

FEATURE_COLUMNS = [
    "heart_rate",
    "spo2",
    "systolic_bp",
    "cholesterol",
    "chest_pain",
    "age",
    "other_risk_factors",
]


def _load_dataset(
    csv_path: Path = DEFAULT_CSV,
) -> tuple[np.ndarray, np.ndarray]:
    """Carga el dataset sintético. Devuelve (X, y_priority).

    Se espera una columna `true_priority` ∈ {0,1,2}. Si no existe, se
    deriva de `risk_level` legacy (bajo=0, medio=1, alto=2).
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset no encontrado: {csv_path}")

    df = pd.read_csv(csv_path)

    if "true_priority" in df.columns:
        # Clamp defensivo: datasets legacy 4-niveles colapsan CRÍTICA→ALTA.
        y = df["true_priority"].astype(int).clip(upper=2).to_numpy()
    elif "risk_level" in df.columns:
        mapping = {"bajo": 0, "medio": 1, "alto": 2}
        y = df["risk_level"].map(mapping).fillna(0).astype(int).to_numpy()
    else:
        raise ValueError(
            "Dataset no contiene `true_priority` ni `risk_level`; no se puede entrenar PSO"
        )

    # Columnas crudas que alimentan la normalización canónica de runtime.
    raw_cols = [
        "heart_rate", "spo2", "systolic_bp", "cholesterol",
        "chest_pain", "age", "smoker", "previous_condition",
    ]
    missing = [col for col in raw_cols if col not in df.columns]
    if missing:
        logger.warning(
            "Dataset %s sin columnas crudas %s; se rellenan con 0.0. "
            "Verifica que el CSV tenga las features esperadas: %s",
            csv_path,
            missing,
            raw_cols,
        )
        for col in missing:
            df[col] = 0.0

    # Normalizar EXACTAMENTE como runtime (`build_feature_bundle`): escala
    # clínica a [0, 1] + inversión de spo2. Sin esto, el PSO entrena sobre
    # features crudas que se saturan al clip y los pesos no transfieren a
    # inferencia (train/serve skew).
    try:
        X = np.array(
            [
                build_feature_bundle(
                    heart_rate=float(row["heart_rate"]),
                    spo2=float(row["spo2"]),
                    systolic_bp=float(row["systolic_bp"]),
                    cholesterol=float(row["cholesterol"]),
                    chest_pain=float(row["chest_pain"]),
                    age=float(row["age"]),
                    smoker=bool(row["smoker"]),
                    previous_condition=bool(row["previous_condition"]),
                ).as_array()
                for _, row in df.iterrows()
            ],
            dtype=float,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"No se pudieron normalizar las features en {csv_path}: {exc}"
        ) from exc
    return X, y


def _persist(
    result_dict: dict,
    weights_path: Path = DEFAULT_WEIGHTS_PATH,
    curve_path: Path = DEFAULT_CURVE_PATH,
) -> None:
    weights_path.parent.mkdir(parents=True, exist_ok=True)

    weights_payload = {
        "weights": result_dict["weights"],
        "thresholds": result_dict["priority_thresholds"],
        "feature_weights_dict": result_dict.get("feature_weights_dict", {}),
        "version": result_dict.get("version", "pso-unknown"),
        "algorithm": result_dict.get("algorithm", "PSO"),
        "metrics": result_dict.get("metrics", {}),
    }
    weights_path.write_text(json.dumps(weights_payload, indent=2), encoding="utf-8")
    logger.info("Pesos PSO persistidos en %s", weights_path)

    curve_payload = {
        "convergence_curve": result_dict.get("convergence_curve", []),
        "version": result_dict.get("version", "pso-unknown"),
        "n_iterations": result_dict.get("n_generations", 0),
    }
    curve_path.write_text(json.dumps(curve_payload, indent=2), encoding="utf-8")
    logger.info("Curva de convergencia persistida en %s", curve_path)


@tool
def optimize_triage_priority_tool(
    n_particles: int = 30,
    iterations: int = 50,
    csv_path: str = "app/data/synthetic_cases.csv",
    weights_path: str = "app/data/triage_priority_weights.json",
    curve_path: str = "app/data/convergence_curve.json",
) -> dict:
    """Optimiza pesos+umbrales de priorización cardiovascular con PSO.

    Codificación: 7 pesos clínicos + 2 umbrales (t_medium, t_high).
    Función objetivo: ordinal_error + 3·top_FN + 0.5·overtriage.

    Persiste el resultado en `triage_priority_weights.json` y la curva de
    convergencia en `convergence_curve.json`. Devuelve el OptimizerResult completo con
    métricas (accuracy, critical_recall, fitness) y la curva de fitness por
    iteración.

    Args:
        n_particles: número de partículas del enjambre (default 30).
        iterations: iteraciones del optimizador (default 50).
        csv_path: ruta al dataset sintético etiquetado.
        weights_path: destino de los pesos optimizados.
        curve_path: destino de la curva de convergencia.

    Returns:
        Dict con `weights`, `thresholds`, `convergence_curve`, `metrics`,
        `best_fitness`, `runtime_ms`, `version`.
    """
    X, y = _load_dataset(Path(csv_path))
    optimizer = PSOOptimizer(n_particles=n_particles, max_iter=iterations)
    result = optimizer.optimize(X, y)
    result_dict = result.model_dump()
    _persist(result_dict, Path(weights_path), Path(curve_path))
    return result_dict
