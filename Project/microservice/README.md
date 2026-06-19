# Microservicio IA — Telemetry Heart AI

Predicción de riesgo cardiovascular, priorización de triaje y explicación clínica con un agente LangGraph, RAG sobre ChromaDB y optimización metaheurística (PSO).

## Stack

| Componente | Tecnología | Propósito |
|-----------|-----------|---------|
| Framework web | FastAPI | API REST async (puerto 8001) |
| Agente | LangGraph (LangChain v0.3+) | `ClinicalGraph` — 1 solo agente con `StateGraph` |
| LLM | OpenAI (gpt-4o-mini) / LM Studio | Vía provider registry (`ChatOpenAI`) |
| Vector store | ChromaDB (`PersistentClient`) | RAG con 26 guías clínicas + embeddings |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (384d) | Vía provider (alternativa: OpenAI) |
| Riesgo | `RiskEngine` | 11 pesos, sigmoid, 3 niveles (bajo/medio/alto) |
| Prioridad | `TriagePriorityService` | 7 pesos + 2 umbrales, 3 niveles (PSO o ML RandomForest) |
| Metaheurística | PSO propio (NumPy/Pandas) | Optimiza pesos+umbrales de prioridad (offline) |
| ML alternativo | `MLPriorityService` | RandomForest (`model.pkl`), accuracy 0.99 |
| Tracing | LangSmith | `LANGCHAIN_TRACING_V2=true` (opcional) |
| Testing | pytest + pytest-asyncio | 47 tests |
| Settings | pydantic-settings | `.env` → `Settings` |

> **Nota de persistencia:** el microservicio **no define modelos SQLModel ni migraciones Alembic propias**. La única persistencia activa es ChromaDB (`app/vectorstore/chroma/`) y archivos JSON de pesos/curva (`app/data/`). No se usa `alembic upgrade head`.

## Setup

```bash
cd Project/microservice
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales reales
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | — | Info básica del servicio |
| GET | `/health` | — | Estado de LLM, embeddings, ChromaDB, agents, LangSmith |
| GET | `/ready` | — | Readiness: 503 si embeddings fake, RAG no cargado o pesos faltan |
| POST | `/predecir` | Bearer interno | Predicción de riesgo + priorización + RAG + explicación LLM |
| POST | `/explicar` | Bearer interno | Pregunta del médico + contexto → respuesta LLM con evidencia |
| POST | `/optimize` | Bearer interno | Persiste pesos+umbrales PSO ya calculados (NO ejecuta PSO) |
| GET | `/metrics/evaluation` | — | Comparación baseline vs. optimizado |
| GET | `/metrics/convergence` | — | Curva de convergencia de la última corrida PSO |
| POST | `/rag/documents` | Bearer interno | Indexa documento clínico en ChromaDB |
| POST | `/rag/documents/bulk` | Bearer interno | Indexación masiva |
| GET | `/rag/documents` | Bearer interno | Lista documentos indexados (paginado) |
| GET | `/rag/documents/{id}` | Bearer interno | Detalle de un documento |
| PUT | `/rag/documents/{id}` | Bearer interno | Actualiza documento (re-embebe si cambia contenido) |
| DELETE | `/rag/documents/{id}` | Bearer interno | Elimina documento y sus chunks |
| POST | `/rag/reindex` | Bearer interno | Reconstruye índice desde `clinical_docs/*.md` |

> **Autenticación:** endpoints sensibles exigen `Authorization: Bearer <internal_token>`. El token se configura en `.env` y debe coincidir con el `INTERNAL_TOKEN` del backend.
>
> **PSO offline:** el optimizador se ejecuta vía `@tool optimize_triage_priority_tool` (`app/tools/pso_tools.py`) o scripts, no desde HTTP. `POST /optimize` solo persiste resultados ya calculados.

### Ejemplos rápidos

```bash
# Predecir riesgo (caso bajo)
curl -s -X POST http://localhost:8001/predecir \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"paciente_id":1,"heart_rate":72,"spo2":98,"systolic_bp":118,"diastolic_bp":76,"age":35,"sex":"F","explain":true}'

# Predecir riesgo (caso alto)
curl -s -X POST http://localhost:8001/predecir \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"paciente_id":3,"heart_rate":160,"spo2":82,"systolic_bp":200,"diastolic_bp":120,"cholesterol":300,"glucose":250,"age":72,"sex":"M","chest_pain_type":"asymptomatic","smoker":true,"previous_condition":true,"explain":true}'

# Pregunta del médico
curl -s -X POST http://localhost:8001/explicar \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Por qué este paciente tiene riesgo alto?","prediction_context":{"risk_score":0.82,"risk_level":"alto","dominant_factors":["taquicardia","hipoxemia"]}}'

# Health + métricas
curl http://localhost:8001/health | python -m json.tool
curl http://localhost:8001/metrics/evaluation | python -m json.tool

# Indexar documento en RAG
curl -s -X POST http://localhost:8001/rag/documents \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Guía HTA","contenido":"La hipertensión arterial se define como...","fuente":"ESC 2024"}'
```

## Arquitectura

```
app/
  main.py                       # FastAPI app, lifespan, registro de routers
  studio.py                     # Bootstrap para LangGraph Studio
  agents/
    __init__.py                  # load_agents() desde manifest.yaml + inyección de deps
    base.py                      # BaseAgent ABC
    clinical_subgraph.py         # ClinicalGraph: predict → prioritize → RAG → explain → response
    manifest.yaml                # Registro: solo 'clinical' habilitado
  api/
    routes_health.py             # GET /health
    routes_ready.py              # GET /ready
    routes_metrics.py            # GET /metrics/evaluation, GET /metrics/convergence
    routes_optimize.py           # POST /optimize
    routes_rag.py                # CRUD /rag/* + /rag/reindex
  core/
    config.py                    # Settings (pydantic-settings)
    dependencies.py              # get_services, verify_internal_token (Bearer)
    registry.py                  # ProviderRegistry (LLM y embeddings)
    resolver.py                  # create_llm(), create_embeddings()
    langgraph_state.py           # ClinicalState (TypedDict)
    langsmith.py                 # Cliente LangSmith
    logging.py                   # setup_logging()
  providers/
    llm_openai.py                # ChatOpenAI (gpt-4o-mini)
    llm_lmstudio.py              # ChatOpenAI con base_url local
    embeddings_openai.py         # OpenAIEmbeddings
    embeddings_huggingface.py    # HuggingFaceEmbeddings (all-MiniLM-L6-v2)
    embeddings_fake.py           # FakeEmbeddings (solo dev; bloqueado en prod)
  schemas/
    prediction.py                # PredictionRequest, PredictionResponse
    explanation.py               # ClinicalExplanation, EvidenceSource, ExplainRequest/Response
    metrics.py                   # MetricsRow, MetricsComparison
    optimize.py                  # OptimizeUploadRequest/Response
    rag.py                       # RagDocumentRequest/Update/Summary, RagBulk*, RagList*, RagReindex*
  services/
    __init__.py                  # Services: orquesta RiskEngine, RAG, TriagePriorityService, LLM, agents
    risk_engine.py               # Modelo de riesgo 11-pesos, sigmoid, 3 niveles
    triage_priority_service.py   # Clasificador 7-pesos + 2 umbrales (PSO | ML)
    ml_priority_service.py       # RandomForest alternativo (model.pkl, PRIORITY_STRATEGY=ml)
    rag_service.py               # ChromaDB + embeddings via provider
    metrics_service.py           # accuracy, recall, F1, critical_recall, fitness
    optimizers/
      base.py                    # BaseOptimizer ABC + OptimizerResult
      pso.py                     # PSOOptimizer (pesos + thresholds)
  tools/
    pso_tools.py                 # @tool optimize_triage_priority_tool (ejecuta PSO offline)
  config/
    clinical_params.yaml         # Thresholds clínicos, features, fallback
  data/
    clinical_docs/               # 26 guías clínicas .md para RAG
    fixtures/                    # Payloads de ejemplo (casos, telemetría, pregunta médico)
    charts/                      # Gráficas N3 (convergencia, pesos PSO)
    synthetic_cases.csv          # Dataset sintético para PSO
    optimized_weights.json       # Pesos del RiskEngine (11)
    triage_priority_weights.json # Pesos + umbrales PSO (pso-2026-06-demo)
    convergence_curve.json       # Curva de convergencia PSO
    model.pkl                    # RandomForest entrenado (ML priority)
    heart.csv                    # UCI Heart Disease dataset
  vectorstore/chroma/            # Persistencia ChromaDB del índice RAG

tests/                           # 47 tests pytest async
  test_agent.py                  # ClinicalGraph: estructura, rutas
  test_prediction.py             # RiskEngine: casos sano/crítico
  test_rag.py                    # RAGService: inicialización, retrieval
  test_health.py                 # Endpoint /health
  test_manifest.py               # Carga de manifest.yaml
  test_metrics_optimize.py       # Métricas y POST /optimize
  test_ml_priority.py            # MLPriorityService
  test_pso_and_validation.py     # PSO optimizer + validación
  test_triage_priority.py        # TriagePriorityService
notebooks/                       # 01-eda, 02-baseline, 03-metaheuristics, 04-rag-evaluation, 05-metrics-n3
scripts/                         # download_heart.py, smoke_studio.py
```

> **Dos esquemas de pesos distintos (no confundir):**
> - `RiskEngine` → **11 pesos** (`optimized_weights.json`), sigmoid, produce `risk_level` ∈ {bajo, medio, alto}.
> - `TriagePriorityService` → **7 pesos + 2 umbrales** (`triage_priority_weights.json`), produce `priority` ∈ {BAJA, MEDIA, ALTA}.
>
> Configuración actual: `PRIORITY_STRATEGY=ml` (RandomForest). Alternar a PSO cambiando la variable de entorno.

## Flujo del agente ClinicalGraph

```
PredictionRequest (heart_rate, spo2, systolic_bp, age, sex, ...)
  │
  ▼
normalize_and_predict   → RiskEngine.predict() → risk_score, risk_level, dominant_factors
  │
  ▼
prioritize              → TriagePriorityService.classify() → priority, priority_score
  │
  ▼
_should_explain = request.explain?
  ├── No ──────────────────────────────────────────────┐
  └── Sí                                                │
      ▼                                                  │
      retrieve_rag  → ChromaDB.query(dominant_factors)   │
      ▼                                                  │
      explain      → CLINICAL_PROMPT | LLM → ClinicalExplanation
      │                                                  │
      ▼                                                  ▼
format_response → PredictionResponse (riesgo + prioridad + explicación + RAG + modelo)
```

## Tests

```bash
pytest tests/ -v              # Suite completa (47 tests)
pytest tests/ -v --tb=short   # Con tracebacks cortos
pytest tests/ -q              # Modo silencioso
```

## LangGraph Studio (desarrollo visual)

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev   # http://127.0.0.1:2024
```

El Agent Server (puerto 2024) coexiste con uvicorn (puerto 8001).

## Variables de entorno clave

| Variable | Valor actual | Descripción |
|----------|-------------|-------------|
| `llm_provider` | `openai` | Proveedor LLM (openai / lmstudio) |
| `llm_model` | `gpt-4o-mini` | Modelo LLM |
| `embedding_provider` | `huggingface` | Proveedor embeddings |
| `internal_token` | `dev-token-cambiar-en-prod` | Token Bearer para auth interna |
| `PRIORITY_STRATEGY` | `ml` | Estrategia de prioridad (ml / pso) |
| `langsmith_api_key` | `lsv2_pt_...` | API key de LangSmith |
| `langsmith_project` | `telemetry-heart-ai` | Proyecto en LangSmith |
| `langsmith_trace_v2` | `true` | Activar tracing |

## Contrato con el backend

El backend (`app/services/microservice_client.py`) consume:

- `POST /predecir` → `PredictionRequest` → `PredictionResponse`
  - `risk_level` → `TriajeCreate.nivelUrgencia`
  - `risk_score` → `TriajeCreate.probabilidadRiesgo`
  - `dominant_factors` → `TriajeCreate.factoresCriticos`
  - `clinical_explanation` → `TriajeCreate.explicacionClinica`
  - `threshold_exceeded == true` → genera `AlertaCreate`
