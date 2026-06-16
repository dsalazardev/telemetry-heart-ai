# Telemetry Heart AI - Microservice IA

Microservicio de Inteligencia Artificial para prediccion de riesgo cardiovascular con LangGraph agents, RAG, y metaheuristicas (PSO).

## Stack

- **FastAPI** (puerto 8001) — API REST async
- **SQLModel** + PostgreSQL — Modelos de BD
- **LangGraph** (LangChain v0.3+) — Agentes con StateGraph
- **ChromaDB** — Vector store para RAG
- **RiskEngine / TriagePriorityService** — Modelos de riesgo y prioridad (este último con pesos PSO)
- **PSO** — Metaheuristica propia para optimizar pesos+umbrales de prioridad
- **LangSmith** — Tracing opcional

## Setup

```bash
cd Project/microservice
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales reales
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Info basica del servicio |
| GET | `/health` | Health check (LLM, embeddings, Chroma, agents) |
| GET | `/ready` | Readiness probe (embeddings real, RAG cargado, pesos cargados) |
| GET | `/metrics/evaluation` | Comparacion baseline vs optimizado |
| GET | `/metrics/convergence` | Curva de convergencia de la ultima corrida PSO |
| POST | `/optimize` | Persiste pesos+umbrales PSO ya calculados y recarga el priority service (NO ejecuta PSO; auth Bearer interno) |
| POST | `/predecir` | Prediccion de riesgo cardiovascular (ClinicalGraph; auth Bearer interno) |
| POST | `/explicar` | Explicacion clinica con LLM + RAG (auth Bearer interno) |

> El optimizador PSO se ejecuta offline vía el `@tool optimize_triage_priority_tool`
> (`app/tools/pso_tools.py`), no desde un endpoint HTTP. El resultado se ingiere con `POST /optimize`.

## Arquitectura

```
app/
  main.py                       # FastAPI app, lifespan, auto-descubrimiento de agents
  agents/                       # LangGraph agents (StateGraph)
    clinical_subgraph           # Normalizar → priorizar → RAG → LLM explain → Response
                                #   expone POST /predecir y POST /explicar
  api/                          # Routers no asociados a agents
    routes_health               # GET /health
    routes_ready                # GET /ready
    routes_metrics              # GET /metrics/evaluation, GET /metrics/convergence
    routes_optimize             # POST /optimize (persiste pesos PSO)
  services/
    risk_engine                 # Modelo de riesgo 11-pesos, 3 niveles (bajo/medio/alto)
    triage_priority_service     # Clasificador PSO 7-pesos + 2 umbrales, 3 niveles
    rag_service                 # ChromaDB + embeddings (provider o fallback)
    metrics_service             # Accuracy, recall, F1, critical_recall, fitness
    optimizers/pso              # PSO para optimizar pesos y thresholds (offline)
  tools/pso_tools               # @tool optimize_triage_priority_tool (ejecuta PSO offline)
  schemas/                      # Pydantic: PredictionRequest/Response, OptimizeUpload, Metrics
  providers/                    # LLM y Embeddings con auto-registro (openai, lmstudio, huggingface, fake)
  core/                         # config, dependencies, registry, logging, langsmith
```

> **Dos esquemas de pesos distintos** (no confundir): `RiskEngine` usa 11 pesos
> (`optimized_weights.json`) y produce 3 niveles via sigmoid; `TriagePriorityService` usa
> 7 pesos + 2 umbrales optimizados por PSO (`triage_priority_weights.json`) y produce 3 niveles
> de prioridad (BAJA/MEDIA/ALTA).

## Tests

```bash
pytest tests/ -v              # Suite de tests
pytest tests/ -v --tb=short   # Con tracebacks cortos
```
