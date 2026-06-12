import numpy as np
import pandas as pd

N_SAMPLES = 500
N_HIGH = 80
N_MEDIUM = 120
N_LOW = N_SAMPLES - N_HIGH - N_MEDIUM

np.random.seed(42)


def _make_patients(n, hr_range, spo2_range, sbp_range, dbp_range, chol_range, glu_range, age_range, p_smoker, p_prev, chest_dist):
    n_ = int(n)
    chest_types = ["typical_angina", "atypical_angina", "non_anginal", "asymptomatic"]
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
        "label": np.full(n_, 0 if n_ == N_LOW else (1 if n_ == N_MEDIUM else 2)),
    }


def _to_df(data_dict, label):
    df = pd.DataFrame(data_dict)
    df["label"] = label
    return df


low = pd.DataFrame(_make_patients(
    N_LOW,
    hr_range=(60, 95),
    spo2_range=(95, 100),
    sbp_range=(100, 135),
    dbp_range=(60, 90),
    chol_range=(120, 200),
    glu_range=(70, 140),
    age_range=(20, 55),
    p_smoker=0.2,
    p_prev=0.1,
    chest_dist=[0.4, 0.4, 0.15, 0.05],
))

medium = pd.DataFrame(_make_patients(
    N_MEDIUM,
    hr_range=(90, 140),
    spo2_range=(90, 98),
    sbp_range=(130, 170),
    dbp_range=(85, 110),
    chol_range=(180, 280),
    glu_range=(120, 200),
    age_range=(40, 70),
    p_smoker=0.4,
    p_prev=0.3,
    chest_dist=[0.2, 0.3, 0.3, 0.2],
))

high = pd.DataFrame(_make_patients(
    N_HIGH,
    hr_range=(120, 190),
    spo2_range=(80, 93),
    sbp_range=(150, 220),
    dbp_range=(95, 140),
    chol_range=(220, 380),
    glu_range=(150, 320),
    age_range=(55, 85),
    p_smoker=0.6,
    p_prev=0.5,
    chest_dist=[0.05, 0.15, 0.3, 0.5],
))

df = pd.concat([low, medium, high], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df["risk_level"] = df["label"].map({0: "bajo", 1: "medio", 2: "alto"})
df.to_csv("app/data/synthetic_cases.csv", index=False)

print(f"Generados {len(df)} registros sintéticos")
print(df["risk_level"].value_counts())
