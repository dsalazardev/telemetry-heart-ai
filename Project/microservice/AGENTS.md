# AGENTS.md — Microservicio IA

**One-Liner:** Capa aislada de Inteligencia Artificial para prediccion de riesgo cardiovascular. Expone API REST (FastAPI :8001) con LangGraph agents (clinical, n8n, pso), RiskEngine con pesos PSO-optimizados, RAG con ChromaDB + providers de embeddings, y metaheuristicas (PSO + AG).

---

## Stack Tecnologico

| Componente | Tecnologia | Version | Proposito |
|-----------|-----------|---------|-----------|
| Framework web | FastAPI | 0.136.3 | API REST async (puerto 8001) |
| ORM | SQLModel | 0.0.37 | Modelos BD + schemas Pydantic unificados |
| Framework agent | LangGraph | 0.3.0+ | StateGraph + InMemorySaver |
| Dev tools | langgraph-cli[inmem] | latest | LangSmith Studio local (`langgraph dev`) |
| Vector store | ChromaDB | 0.5.0+ | PersistentClient para RAG |
| Metaheuristicas | DEAP | 1.4.0+ | AG + PSO manual (Particle class) |
| Embeddings | LangChain providers | — | openai / huggingface / fake |
| Riesgo | RiskEngine | — | Modelo ponderado con pesos PSO-optimizados |
| Base de datos | PostgreSQL | — | Misma BD que backend (Aiven Cloud) |
| Driver async | asyncpg | 0.30+ | Conexion PostgreSQL async |
| Testing | pytest + pytest-asyncio | 9.0+ / 0.24+ | Tests async |
| LLM | OpenAI / LM Studio | — | Via langchain providers |

---

## Arquitectura

Entry point unico: `app/main.py` (uvicorn app.main:app).

```text
microservice/
  app/
    __init__.py
    main.py                    # FastAPI app + lifespan + auto-descubrimiento agents
    agents/
      __init__.py              # load_agents() desde manifest.yaml
      base.py                  # BaseAgent ABC
      clinical_subgraph.py     # ClinicalGraph: predictor + RAG + LLM explain
      n8n_subgraph.py          # N8NGraph: parseo, umbrales, fallback
      pso_subgraph.py          # PSOGraph: optimizar pesos, evaluar metricas
      manifest.yaml            # Registro de agents y sus dependencias
    api/
      __init__.py
      routes_health.py         # GET /health
      routes_ready.py          # GET /ready
      routes_metrics.py        # GET /metrics/evaluation, POST /rag/reindex
    core/
      __init__.py
      config.py                # Settings (pydantic-settings, .env) + singleton
      database.py              # Engine async, session factory, create_tables
      dependencies.py          # get_services, verify_internal_token
      registry.py              # ProviderRegistry (LLM y embeddings)
      logging.py               # setup_logging()
      langsmith.py             # LangSmith client + tracing nativo
      langgraph_state.py       # ClinicalState, PSOState, N8NState TypedDicts
    models/
      __init__.py
      lectura.py               # 13 features + target
      evaluacion.py            # FK a pacientes, lecturas, predicciones
      prediccion.py            # probabilidad, clasificacion, JSON metadata
      documento.py             # RAG: embedding PG_ARRAY(384)
      adapter.py               # Workflow: proveedor, endpoint, flujo JSON
      resolver.py              # create_llm(), create_embeddings()
    providers/
      __init__.py              # Importa todos los providers → auto-registro
      llm_openai.py            # ChatOpenAI via langchain-openai
      llm_lmstudio.py          # ChatOpenAI con base_url local
      embeddings_openai.py     # OpenAIEmbeddings
      embeddings_huggingface.py # HuggingFaceEmbeddings
      embeddings_fake.py       # FakeEmbeddings (solo dev)
    schemas/
      __init__.py
      predict.py               # PredictRequest, PredictResponse (13 features)
      prediction.py            # PredictionRequest, PredictionResponse (telemetria)
      agent.py                 # AgentQuery, AgentResponse
      workflow.py              # WorkflowTrigger, WorkflowResponse
      explanation.py           # ClinicalExplanation, EvidenceSource
      metrics.py               # MetricsRow, MetricsComparison
    services/
      __init__.py              # Services: orquesta RiskEngine, RAG, LLM, agents
      risk_engine.py           # Modelo de riesgo con pesos PSO-optimizados
      rag_service.py           # ChromaDB + embeddings via provider
      metrics_service.py       # Accuracy, recall, F1, false negative rate
      workflow_service.py      # HTTP client para adapters n8n
      genetic_engine.py        # DEAP AG: feature selection
      pso_engine.py            # DEAP PSO manual: hiperparametros
      optimizers/
        __init__.py
        base.py                # BaseOptimizer ABC + OptimizerResult
        pso.py                 # PSOOptimizer para pesos y thresholds
        registry.py            # OptimizerRegistry
    tools/
      __init__.py
      clinical_tools.py        # predict_risk(), retrieve_guidelines()
    data/
      clinical_docs/           # Documentos .md para RAG (3 archivos demo)
      generate_synthetic.py    # Genera synthetic_cases.csv
      synthetic_cases.csv      # Datos sinteticos para PSO
      optimized_weights.json   # Pesos optimizados por PSO
    config/
      clinical_params.yaml     # Thresholds, features, fallback, n8n config

  tests/
    conftest.py                # Fixtures: test DB, test_client con mocks
    test_agent.py              # ClinicalGraph, PSOGraph, N8NGraph + endpoints
    test_health.py             # /health, /ready, /
    test_prediction.py         # RiskEngine: sano, critico, incompleto, dominantes
    test_predictor.py          # /predecir endpoint
    test_rag.py                # RAGService con FakeEmbeddings
    test_registry.py           # ProviderRegistry
    test_manifest.py           # manifest.yaml + clinical_params.yaml
    test_models.py             # CRUD Lectura + Adapter
    test_workflow.py           # /n8n/webhook + /evaluar endpoints

  scripts/
    bootstrap_chroma.py        # Inicializar ChromaDB con documentos
    download_heart.py          # Descargar dataset heart.csv
    test_rag.py                # Test manual de RAG
    bootstrap.sh               # Setup inicial
    demo.sh                    # Demo script

  alembic/                     # Migraciones (branch_labels=microservice)
  notebooks/                   # Jupyter notebooks (EDA, baseline, metaheuristics)
  langgraph.json               # Config Agent Server para LangSmith Studio
  requirements.txt
  pyproject.toml
  pytest.ini
  .env / .env.example

  app/
    studio.py                  # Bootstrap para LangGraph Studio (exporta clinical/n8n/pso_graph)
    ...
```

---

## Flujo de Datos por Agente

Cada agente implementa un `StateGraph` (LangGraph) con nodos, edges condicionales y estados tipados (`app/core/langgraph_state.py`).

### ClinicalGraph — `POST /predecir`

```
PredictionRequest (heart_rate, spo2, systolic_bp, age, sex, ...)
  │
  ▼
[normalize_and_predict]
  │  RiskEngine.predict(data) → {risk_score, risk_level, dominant_factors}
  │
  ▼
_should_explain: ¿request.explain == True?
  ├── No ──────────────────────────────────────────┐
  │                                                 │
  └── Sí                                            │
      │                                              │
      ▼                                              │
[retrieve_rag]                                    │
  │  RAG.retrieve_async(query=dominant_factors)     │
  │  → [ {content, metadata, score}, ... ]          │
  │                                                 │
  ▼                                                 │
[explain]                                          │
  │  Filtra RAG por MIN_RAG_SCORE (0.65)            │
  │  CLINICAL_PROMPT.format(risk_score, level,      │
  │    dominant_factors, rag_sources)               │
  │  LLM.ainvoke(messages) → JSON                   │
  │  Valida contra ClinicalExplanation schema       │
  │  Fallback si LLM falla o score < 0.65           │
  │                                                 │
  ▼                                                 ▼
[format_response]                                   ◄┘
  │  Arma PredictionResponse con:
  │    - risk_score, risk_level, threshold_exceeded
  │    - dominant_factors, clinical_explanation
  │    - rag: {used, sources}
  │    - model: {technique, weights_version, prompt_version}
  │
  ▼
PredictionResponse → backend / n8n
```

**Archivos involucrados:**
| Paso | Archivo:linea | Funcion |
|------|--------------|---------|
| Entry | `agents/clinical_subgraph.py:198` | `router.post("/predecir")` |
| Normalizar | `agents/clinical_subgraph.py:108` | `_normalize_and_predict()` |
| RiskEngine | `services/risk_engine.py:70` | `predict(data)` → normaliza, sigmoid, clasifica |
| RAG | `agents/clinical_subgraph.py:113` | `_retrieve_rag()` → `rag.retrieve_async()` |
| Explain | `agents/clinical_subgraph.py:118` | `_explain()` → LLM + prompt |
| Formatear | `agents/clinical_subgraph.py:163` | `_format_response()` → PredictionResponse |
| State | `core/langgraph_state.py:6` | `ClinicalState(TypedDict)` |
| Trace | LangGraph nativo | Auto-tracing via `LANGCHAIN_TRACING_V2=true` |

---

### N8NGraph — `POST /evaluar`

```
{ paciente_id, frecuenciaCardiaca, spo2, systolic_bp, ... }
  │
  ▼
[parse_payload]
  │  Normaliza nombres de campo (es/en): heart_rate↔frecuencia_cardiaca, etc.
  │  Convierte tipos: _num(), _bool()
  │  Deduplicacion: cache por event_id (_EVENT_CACHE, max 1000)
  │
  ▼
[check_thresholds]
  │  Lee clinical_params.yaml → n8n_thresholds
  │  Evalua: taquicardia(>=130), bradicardia(<=45), SpO2(<=92),
  │          sistolica(>=160), diastolica(>=100), colesterol(>=240), glucosa(>=180)
  │  → threshold_flags: ["taquicardia >= 130 bpm", "SpO2 <= 92%", ...]
  │
  ▼
_needs_prediction: ¿len(flags) > 0?
  ├── No ───────────────────────────────────┐
  │                                          │
  └── Sí                                     │
      │                                       │
      ▼                                       │
[call_clinical]                              │
  │  Convierte parsed_data → PredictionRequest
  │  clinical_graph.run(request)             │
  │  → PredictionResponse                    │
  │                                          │
  ▼                                          │
_clinical_ok: ¿clinical_result sin error?    │
  ├── No ──▶ [build_fallback] ◀─────────────┘
  │           │  Reglas del clinical_params.yaml → fallback
  │           │  crit_flags=3 → ALTO, high_flags=1 → MEDIO
  │           │  → {risk_score, risk_level, fuente: "fallback_reglas_n8n"}
  │           │
  └── Sí ──┐
            │
            ▼
[format_n8n]                                 ◄┘
  │  Arma n8n_response con:
  │    - riesgo (ALTO/MEDIO/BAJO), score, prioridad (CRITICA/ALTA/MEDIA)
  │    - flags_umbral, resumen_clinico, prediccion
  │    - alerta: {paciente_id, tipo, prioridad, mensaje, origen}
  │
  ▼
{ n8n_response } → n8n workflow
```

**Archivos involucrados:**
| Paso | Archivo:linea | Funcion |
|------|--------------|---------|
| Entry | `agents/n8n_subgraph.py:279` | `router.post("/evaluar")`, `router.post("/n8n/webhook")` |
| Parseo | `agents/n8n_subgraph.py:128` | `_parse_payload()` |
| Umbrales | `agents/n8n_subgraph.py:150` | `_check_thresholds()` |
| Clinical | `agents/n8n_subgraph.py:155` | `_call_clinical()` → ClinicalGraph |
| Fallback | `agents/n8n_subgraph.py:178` | `_build_fallback()` |
| Formatear | `agents/n8n_subgraph.py:216` | `_format_n8n()` |
| Config | `config/clinical_params.yaml:9` | `n8n_thresholds`, `fallback` |
| State | `core/langgraph_state.py:26` | `N8NState(TypedDict)` |

---

### PSOGraph — `POST /optimize`

```
?action=optimize&n_particles=30&max_iter=100
  │
  ▼
[load_data]
  │  Lee synthetic_cases.csv
  │  → X(500×11 features), y(500 niveles: bajo/medio/alto)
  │
  ▼
_should_optimize: ¿action == "optimize"?
  ├── No ──▶ [explain_results]
  │
  └── Sí
      │
      ▼
[run_pso]  ← asyncio.to_thread (CSV + PSO)
  │  PSOOptimizer(n_particles, max_iter).optimize(X, y)
  │  30 particulas exploran espacio n_features+3 dimensiones
  │  Fitness = 0.45×FNR + 0.25×(1-recall) + 0.20×(1-F1) + 0.10×FPR
  │  → OptimizerResult: weights, thresholds, bias, convergence_curve
  │
  ▼
[evaluate_metrics]  ← asyncio.to_thread (CSV + metrics)
  │  MetricsService.compare(X, y, baseline_w, baseline_t, opt_w, opt_t)
  │  → {baseline, optimized, improvement, delta}
  │
  ▼
_should_explain: ¿action en (optimize, explain)?
  ├── No ──▶ [export_weights]
  │
  └── Sí
      │
      ▼
[explain_results]
  │  PSO_PROMPT.format(context=resultados + comparacion)
  │  LLM.ainvoke() → explicacion en lenguaje natural
  │
  ▼
[export_weights]  ← asyncio.to_thread (write_text)
  │  Guarda optimized_weights.json:
  │    {weights, thresholds, bias, version, metrics}
  │
  ▼
[format_result]
  │  {baseline, optimized, delta, weights, thresholds,
  │   convergence_curve, explanation, runtime_ms}
  │
  ▼
Resultado JSON → dev / demo
```

**Archivos involucrados:**
| Paso | Archivo:linea | Funcion |
|------|--------------|---------|
| Entry | `agents/pso_subgraph.py:199` | `router.post("/optimize")` |
| Load | `agents/pso_subgraph.py:79` | `_load_data()` |
| PSO | `agents/pso_subgraph.py:92` | `_run_pso()` → `PSOOptimizer.optimize()` |
| PSO core | `services/optimizers/pso.py:47` | `PSOOptimizer` con fitness function |
| Metricas | `agents/pso_subgraph.py:108` | `_evaluate_metrics()` → `MetricsService.compare()` |
| Explain | `agents/pso_subgraph.py:123` | `_explain_results()` → LLM |
| Export | `agents/pso_subgraph.py:137` | `_export_weights()` → optimized_weights.json |
| Data | `app/data/synthetic_cases.csv` | 500 registros sinteticos (bajo/medio/alto) |
| State | `core/langgraph_state.py:16` | `PSOState(TypedDict)` |

> **Nota:** Operaciones bloqueantes (CSV, PSO, escritura JSON) envueltas en `asyncio.to_thread()` para no bloquear el event loop ASGI.

---

## LangSmith Studio (Desarrollo Visual)

Visualizacion y depuracion paso a paso de los 3 grafos via LangGraph Agent Server.

**Setup:**
```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev
# Abre automaticamente: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

| Archivo | Proposito |
|---------|-----------|
| `langgraph.json` | Config: `"clinical": "app.studio:clinical_graph"`, `"n8n"`, `"pso"` |
| `app/studio.py` | Bootstrap: instancia Settings, LLM, embeddings, RiskEngine, RAG, 3 agentes. Exporta `clinical_graph`, `n8n_graph`, `pso_graph` |

**Tracing:** LangGraph nativo — sin `RunTree` manual. Cada `graph.ainvoke()` genera trace padre con sub-spans por nodo visibles en Studio. Requiere `LANGCHAIN_TRACING_V2=true` en `.env`.

**FastAPI vs Studio:** El Agent Server (puerto 2024) coexiste con uvicorn (puerto 8001). FastAPI sigue sirviendo los endpoints REST para backend/n8n.

---

## Endpoints

| Metodo | Ruta | Agente/Servicio | Descripcion |
|--------|------|-----------------|-------------|
| POST | `/predecir` | ClinicalGraph | 11 features fisiologicas → riesgo + explicacion |
| POST | `/explicar` | ClinicalGraph | Pregunta del medico + contexto → respuesta con evidencia |
| POST | `/evaluar` | N8NGraph | Webhook n8n: payload de telemetria → evaluacion umbrales + prediccion |
| POST | `/n8n/webhook` | N8NGraph | Alias de /evaluar |
| POST | `/optimize` | PSOGraph | Ejecutar PSO → pesos optimizados, metricas, curva convergencia |
| GET | `/health` | API | Health check con estado de LLM, embeddings, Chroma, agents |
| GET | `/ready` | API | Readiness probe: embeddings real, RAG cargado, pesos cargados |
| GET | `/metrics/evaluation` | API | Comparacion baseline vs optimizado (recall, F1, false negative) |
| POST | `/rag/reindex` | API | Reindexar documentos clinicos en ChromaDB |

---

## Contratos Cross-Module

### Backend → Microservicio

| Quien | Endpoint | Request Schema | Response Schema |
|-------|----------|---------------|-----------------|
| `backend/app/services/microservice_client.py:23` | `POST /predecir` | `PredictionRequest` (`schemas/prediction.py`) | `PredictionResponse` (`schemas/prediction.py`) |

**PredictionRequest** (enviado por el backend):
```json
{
  "paciente_id": 1,
  "heart_rate": 72,       "spo2": 98,
  "systolic_bp": 118,     "diastolic_bp": 76,
  "cholesterol": 180,     "glucose": 90,
  "age": 35,              "sex": "F",
  "chest_pain_type": null,"smoker": false,
  "previous_condition": false, "explain": true
}
```

**PredictionResponse** (devuelto al backend, mapeado a `TriajeCreate`):
```json
{
  "paciente_id": 1,
  "risk_score": 0.12,
  "risk_level": "bajo",
  "threshold_exceeded": false,
  "dominant_factors": ["sin factores dominantes significativos"],
  "clinical_explanation": "Paciente con perfil de riesgo bajo...",
  "recommended_action": "Monitoreo continuo sin intervencion inmediata.",
  "rag": { "used": true, "sources": [...] },
  "model": { "technique": "PSO-optimized", "weights_version": "pso-v1" }
}
```

**Adaptacion en el backend** (`microservice_client.py:44-57`):
| Campo PredictionResponse | Campo TriajeCreate |
|--------------------------|-------------------|
| `risk_level` | `nivelUrgencia` |
| `risk_score` | `probabilidadRiesgo` |
| `dominant_factors` | `factoresCriticos` (JSON string) |
| `clinical_explanation` | `explicacionClinica` |
| `threshold_exceeded == true` | Genera `AlertaCreate` |

### n8n → Microservicio

| Quien | Endpoint | Request Schema | Response Schema |
|-------|----------|---------------|-----------------|
| `n8n/workflows/THA-Webhook-Telemetria.json` (nodo 4) | `POST /evaluar` | `dict` (campos flexibles) | `{n8n_response: {...}}` |

**Request** (enviado por n8n — soporta nombres es/en):
```json
{
  "paciente_id": 1,
  "frecuenciaCardiaca": 160,   // o "heart_rate"
  "spo2": 82,
  "presion_sistolica": 200,    // o "systolic_bp"
  "presion_diastolica": 120,   // o "diastolic_bp"
  "colesterol": 300,           // o "cholesterol"
  "glucosa": 250,              // o "glucose"
  "edad": 72,                  // o "age"
  "sexo": "M",                 // o "sex"
  "fumador": true,             // o "smoker"
  "dolor_toracico": "asymptomatic" // o "chest_pain_type"
}
```

**Response** (devuelto a n8n):
```json
{
  "n8n_response": {
    "riesgo": "ALTO",
    "score": 0.85,
    "prioridad": "CRITICA",
    "flags_umbral": ["taquicardia >= 130 bpm", "SpO2 <= 92%"],
    "resumen_clinico": "Paciente 1 con riesgo ALTO. Flags: ...",
    "prediccion": { "risk_score": 0.85, "risk_level": "alto", ... },
    "microservice_fallo": false,
    "alerta": {
      "paciente_id": 1,
      "tipo": "riesgo_cardiovascular",
      "prioridad": "CRITICA",
      "mensaje": "Paciente 1 con riesgo ALTO...",
      "flags": ["taquicardia >= 130 bpm"],
      "origen": "n8n_agent"
    }
  }
}
```

### Microservicio → PostgreSQL

| Modulo | Tablas | Operaciones |
|--------|--------|-------------|
| `core/database.py` | `lecturas`, `predicciones`, `evaluaciones`, `documentos`, `adapters` | `create_all` en startup |
| `alembic/` | Las 5 tablas | Migracion `7468eec37173` |
| `models/` (SQLModel) | Las 5 tablas | ORM via `AsyncSession` |

---

## Esquema de Base de Datos

**Instancia:** PostgreSQL Aiven Cloud (compartida con backend).
**Migracion:** `alembic/versions/7468eec37173_add_microservice_tables.py`
**Branch:** `branch_labels=("microservice",)` — `depends_on="7468eec37172"` (migracion base del backend).

### `lecturas`
```sql
CREATE TABLE lecturas (
    id            SERIAL PRIMARY KEY,
    age           INTEGER NOT NULL,
    sex           INTEGER NOT NULL,       -- 1=M, 0=F
    cp            INTEGER NOT NULL,       -- tipo dolor toracico 0-3
    trestbps      INTEGER NOT NULL,       -- presion arterial reposo mmHg
    chol          INTEGER NOT NULL,       -- colesterol serico mg/dl
    fbs           BOOLEAN NOT NULL,       -- glucosa ayunas >120 mg/dl
    restecg       INTEGER NOT NULL,       -- ECG reposo 0-2
    thalach       INTEGER NOT NULL,       -- FC maxima alcanzada
    exang         BOOLEAN NOT NULL,       -- angina ejercicio
    oldpeak       FLOAT NOT NULL,         -- depresion ST
    slope         INTEGER NOT NULL,       -- pendiente ST 0-2
    ca            INTEGER NOT NULL,       -- vasos coloreados 0-3
    thal          INTEGER NOT NULL,       -- talasemia 0-3
    target        BOOLEAN,                -- NULL=pendiente, TRUE=enfermo, FALSE=sano
    fechaCreacion TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### `predicciones`
```sql
CREATE TABLE predicciones (
    id                  SERIAL PRIMARY KEY,
    versionModelo       VARCHAR NOT NULL,     -- "rf-v1.0", "pso-v2"
    probabilidad        FLOAT NOT NULL,       -- 0.0 a 1.0
    clasificacion       VARCHAR NOT NULL,     -- "bajo" | "medio" | "alto"
    importanciaVariables JSON,                -- {feature: importance, ...}
    tiempoMs            FLOAT NOT NULL,       -- ms de inferencia
    fecha               TIMESTAMP NOT NULL DEFAULT NOW(),
    metadataTecnica     JSON                  -- config del modelo, hiperparams
);
```

### `evaluaciones`
```sql
CREATE TABLE evaluaciones (
    id               SERIAL PRIMARY KEY,
    fechaEvaluacion  TIMESTAMP NOT NULL DEFAULT NOW(),
    origenDatos      VARCHAR NOT NULL,        -- "telemetria" | "manual" | "batch"
    paciente_id      INTEGER NOT NULL,        -- FK → pacientes.id (BACKEND)
    lectura_id       INTEGER NOT NULL REFERENCES lecturas(id),
    prediccion_id    INTEGER NOT NULL REFERENCES predicciones(id)
);
-- paciente_id es FK cross-module: la tabla pacientes esta en el backend
```

### `documentos`
```sql
CREATE TABLE documentos (
    id              SERIAL PRIMARY KEY,
    titulo          VARCHAR NOT NULL,
    contenido       TEXT NOT NULL,
    embedding       FLOAT[],                  -- PG_ARRAY 384 dimensiones
    fuente          VARCHAR NOT NULL,
    fechaIndexacion TIMESTAMP NOT NULL DEFAULT NOW(),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    prediccion_id   INTEGER REFERENCES predicciones(id)
);
```

### `adapters`
```sql
CREATE TABLE adapters (
    id             SERIAL PRIMARY KEY,
    proveedor      VARCHAR NOT NULL,          -- "n8n" | "langchain" | "manual"
    endpoint       VARCHAR NOT NULL,          -- URL del webhook
    flujo          JSON,                      -- config del workflow
    token          VARCHAR NOT NULL,
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    fechaCreacion  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Relaciones entre tablas

```
evaluaciones.paciente_id  ──FK──▶  pacientes.id          (backend)
evaluaciones.lectura_id   ──FK──▶  lecturas.id
evaluaciones.prediccion_id──FK──▶  predicciones.id
documentos.prediccion_id  ──FK──▶  predicciones.id
predicciones.id           ◀──FK──  documentos.prediccion_id
```

---

## Convenciones

- **Archivos**: `snake_case`
- **Modelos**: Singular (`Lectura`, `Prediccion`) — SQLModel usa el nombre de la clase como tabla
- **Servicios**: Sufijo `_service` (`rag_service.py`, `metrics_service.py`)
- **Schemas**: Sufijo de operacion (`PredictRequest`, `PredictResponse`, `PredictionRequest`)
- **Endpoints**: En espanol/prefijo descriptivo (`/predecir`, `/evaluar`, `/optimize`)
- **Tests**: Prefijo `test_` + `_` + nombre del modulo (`test_agent.py`)
- **BD**: PostgreSQL en Aiven Cloud (remoto), conexion via URL con python-dotenv
- **Entry point**: `uvicorn app.main:app` (NO `main:app`)

---

## Cobertura Rubrica

### N2 — LangChain (30% del nivel 2)

| PPTX | Criterio | Artefacto |
|------|----------|-----------|
| 07 | LLM | `providers/llm_openai.py` — ChatOpenAI via provider registry |
| 07 | ChatPromptTemplate | `agents/clinical_subgraph.py` — CLINICAL_PROMPT, MEDICO_EXPLAIN_PROMPT |
| 07 | Tools | `tools/clinical_tools.py` — predict_risk(), retrieve_guidelines() |
| 07 | Chain/Agent | `agents/clinical_subgraph.py` — StateGraph con nodos normalize→RAG→explain→format |
| 08 | RAG | `services/rag_service.py` — ChromaDB + embeddings via provider |
| 09 | Video | YouTube 4-10 min demostracion |

### N3 — Metaheuristicas (20% del nivel 3)

| PPTX | Criterio | Artefacto |
|------|----------|-----------|
| 10 | Seleccion | AG + PSO combinados |
| 10 | Codificacion | `services/optimizers/pso.py` — PSO para pesos + thresholds |
| 10 | Parametros | 30 particulas × 100 iteraciones, w=0.7, c1=c2=1.5 |
| 11 | Metrica #1 | Accuracy, recall, F1 en `services/metrics_service.py` |
| 11 | Metrica #2 | Comparacion baseline vs optimizado en `/metrics/evaluation` |
| 11 | Visualizacion | Curvas de convergencia en `OptimizerResult.convergence_curve` |

---

## Mapeo UML → Codigo

| Concepto UML | Implementacion |
|-------------|---------------|
| Clase `<<microservice>>` | Modelo SQLModel en `models/` |
| `Lectura.exportarVector()` | Metodo del modelo |
| `Prediccion.interpretarResultado()` | Metodo del modelo |
| `Documento.buscarSimilares()` | Delegado a `services/rag_service.py` |
| `Adapter.ejecutarFlujo()` | Delegado a `services/workflow_service.py` |
| `Adapter.notificarUrgencia()` | Delegado a `services/workflow_service.py` |
| Relacion `Evaluacion → Paciente` | `paciente_id` FK → `pacientes.id` (backend) |
| `embedding: List~Float~` | `sa_column=Column(PG_ARRAY(Float))` |
| `importanciaVariables: JSON` | `sa_type=JSON` |
| `flujo: Object` | `sa_type=JSON` |

---

## Referencias

- `../Documents/Diagrama UML.md` — 5 modelos exactos del sistema
- `../Rubric/Proyecto final_SI1_UCaldas.md` — Rubrica N2 + N3
- `../Project/backend/AGENTS.md` — Template de estructura y convenciones
- `../Project/backend/app/services/microservice_client.py` — Contrato HTTP con backend
- `exploracion-definitiva.md` — ADRs y validacion ctx7 (historico)
