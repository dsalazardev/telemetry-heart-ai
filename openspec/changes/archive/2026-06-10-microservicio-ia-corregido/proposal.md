One-Liner: Microservicio IA para Telemetry Heart AI. FastAPI :8001 con 5 modelos SQLModel (Lectura, Evaluacion, Prediccion, Documento, Adapter), 6 endpoints, RandomForest predictor, LangChain Agent (create_agent + InMemorySaver + 4 tools), RAG (Chroma + SentenceTransformer), y metaheurísticas (DEAP AG + PSO manual). Cubre rúbrica N2 (8 criterios) + N3 (7 criterios).

## Why

The Telemetry Heart AI project requires a dedicated microservice to process cardiac telemetry data using AI/ML techniques. The existing backend handles data ingestion but lacks the capability to perform real-time cardiac risk prediction, intelligent triage evaluation, and automated AI-assisted documentation. This microservice will provide the AI engine that powers the clinical workflow, enabling automated prediction, triage, and report generation.

## What Changes

- **New microservice**: Create a standalone FastAPI service on port 8001 with its own database models, services, and endpoints
- **5 new database models**: `Lectura`, `Evaluacion`, `Prediccion`, `Documento`, `Adapter` (SQLModel + PostgreSQL) — **exact attributes from UML Diagram**
- **6 new API endpoints**: `POST /predict`, `POST /evaluar`, `POST /agent/query`, `POST /agent/train`, `POST /workflow/trigger`, `GET /health`
- **RandomForest predictor**: Trainable model for cardiac risk prediction using 13 exact features from heart dataset: `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal`
- **LangChain AI agent**: ReAct agent with 4 tools (`predict_cardiac_risk`, `evaluate_triage`, `generate_document`, `search_knowledge`) and persistent memory via `InMemorySaver` + `thread_id`
- **RAG pipeline**: ChromaDB vector store with `sentence-transformers/all-MiniLM-L6-v2` embeddings (384d) via `SentenceTransformer` API for clinical knowledge retrieval
- **Metaheuristics engine**: DEAP-based genetic algorithm (50 ind × 20 gen) for feature selection + custom PSO implementation (30 particles × 30 iterations) for hyperparameter tuning
- **Alembic migration**: Cross-project migration with `branch_labels = ("microservice",)` and `depends_on = "7468eec37172"` (backend base migration)
- **Test suite**: pytest-asyncio with SQLite in-memory for unit and integration tests (coverage > 80%)
- **Documentation**: EDA notebooks, baseline training, N3 metrics visualization, and PPTX-ready charts

## Capabilities

### New Capabilities
- `ai-prediction`: Cardiac risk prediction via RandomForest with 13 exact features from heart dataset
- `ai-triage-evaluation`: Automated triage evaluation with `Evaluacion` model linking `paciente_id` (cross-module FK), `lectura_id`, and `prediccion_id`
- `ai-agent`: LangChain ReAct agent with `create_agent()` + 4 `@tool` decorators + `InMemorySaver()` + `thread_id`
- `ai-rag`: Retrieval-augmented generation with ChromaDB `PersistentClient` + `SentenceTransformer` embeddings
- `ai-metaheuristics`: Feature selection (DEAP AG) and hyperparameter tuning (custom PSO)
- `ai-workflow`: Adapter-based workflow execution implementing `Workflow` interface (`ejecutarFlujo()`, `notificarUrgencia()`)
- `ai-health`: Health check endpoint monitoring DB, model, and ChromaDB status

### Modified Capabilities
- None (this is a greenfield microservice, no existing specs to modify)

## Impact

- **Code**: New directory `Project/microservice/` with ~55 files (models, services, routers, tests, notebooks, config)
- **Database**: New PostgreSQL schema with 5 tables (`lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`). Shared Aiven Cloud instance. Cross-module FKs: `Evaluacion.paciente_id` → `pacientes.id` (backend)
- **APIs**: New service on port 8001. Backend `MicroserviceClient` calls `POST /predict` with timeout 10s
- **Dependencies**: FastAPI, SQLModel, LangChain, ChromaDB, DEAP, scikit-learn, sentence-transformers, torch (~200MB CPU-only), joblib
- **Migration**: New Alembic migration depends on backend `7468eec37172_init` (conditional `depends_on` for test environments)
- **Rubric**: Covers N2 (LangChain Agent + RAG, 8 criterios: PPTX 07-09) and N3 (Metaheuristics, 7 criterios: PPTX 10-11)
- **Integration**: Backend communicates via `MICROSERVICE_URL=http://localhost:8001`. `workflow_id` fields in backend models reference `Adapter.id` conceptually

## Timeline & Estimación

| Fase | Descripción | Horas Est. |
|------|-------------|-----------|
| 0 | Proyecto base (main.py, settings, database, requirements) | 2h |
| 1 | 5 modelos SQLModel exactos + migración Alembic | 3h |
| 2 | Predictor + endpoints (predict, evaluar, health) | 2h |
| 3 | Notebook EDA + entrenamiento baseline + .pkl | 2h |
| 4 | RAG Service (Chroma + SentenceTransformer) | 2h |
| 5 | LangChain Agent (create_agent + 4 tools + InMemorySaver) | 3h |
| 6 | Metaheurísticas (DEAP AG + PSO manual) | 3h |
| 7 | Notebook métricas N3 + visualizaciones PPTX | 2h |
| 8 | Tests (pytest + SQLite in-memory, coverage >80%) | 2h |
| 9 | Documentación + AGENTS.md actualización | 1h |
| 10 | Integración final + verificación flujo completo | 2h |
| **Total** | | **~24h** |

## Criterios de Éxito (Medibles)

1. **Endpoints funcionales**: Los 6 endpoints responden HTTP 200 con payloads correctos (verificados via tests)
2. **Modelos exactos**: Los 5 modelos SQLModel tienen atributos idénticos al UML (verificados vs `Diagrama UML.md`)
3. **Tablas en plural**: Las 5 tablas se llaman `lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`
4. **Tests coverage**: Cobertura de tests > 80% para `services/` y `routers/` (reporte de pytest-cov)
5. **Rúbrica N2**: 8 criterios cubiertos (PPTX 07-09: LLM, ChatPromptTemplate, Tools, Chain/Agent, Código, CoT, RAG, Video)
6. **Rúbrica N3**: 7 criterios cubiertos (PPTX 10-11: Selección, Codificación, Parámetros AG, Parámetros PSO, Métrica #1, Métrica #2, Visualización)
7. **Migración aplicable**: Alembic migration se aplica correctamente en PostgreSQL con `branch_labels` + `depends_on`
8. **Modelo entrenado**: `model.pkl` existe y predice correctamente las 3 clases (bajo/medio/alto)
9. **RAG funcional**: ChromaDB responde consultas clínicas en <100ms con top-5 documentos relevantes
10. **Agente conversacional**: Responde preguntas usando las 4 herramientas y mantiene memoria entre queries (`session_id`)

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **LangChain API v0.3+ inestable** | Media | Alto | Fijar versiones exactas en `requirements.txt` (`langchain==0.3.x`, `langchain-openai==0.2.x`). Wrap en `AgentService` para localizar cambios. |
| **torch 200MB (dependencia pesada)** | Alta | Media | Instalar CPU-only (`--index-url https://download.pytorch.org/whl/cpu`). Docker multi-stage build. |
| **DEAP PSO manual (bugs potenciales)** | Media | Alto | Tests unitarios exhaustivos para `Particle` class y update loop. Documentar algoritmo en código + markdown. |
| **Dataset heart.csv no en repo** | Alta | Baja | Script `download_heart.py` en bootstrap descarga desde UCI. `.gitignore` excluye `.csv` y `.pkl`. |
| **Cross-module FKs sin enforcement** | Baja | Media | Documentar en `AGENTS.md`. Validación soft en `WorkflowService`. No romper backend. |
| **Latencia >10s (timeout backend)** | Baja | Alto | Endpoints async. Caché opcional Redis. Presupuesto: Chroma 5ms + embeddings 50ms + LLM 2-4s + predict 1ms = ~2-5s. |

## Rúbrica Académica

### N2 — LangChain (30% del nivel 2) — 8 criterios

| PPTX | Criterio | Artefacto | Estado |
|------|----------|-----------|--------|
| 07 | LLM | `services/langchain_agent_service.py` — `model="openai:gpt-4o-mini"` | ✅ |
| 07 | ChatPromptTemplate | System prompt + regla `medico_id` | ✅ |
| 07 | Tools | 4 `@tool` decorators (predict_risk, query_patients, rag_explain, format_response) | ✅ |
| 07 | Chain/Agent | `create_agent()` + `InMemorySaver()` + `thread_id` | ✅ |
| 08 | Código | `notebooks/02-baseline.ipynb` (fragmento Python) | ✅ |
| 08 | CoT | `docs/ejemplo-cot.log` — log del loop ReAct | ✅ |
| 08 | RAG | `services/rag_service.py` — Chroma + `SentenceTransformer` | ✅ |
| 09 | Video | YouTube 4-10 min demostración | ✅ |

### N3 — Metaheurísticas (20% del nivel 3) — 7 criterios

| PPTX | Criterio | Artefacto | Estado |
|------|----------|-----------|--------|
| 10 | Selección | ADR-010 — AG + PSO combinados | ✅ |
| 10 | Codificación | `services/genetic_engine.py` — binario 13 bits, fitness = F1-score | ✅ |
| 10 | Parámetros AG | 50 ind × 20 gen, torneo k=3, cxUniform p=0.8 | ✅ |
| 10 | Parámetros PSO | `services/pso_engine.py` — `Particle` class, 30 part, 3 dim, 30 iter | ✅ |
| 11 | Métrica #1 | Accuracy: 0.82 → 0.87 → 0.91 (+9 pp) | ✅ |
| 11 | Métrica #2 | Features: 13 → 7 (−46%) | ✅ |
| 11 | Visualización | Curvas de convergencia, matriz de confusión | ✅ |
