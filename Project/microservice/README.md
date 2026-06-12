# Telemetry Heart AI - Microservice IA

Microservicio de Inteligencia Artificial para prediccion de riesgo cardiovascular con LangGraph agents, RAG, y metaheuristicas (PSO).

## Stack

- **FastAPI** (puerto 8001) — API REST async
- **SQLModel** + PostgreSQL — Modelos de BD
- **LangGraph** (LangChain v0.3+) — Agentes con StateGraph + InMemorySaver
- **ChromaDB** — Vector store para RAG
- **RiskEngine** — Modelo de riesgo con pesos optimizados por PSO
- **PSO + Genetic** — Metaheuristicas (DEAP + PSO manual)
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
| GET | `/health` | Health check (LLM, embeddings, Chroma, agents) |
| GET | `/ready` | Readiness probe (embeddings real, RAG cargado, pesos cargados) |
| GET | `/metrics/evaluation` | Comparacion baseline vs optimizado |
| POST | `/rag/reindex` | Reindexar documentos clinicos en ChromaDB |
| POST | `/predecir` | Prediccion de riesgo cardiovascular (ClinicalGraph) |
| POST | `/explicar` | Explicacion clinica con LLM + RAG |
| POST | `/evaluar` | Webhook para n8n: recibe telemetria, evalua umbrales, predice |
| POST | `/n8n/webhook` | Igual que /evaluar (alias directo) |
| POST | `/optimize` | Ejecutar PSO para optimizar pesos del RiskEngine |

## Arquitectura

```
app/
  main.py              # FastAPI app, lifespan, auto-descubrimiento de agents
  agents/              # LangGraph agents (StateGraph)
    clinical_subgraph  # Normalizar → RAG → LLM explain → Response
    n8n_subgraph        # Parse payload → Umbrales → Clinical → Fallback → Response
    pso_subgraph        # Load data → PSO optimize → Metrics → Explain → Export
  api/                 # Routers no asociados a agents
    routes_health      # GET /health
    routes_ready       # GET /ready
    routes_metrics     # GET /metrics/evaluation, POST /rag/reindex
  services/
    risk_engine        # Modelo de riesgo con pesos PSO-optimizados
    rag_service        # ChromaDB + embeddings (provider o fallback)
    metrics_service    # Accuracy, recall, F1, false negative rate
    workflow_service   # HTTP client para adapters n8n
    genetic_engine     # DEAP AG: feature selection
    pso_engine         # DEAP PSO manual: hiperparametros
    optimizers/pso     # PSO para optimizar pesos y thresholds
  models/              # SQLModel: Lectura, Prediccion, Evaluacion, Documento, Adapter
  schemas/             # Pydantic: PredictionRequest/Response, AgentQuery, WorkflowTrigger
  providers/           # LLM y Embeddings con auto-registro (openai, lmstudio, huggingface, fake)
  core/                # config, database, dependencies, registry, logging, langsmith
```

## Tests

```bash
pytest tests/ -v              # 33 tests
pytest tests/ -v --tb=short   # Con tracebacks cortos
```
