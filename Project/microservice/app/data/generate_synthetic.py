import numpy as np
import pandas as pd

# 3 niveles de prioridad: 0=BAJA, 1=MEDIA, 2=ALTA. Los pacientes en estado
# crítico se modelan como el extremo superior de ALTA (mismo nivel 2).
N_LOW = 250
N_MEDIUM = 120
N_HIGH = 80
N_CRITICAL = 50
N_SAMPLES = N_LOW + N_MEDIUM + N_HIGH + N_CRITICAL

np.random.seed(42)

CHEST_PAIN_MAP = {
    "typical_angina": 1,
    "atypical_angina": 2,
    "non_anginal": 3,
    "asymptomatic": 4,
}


def _make_patients(n, priority, hr_range, spo2_range, sbp_range, dbp_range,
                   chol_range, glu_range, age_range, p_smoker, p_prev, chest_dist):
    n_ = int(n)
    chest_types = list(CHEST_PAIN_MAP.keys())
    return {
        "heart_rate": np.random.uniform(*hr_range, n_),
        "spo2": np.random.uniform(*spo2_range, n_),
        "systolic_bp": np.random.uniform(*sbp_range, n_),
        "diastolic_bp": np.random.uniform(*dbp_range, n_),
        "cholesterol": np.random.uniform(*chol_range, n_),
        "glucose": np.random.uniform(*glu_range, n_),
        "age": np.random.uniform(*age_range, n_),
        "sex": np.random.choice(["M", "F"], n_, p=[0.5, 0.5]),
        "smoker": np.random.choice([0, 1], n_, p=[1 - p_smoker, p_smoker]),
        "previous_condition": np.random.choice([0, 1], n_, p=[1 - p_prev, p_prev]),
        "chest_pain_type": np.random.choice(chest_types, n_, p=chest_dist),
        "true_priority": np.full(n_, priority),
    }


low = pd.DataFrame(_make_patients(
    N_LOW, priority=0,
    hr_range=(60, 95), spo2_range=(95, 100),
    sbp_range=(100, 135), dbp_range=(60, 90),
    chol_range=(120, 200), glu_range=(70, 140), age_range=(20, 55),
    p_smoker=0.2, p_prev=0.1,
    chest_dist=[0.4, 0.4, 0.15, 0.05],
))

medium = pd.DataFrame(_make_patients(
    N_MEDIUM, priority=1,
    hr_range=(90, 140), spo2_range=(90, 98),
    sbp_range=(130, 170), dbp_range=(85, 110),
    chol_range=(180, 280), glu_range=(120, 200), age_range=(40, 70),
    p_smoker=0.4, p_prev=0.3,
    chest_dist=[0.2, 0.3, 0.3, 0.2],
))

high = pd.DataFrame(_make_patients(
    N_HIGH, priority=2,
    hr_range=(120, 175), spo2_range=(85, 93),
    sbp_range=(150, 195), dbp_range=(95, 125),
    chol_range=(220, 340), glu_range=(150, 280), age_range=(55, 80),
    p_smoker=0.55, p_prev=0.45,
    chest_dist=[0.05, 0.15, 0.35, 0.45],
))

critical = pd.DataFrame(_make_patients(
    N_CRITICAL, priority=2,
    hr_range=(150, 200), spo2_range=(70, 85),
    sbp_range=(180, 240), dbp_range=(115, 150),
    chol_range=(300, 400), glu_range=(220, 350), age_range=(60, 90),
    p_smoker=0.7, p_prev=0.7,
    chest_dist=[0.02, 0.08, 0.25, 0.65],
))

df = pd.concat([low, medium, high, critical], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Columnas numéricas que consume PSO (FEATURE_COLUMNS en app/tools/pso_tools.py)
df["chest_pain"] = df["chest_pain_type"].map(CHEST_PAIN_MAP).astype(int)
df["other_risk_factors"] = (df["smoker"] + df["previous_condition"]) / 2.0

# Compatibilidad legacy (notebooks que usan label/risk_level de 3 niveles)
df["label"] = df["true_priority"]
df["risk_level"] = df["label"].map({0: "bajo", 1: "medio", 2: "alto"})

df.to_csv("app/data/synthetic_cases.csv", index=False)

print(f"Generados {len(df)} registros sintéticos")
print(df["true_priority"].value_counts().sort_index())
