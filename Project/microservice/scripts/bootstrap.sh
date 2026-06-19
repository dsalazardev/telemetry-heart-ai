#!/bin/bash
set -e

echo "🚀 Bootstrap Telemetry Heart AI Microservice"

# 1. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 2. Download dataset
echo "📊 Downloading heart dataset..."
python scripts/download_heart.py

# 3. Run notebooks
echo "📓 Running EDA notebook..."
jupyter nbconvert --to notebook --execute notebooks/01-eda.ipynb --output notebooks/01-eda.ipynb

echo "📓 Running baseline training notebook..."
jupyter nbconvert --to notebook --execute notebooks/02-baseline.ipynb --output notebooks/02-baseline.ipynb

# 4. Bootstrap ChromaDB
echo "🔍 Bootstrapping ChromaDB..."
python scripts/bootstrap_chroma.py

# 5. Run migrations
echo "🗄️ Running Alembic migrations..."
alembic upgrade head

# 6. Start microservice
echo "🌐 Starting microservice..."
echo "Run: python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

echo "✅ Bootstrap complete!"