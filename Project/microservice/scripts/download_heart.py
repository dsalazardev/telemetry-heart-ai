import os
import urllib.request
import pandas as pd


def download_heart_dataset(output_dir="./data"):
    """Download heart dataset from UCI repository"""
    os.makedirs(output_dir, exist_ok=True)

    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
    output_path = os.path.join(output_dir, "heart.csv")

    # Column names
    columns = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
    ]

    try:
        # Download
        print(f"Downloading from {url}...")
        urllib.request.urlretrieve(url, output_path)

        # Read and fix
        df = pd.read_csv(output_path, names=columns, na_values="?")
        df = df.dropna()
        df["target"] = df["target"].apply(lambda x: 1 if x > 0 else 0)

        # Save cleaned
        df.to_csv(output_path, index=False)
        print(f"[OK] Dataset saved to {output_path}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return None


if __name__ == "__main__":
    download_heart_dataset()