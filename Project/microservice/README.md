# Telemetry Heart AI - Microservice IA

Microservicio de Inteligencia Artificial para predicción de riesgo cardiovascular.

## Stack

- FastAPI (puerto 8001)
- SQLModel + PostgreSQL
- LangChain (Agente ReAct)
- ChromaDB + SentenceTransformer
- RandomForest + DEAP

## Setup

```bash
cd Project/microservice
pip install -r requirements.txt
# Create .env from .env.example
cp .env.example .env
# Edit .env with your credentials
# Run migrations
alembic upgrade head
# Start service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Endpoints

- POST /predict - Predicción de riesgo
- POST /evaluar - Evaluación de triaje
- POST /agent/query - Agente conversacional
- POST /agent/train - Entrenamiento
- POST /workflow/trigger - Workflow
- GET /health - Health check
