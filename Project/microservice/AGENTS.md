# AGENTS.md — Microservicio IA

**One-Liner:** Capa aislada de Inteligencia Artificial para predicción de riesgo cardiovascular y priorización de triaje. Expone una API REST (FastAPI :8001) con **un único agente LangGraph** (`ClinicalGraph`), un `RiskEngine` ponderado, un `TriagePriorityService` con pesos optimizados por PSO, y RAG sobre ChromaDB con providers de embeddings intercambiables. El optimizador PSO corre **offline** (no hay endpoint que lo ejecute).

---

## Stack Tecnológico

| Componente | Tecnología | Propósito |
|-----------|-----------|---------|
| Framework web | FastAPI | API REST async (puerto 8001) |
| Framework agent | LangGraph (LangChain v0.3+) | `StateGraph` del agente clínico |
| Dev tools | langgraph-cli[inmem] | LangGraph Studio local (`langgraph dev`) |
| Vector store | ChromaDB (`PersistentClient`) | Persistencia del índice RAG en `app/vectorstore/chroma` |
| Metaheurística | PSO propio (NumPy/Pandas) | Optimiza 7 pesos + 2 umbrales de prioridad (offline) |
| Embeddings | LangChain providers | openai / huggingface / fake |
| LLM | OpenAI / LM Studio | Vía langchain providers |
| Settings | pydantic-settings | `.env` → `Settings` (`core/config.py`) |
| Testing | pytest + pytest-asyncio | Tests async |
| Tracing | LangSmith (opcional) | `LANGCHAIN_TRACING_V2=true` |

> **Nota de persistencia:** el microservicio **no define modelos SQLModel ni migraciones Alembic propias**. La única persistencia activa es ChromaDB (RAG) y archivos JSON de pesos/curva (`app/data/`). `Settings.database_url` existe pero hoy no se usa para escribir tablas (`/health` reporta `postgres: not_checked`).

---

## Arquitectura

Entry point único: `app/main.py` (`uvicorn app.main:app --port 8001`).

```text
microservice/
  app/
    main.py                      # FastAPI + lifespan: instancia Services, registra routers de agents
    studio.py                    # Bootstrap para LangGraph Studio (exporta clinical_graph)
    agents/
      __init__.py                # load_agents() desde manifest.yaml + inyección de deps
      base.py                    # BaseAgent ABC
      clinical_subgraph.py       # ClinicalGraph: predict → prioritize → RAG → explain → response
      manifest.yaml              # Registro de agents (sólo 'clinical' habilitado)
    api/
      routes_health.py           # GET /health
      routes_ready.py            # GET /ready
      routes_metrics.py          # GET /metrics/evaluation, GET /metrics/convergence
      routes_optimize.py         # POST /optimize (persiste pesos PSO ya calculados; NO ejecuta PSO)
      routes_rag.py              # CRUD RAG bajo prefijo /rag (+ /rag/reindex)
    core/
      config.py                  # Settings (pydantic-settings) + singleton
      dependencies.py            # get_services, verify_internal_token (Bearer)
      registry.py                # ProviderRegistry (LLM y embeddings)
      resolver.py                # create_llm(), create_embeddings()
      langgraph_state.py         # ClinicalState (TypedDict)
      langsmith.py               # Cliente LangSmith + tracing
      logging.py                 # setup_logging()
    providers/                   # Auto-registro al importar el paquete
      llm_openai.py              # ChatOpenAI
      llm_lmstudio.py            # ChatOpenAI con base_url local
      embeddings_openai.py       # OpenAIEmbeddings
      embeddings_huggingface.py  # HuggingFaceEmbeddings
      embeddings_fake.py         # FakeEmbeddings (sólo dev; bloqueado en prod)
    schemas/
      prediction.py              # PredictionRequest, PredictionResponse
      explanation.py             # ClinicalExplanation, EvidenceSource, ExplainRequest, ExplainResponse
      metrics.py                 # MetricsRow, MetricsComparison
      optimize.py                # OptimizeUploadRequest, OptimizeUploadResponse
      rag.py                     # RagDocumentRequest/Update/Summary, RagBulk*, RagList*, RagReindex*
    services/
      __init__.py                # Services: orquesta RiskEngine, RAG, TriagePriorityService, LLM, agents
      risk_engine.py             # Modelo de riesgo 11-pesos, sigmoid, 3 niveles (bajo/medio/alto)
      triage_priority_service.py # Clasificador PSO 7-pesos + 2 umbrales, 3 niveles (BAJA/MEDIA/ALTA)
      rag_service.py             # ChromaDB + embeddings via provider
      metrics_service.py         # accuracy, recall, F1, critical_recall, fitness
      optimizers/
        base.py                  # BaseOptimizer ABC + OptimizerResult
        pso.py                   # PSOOptimizer (pesos + thresholds)
    tools/
      pso_tools.py               # @tool optimize_triage_priority_tool (ejecuta PSO OFFLINE)
    config/
      clinical_params.yaml       # Thresholds clínicos, features, fallback
    data/
      clinical_docs/             # 3 .md demo para RAG
      synthetic_cases.csv        # Dataset sintético para PSO
      optimized_weights.json     # Pesos del RiskEngine (11)
      triage_priority_weights.json # Pesos + umbrales del TriagePriorityService (PSO)
      convergence_curve.json     # Curva de convergencia de la última corrida PSO
      fixtures/                  # Payloads de ejemplo (casos, telemetría, pregunta médico)
      charts/                    # Gráficas N3 (confusión, convergencia)
    vectorstore/chroma/          # Persistencia ChromaDB del índice RAG

  tests/                         # pytest async
  notebooks/                     # EDA, baseline, metaheurísticas
  scripts/                       # Bootstrap y utilidades
  langgraph.json                 # Config Studio: graph "clinical" -> app.studio:clinical_graph
  requirements.txt / pyproject.toml / pytest.ini
  .env
```

> **Dos esquemas de pesos distintos (no confundir):**
> - `RiskEngine` → **11 pesos** (`optimized_weights.json`), sigmoid, produce `risk_level` ∈ {bajo, medio, alto}.
> - `TriagePriorityService` → **7 pesos + 2 umbrales** optimizados por PSO (`triage_priority_weights.json`), produce `priority` ∈ {BAJA, MEDIA, ALTA} (niveles 0/1/2).

---

## Único agente: ClinicalGraph — `POST /predecir`

`StateGraph` con estado tipado `ClinicalState` (`core/langgraph_state.py:6`). Flujo:

```
PredictionRequest (heart_rate, spo2, systolic_bp, age, sex, ...)
  │
  ▼
[normalize_and_predict]
  │  RiskEngine.predict(data) → {risk_score, risk_level, threshold_exceeded,
  │                              dominant_factors, recommended_action}
  ▼
[prioritize]
  │  CHEST_PAIN_MAP + build_feature_bundle(...) → 7 features normalizados
  │  TriagePriorityService.classify(bundle) → PriorityResult
  │    {score, priority_label, priority_level, weights_version}
  ▼
_should_explain: ¿request.explain == True?
  ├── No ───────────────────────────────────────────┐
  └── Sí                                             │
      ▼                                               │
   [retrieve_rag]                                    │
   │  query = dominant_factors                        │
   │  rag.retrieve_async(query, k=retrieval_k)        │
   ▼                                                  │
   [explain]                                          │
   │  Filtra fuentes por MIN_RAG_SCORE                │
   │  CLINICAL_PROMPT | LLM → JSON                     │
   │  Valida contra ClinicalExplanation; fallback     │
   │  seguro si LLM falla o no hay evidencia           │
      │                                                │
      ▼                                                ▼
[format_response]                                    ◄┘
  │  PredictionResponse con:
  │    risk_score, risk_level, threshold_exceeded, dominant_factors,
  │    clinical_explanation, explanation_structured, recommended_action,
  │    rag {used, sources}, model {technique, weights_version, prompt_version, ...},
  │    priority, priority_score, priority_level, weights_version
  ▼
PredictionResponse → backend
```

**Archivos involucrados:**

| Paso | Archivo:línea | Función |
|------|--------------|---------|
| Router `/predecir` | `agents/clinical_subgraph.py:328` | `predecir()` (auth Bearer interno) |
| Router `/explicar` | `agents/clinical_subgraph.py:355` | `explicar()` (auth Bearer interno) |
| Build graph | `agents/clinical_subgraph.py:144` | `_build_graph()` |
| Normalizar + riesgo | `agents/clinical_subgraph.py:175` | `_normalize_and_predict()` |
| Priorizar (PSO) | `agents/clinical_subgraph.py:187` | `_prioritize()` |
| RAG | `agents/clinical_subgraph.py:205` | `_retrieve_rag()` |
| Explicar (LLM) | `agents/clinical_subgraph.py:212` | `_explain()` |
| Formatear | `agents/clinical_subgraph.py:266` | `_format_response()` |
| RiskEngine | `services/risk_engine.py:119` | `predict(data)` |
| Priority | `services/triage_priority_service.py` | `build_feature_bundle()`, `TriagePriorityService.classify()` |
| State | `core/langgraph_state.py:6` | `ClinicalState(TypedDict)` |

> `manifest.yaml` registra sólo `clinical` con deps `[llm, risk_engine, rag, triage_priority]`. `load_agents()` (`agents/__init__.py:12`) los inyecta y expone cada agente como `services.{name}_graph`. El router del agente se monta en el `lifespan` (`main.py:41-46`).

---

## PSO offline (no es un endpoint)

El optimizador **no se ejecuta vía HTTP**. La única superficie que corre PSO es el `@tool optimize_triage_priority_tool` (`tools/pso_tools.py`), invocado desde LangGraph Studio, scripts de evaluación o tareas admin. El tool:

1. Carga `synthetic_cases.csv` → `(X, y_priority)`.
2. Corre `PSOOptimizer.optimize()` (`services/optimizers/pso.py`).
3. Escribe `triage_priority_weights.json` + `convergence_curve.json`.

`POST /optimize` **sólo persiste** un resultado PSO ya calculado (subido en el request) y recarga el `TriagePriorityService` (`triage_priority.reload()`). No corre el optimizador.

---

## Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/predecir` | Bearer interno | Predicción de riesgo + priorización PSO + explicación (ClinicalGraph) |
| POST | `/explicar` | Bearer interno | Pregunta del médico + contexto → respuesta LLM (ClinicalGraph) |
| POST | `/optimize` | Bearer interno | Persiste pesos+umbrales PSO ya calculados y recarga el priority service |
| GET | `/metrics/evaluation` | — | Comparación baseline vs. optimizado (lee `triage_priority_weights.json`) |
| GET | `/metrics/convergence` | — | Curva de convergencia de la última corrida PSO |
| POST | `/rag/documents` | Bearer interno | Indexa un documento clínico en ChromaDB |
| POST | `/rag/documents/bulk` | Bearer interno | Indexación masiva (sync de historiales desde backend) |
| GET | `/rag/documents` | Bearer interno | Lista documentos indexados (paginado) |
| GET | `/rag/documents/{doc_id}` | Bearer interno | Detalle de un documento |
| PUT | `/rag/documents/{doc_id}` | Bearer interno | Actualiza documento (re-embebe si cambia `contenido`) |
| DELETE | `/rag/documents/{doc_id}` | Bearer interno | Elimina documento y sus chunks |
| POST | `/rag/reindex` | Bearer interno | Reconstruye el índice desde los `.md` de `clinical_docs` |
| GET | `/health` | — | Estado de LLM, embeddings, ChromaDB, agents, LangSmith |
| GET | `/ready` | — | Readiness: 503 si embeddings fake, RAG no cargado o faltan pesos |
| GET | `/` | — | Info básica del servicio |

> **Autenticación:** `verify_internal_token` (`core/dependencies.py:11`) exige `Authorization: Bearer <internal_token>`. El `internal_token` se configura en `.env` y debe coincidir con el `INTERNAL_TOKEN` del backend.

---

## LangGraph Studio (desarrollo visual)

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev   # abre Studio apuntando a http://127.0.0.1:2024
```

| Archivo | Propósito |
|---------|-----------|
| `langgraph.json` | `"graphs": { "clinical": "app.studio:clinical_graph" }` |
| `app/studio.py` | Instancia Settings, LLM, embeddings, RiskEngine, RAG, TriagePriorityService y `ClinicalGraph`; exporta `clinical_graph` |

El Agent Server (puerto 2024) coexiste con uvicorn (puerto 8001), que sigue sirviendo los endpoints REST.

---

## Contratos Cross-Module

### Backend → Microservicio

| Quién | Endpoint | Request | Response |
|-------|----------|---------|----------|
| `backend/app/services/microservice_client.py:30` | `POST /predecir` | `PredictionRequest` | `PredictionResponse` |

**PredictionRequest** (enviado por el backend):
```json
{
  "paciente_id": 1, "evento_id": 12,
  "heart_rate": 72, "spo2": 98,
  "systolic_bp": 118, "diastolic_bp": 76,
  "cholesterol": 180, "glucose": 90,
  "age": 35, "sex": "F",
  "chest_pain_type": null, "smoker": false,
  "previous_condition": false, "explain": true
}
```
> Validación: `heart_rate` obligatorio; el resto opcional. `systolic_bp` debe ser mayor que `diastolic_bp` (validador en `schemas/prediction.py:24`).

**PredictionResponse** (devuelto al backend):
```json
{
  "paciente_id": 1, "evento_id": 12,
  "risk_score": 0.12, "risk_level": "bajo", "threshold_exceeded": false,
  "dominant_factors": ["sin factores dominantes significativos"],
  "clinical_explanation": "Paciente con perfil de riesgo bajo...",
  "explanation_structured": { "...": "ClinicalExplanation | null" },
  "recommended_action": "Monitoreo continuo sin intervención inmediata.",
  "rag": { "used": true, "sources": [ ... ] },
  "model": { "technique": "RiskEngine (sigmoid 11-pesos) + TriagePriorityService (PSO)",
             "weights_version": "...", "prompt_version": "...", "inference_time_ms": 0 },
  "priority": "BAJA", "priority_score": 0.18, "priority_level": 0,
  "weights_version": "pso-..."
}
```

**Adaptación en el backend** (`microservice_client.py`):

| Campo PredictionResponse | Destino backend |
|--------------------------|-----------------|
| `risk_level` | `TriajeCreate.nivelUrgencia` |
| `risk_score` | `TriajeCreate.probabilidadRiesgo` |
| `dominant_factors` | `TriajeCreate.factoresCriticos` (JSON string) |
| `clinical_explanation` | `TriajeCreate.explicacionClinica` |
| `threshold_exceeded == true` | Genera `AlertaCreate` |
| `priority` / `priority_score` / `priority_level` | Persistidos en `Evento.valorAgregado` |

> El backend tolera caídas del microservicio: `microservice_client.solicitar_prediccion()` captura timeout / HTTP / conexión y retorna un dict con `error`, sin lanzar excepción.

---

## Convenciones

- **Archivos**: `snake_case`. **Servicios**: sufijo `_service`. **Tests**: prefijo `test_`.
- **Schemas**: Pydantic en `schemas/`, nombrados por operación (`PredictionRequest/Response`, `ExplainRequest/Response`).
- **Endpoints**: en español (`/predecir`, `/explicar`, `/optimize`).
- **Entry point**: `uvicorn app.main:app` (NO `main:app`), puerto 8001.
- **Operaciones bloqueantes** (CSV, PSO, escritura JSON) se ejecutan fuera del event loop ASGI.
- **Auth interna**: todos los endpoints sensibles exigen `Authorization: Bearer <internal_token>`.

---

## Cobertura Rúbrica

### N2 — LangChain

| Criterio | Artefacto |
|----------|-----------|
| LLM | `providers/llm_openai.py` — ChatOpenAI vía provider registry |
| ChatPromptTemplate | `agents/clinical_subgraph.py` — `CLINICAL_PROMPT`, `MEDICO_EXPLAIN_PROMPT` |
| Tools | `tools/pso_tools.py` — `optimize_triage_priority_tool` |
| Chain/Agent | `agents/clinical_subgraph.py` — `StateGraph` predict→prioritize→RAG→explain→format |
| RAG | `services/rag_service.py` — ChromaDB + embeddings vía provider |

### N3 — Metaheurísticas

| Criterio | Artefacto |
|----------|-----------|
| Codificación | `services/optimizers/pso.py` — PSO para 7 pesos + 2 umbrales |
| Parámetros | Configurables en el `@tool` (n_particles, max_iter) |
| Métricas | `services/metrics_service.py` — accuracy, recall, F1, critical_recall, fitness |
| Comparación | `GET /metrics/evaluation` — baseline vs. optimizado |
| Visualización | `GET /metrics/convergence` + `convergence_curve.json` |

---

## Referencias

- `README.md` — Setup, stack y tabla de endpoints (fuente sincronizada con este documento).
- `../Project/backend/app/services/microservice_client.py` — Contrato HTTP con el backend.
- `app/agents/clinical_subgraph.py` — Implementación del único agente.
- `app/config/clinical_params.yaml` — Thresholds clínicos y configuración de fallback.
</content>
</invoke>
