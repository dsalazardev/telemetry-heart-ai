## 1. Project Base Setup

- [ ] 1.1 Create `Project/microservice/` directory structure: `app/`, `app/core/`, `app/models/`, `app/services/`, `app/routers/`, `tests/`, `notebooks/`, `data/`, `alembic/`
- [ ] 1.2 Create `requirements.txt` with all dependencies: FastAPI, uvicorn, SQLModel, asyncpg, psycopg2-binary, alembic, pydantic-settings, langchain, langchain-openai, langchain-community, chromadb, sentence-transformers, torch, scikit-learn, joblib, deap, pandas, numpy, jupyter, matplotlib, seaborn, pytest, pytest-asyncio, httpx, aiosqlite
- [ ] 1.3 Create `main.py` with FastAPI app factory, lifespan handler, and startup health checks
- [ ] 1.4 Create `app/core/settings.py` with PydanticSettings (DB URL, OPENAI_API_KEY, CHROMA_PATH, MODEL_PATH, ENV)
- [ ] 1.5 Create `app/core/database.py` with async engine, session factory, and `get_db()` dependency
- [ ] 1.6 Create `alembic.ini` with async PostgreSQL URL and `script_location = alembic`
- [ ] 1.7 Create `alembic/env.py` with async support, SQLModel metadata, and `run_migrations_online()`
- [ ] 1.8 Create `alembic/script.py.mako` template
- [ ] 1.9 Create `.env.example` with all required environment variables
- [ ] 1.10 Create `README.md` for microservice with setup instructions

## 2. Database Models & Migration (Exact UML Attributes)

### 2.1 Lectura Model (exact UML attributes)
- [ ] 2.1.1 Create `app/models/lectura.py` with SQLModel `Lectura` class and `__tablename__ = "lecturas"`
- [ ] 2.1.2 Attributes (exact from UML): `id` (int PK), `age` (int), `sex` (int), `cp` (int), `trestbps` (int), `chol` (int), `fbs` (bool), `restecg` (int), `thalach` (int), `exang` (bool), `oldpeak` (float), `slope` (int), `ca` (int), `thal` (int), `target` (bool nullable), `fechaCreacion` (datetime, auto)
- [ ] 2.1.3 Method: `exportarVector(): List[float]` — returns [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]

### 2.2 Evaluacion Model (exact UML attributes)
- [ ] 2.2.1 Create `app/models/evaluacion.py` with SQLModel `Evaluacion` class and `__tablename__ = "evaluaciones"`
- [ ] 2.2.2 Attributes (exact from UML): `id` (int PK), `fechaEvaluacion` (datetime, auto), `origenDatos` (str: "telemetria"|"manual"|"batch"), `paciente_id` (int FK → `pacientes.id` cross-module), `lectura_id` (int FK → `lecturas.id`), `prediccion_id` (int FK → `predicciones.id`)
- [ ] 2.2.3 Relationships: `lectura: Optional[Lectura] = Relationship()`, `prediccion: Optional[Prediccion] = Relationship()`

### 2.3 Prediccion Model (exact UML attributes)
- [ ] 2.3.1 Create `app/models/prediccion.py` with SQLModel `Prediccion` class and `__tablename__ = "predicciones"`
- [ ] 2.3.2 Attributes (exact from UML): `id` (int PK), `versionModelo` (str), `probabilidad` (float), `clasificacion` (str: "bajo"|"medio"|"alto"), `importanciaVariables` (dict, `sa_type=JSON`), `tiempoMs` (float), `fecha` (datetime, auto), `metadataTecnica` (dict, `sa_type=JSON`)
- [ ] 2.3.3 Method: `interpretarResultado(): String` — returns "Riesgo {clasificacion}: {probabilidad:.1%}"
- [ ] 2.3.4 Relationships: `evaluacion: Optional[Evaluacion] = Relationship()`, `documentos: List[Documento] = Relationship()`

### 2.4 Documento Model (exact UML attributes)
- [ ] 2.4.1 Create `app/models/documento.py` with SQLModel `Documento` class and `__tablename__ = "documentos"`
- [ ] 2.4.2 Attributes (exact from UML): `id` (int PK), `titulo` (str), `contenido` (str), `embedding` (List[float], `sa_column=Column(ARRAY(Float(384)))`), `fuente` (str), `fechaIndexacion` (datetime, auto), `activo` (bool), `prediccion_id` (int FK nullable → `predicciones.id`)
- [ ] 2.4.3 Method: `buscarSimilares(query): List[Documento]` — delegates to `RAGService`
- [ ] 2.4.4 Relationship: `prediccion: Optional[Prediccion] = Relationship()`

### 2.5 Adapter Model (exact UML attributes)
- [ ] 2.5.1 Create `app/models/adapter.py` with SQLModel `Adapter` class and `__tablename__ = "adapters"`
- [ ] 2.5.2 Attributes (exact from UML): `id` (int PK), `proveedor` (str: "n8n"|"langchain"|"manual"), `endpoint` (str), `flujo` (dict, `sa_type=JSON`), `token` (str), `activo` (bool), `fechaCreacion` (datetime, auto)
- [ ] 2.5.3 Methods: `ejecutarFlujo(triggerTipo: str, payload: dict): dict` — delegates to `WorkflowService`; `notificarUrgencia(medico_id: int, mensaje: str): bool` — delegates to `WorkflowService`
- [ ] 2.5.4 Implements `Workflow` interface (Protocol/ABC)

### 2.6 Migration & Exports
- [ ] 2.6 Create `app/models/__init__.py` exporting all 5 models
- [ ] 2.7 Create Alembic migration with `branch_labels = ("microservice",)` and `depends_on = "7468eec37172"`
- [ ] 2.8 Migration creates 5 tables: `lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`
- [ ] 2.9 Verify migration applies correctly against test PostgreSQL instance
- [ ] 2.10 Test rollback of migration

## 3. Predictor Service & Endpoints

- [ ] 3.1 Create `app/services/predictor_service.py` with `PredictorService` class: `load_model()`, `predict(features)`, `get_feature_importance()`
- [ ] 3.2 Implement `PredictorService` using `joblib.load()` to load `model.pkl`
- [ ] 3.3 Map prediction output (0-2) to `clasificacion`: "bajo" | "medio" | "alto"
- [ ] 3.4 Create `app/routers/predict.py` with `POST /predict` endpoint accepting exact 13 features (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal)
- [ ] 3.5 Response must include: `probabilidad`, `clasificacion`, `versionModelo`, `tiempoMs`, `importanciaVariables`, `explicacionClinica`
- [ ] 3.6 Create `app/routers/health.py` with `GET /health` endpoint checking DB, model, ChromaDB
- [ ] 3.7 Create `app/routers/__init__.py` with router aggregation
- [ ] 3.8 Wire routers into `main.py` with prefixes: `/predict`, `/evaluar`, `/agent`, `/workflow`, `/health`
- [ ] 3.9 Test `POST /predict` with valid payload using `pytest-asyncio` and `AsyncClient`
- [ ] 3.10 Test `POST /predict` with invalid payload (missing features, wrong types)
- [ ] 3.11 Test `GET /health` returns 200 when all dependencies are healthy

## 4. Notebook: EDA & Baseline Training

- [ ] 4.1 Create `notebooks/01-eda.ipynb` with heart dataset download from UCI, exploration, correlation matrix, distribution plots
- [ ] 4.2 Create `notebooks/02-baseline.ipynb` with RandomForest training, cross-validation, confusion matrix
- [ ] 4.3 Save trained model to `Project/microservice/data/model.pkl` using `joblib.dump()`
- [ ] 4.4 Generate feature importance plot and save to `data/feature_importance.png`
- [ ] 4.5 Document baseline metrics: accuracy, precision, recall, F1-score
- [ ] 4.6 Add `scripts/download_heart.py` script to download `heart.csv` from UCI repository
- [ ] 4.7 Add `.gitignore` entries for `data/*.csv`, `data/*.pkl`, `chroma_db/`, `notebooks/.ipynb_checkpoints/`

## 5. RAG Service (SentenceTransformer)

- [ ] 5.1 Create `app/services/rag_service.py` with `RAGService` class: `init_collection()`, `add_documents()`, `query()`, `get_collection_stats()`
- [ ] 5.2 Initialize ChromaDB `PersistentClient` with `path="./chroma_db"`
- [ ] 5.3 Create `get_or_create_collection("clinical_knowledge")` with metadata `{"hnsw:space": "cosine"}`
- [ ] 5.4 Use `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')` (NOT HuggingFaceEmbeddings)
- [ ] 5.5 Implement `query()` method: `model.encode(query)` → `collection.query()` with `n_results=5` → return documents
- [ ] 5.6 Add sample clinical knowledge documents to `data/knowledge_base/` (5-10 markdown files)
- [ ] 5.7 Create `scripts/bootstrap_chroma.py` to load knowledge base into ChromaDB on startup
- [ ] 5.8 Test `RAGService.query()` with sample clinical question
- [ ] 5.9 Verify ChromaDB persistence across restarts
- [ ] 5.10 Document RAG latency in `AGENTS.md` (target: <100ms)

## 6. LangChain Agent

- [ ] 6.1 Create `app/services/langchain_agent_service.py` with `AgentService` class: `init_agent()`, `query()`, `get_memory()`
- [ ] 6.2 Define 4 tools using `@tool` decorator:
  - `predict_cardiac_risk(features: list) -> dict`
  - `evaluate_triage(patient_data: dict) -> dict`
  - `generate_document(patient_id: int, doc_type: str) -> dict`
  - `search_knowledge(query: str) -> list`
- [ ] 6.3 Create agent using `create_agent()` with `llm`, `tools`, `InMemorySaver()`, and `prompt`
- [ ] 6.4 Implement `query()` method: `agent.invoke({"messages": [...]}, config={"configurable": {"thread_id": session_id}})`
- [ ] 6.5 Create `app/routers/agent.py` with `POST /agent/query` and `POST /agent/train` endpoints
- [ ] 6.6 `POST /agent/query` accepts `question` (str) and `session_id` (str, optional)
- [ ] 6.7 `POST /agent/train` accepts `dataset_path` (str) and optional `run_metaheuristics` (bool)
- [ ] 6.8 Test agent query with each of the 4 tools (mock external services)
- [ ] 6.9 Test session persistence with `InMemorySaver` (same `session_id` across 2 queries)
- [ ] 6.10 Document agent architecture in `AGENTS.md` (tool descriptions, prompt template, memory)

## 7. Metaheuristics Engine

- [ ] 7.1 Create `app/services/genetic_engine.py` with DEAP genetic algorithm for feature selection
- [ ] 7.2 Implement GA:
  - `creator.create("Fitness", base.Fitness, weights=(1.0,))`
  - `creator.create("Individual", list, fitness=creator.Fitness)`
  - `toolbox`: `random.randint(0,1)` for each of 13 features, `mate`, `mutate`, `select`
  - Population: 50, Generations: 20, Crossover: 0.7, Mutation: 0.2
  - Fitness: F1-score weighted of RandomForest on selected features
- [ ] 7.3 Create `app/services/pso_engine.py` with custom PSO implementation
- [ ] 7.4 Implement PSO:
  - `Particle` class: `position`, `velocity`, `best_position`, `best_fitness`
  - Swarm: 30 particles, Iterations: 30
  - Dimensions: `n_estimators` [10,200], `max_depth` [2,20], `min_samples_split` [2,10], `min_samples_leaf` [1,5]
  - Update: velocity = w*v + c1*r1*(pbest-x) + c2*r2*(gbest-x), position += velocity
  - Fitness: F1-score weighted of RandomForest with those hyperparameters
- [ ] 7.5 Add `run_metaheuristics()` method to `MetaheuristicsService`
- [ ] 7.6 Integrate metaheuristics into `POST /agent/train` endpoint
- [ ] 7.7 Store AG results in `Prediccion.importanciaVariables` (JSON)
- [ ] 7.8 Store PSO results in `Prediccion.metadataTecnica` (JSON)
- [ ] 7.9 Test GA feature selection with `heart.csv` dataset (assert best subset improves baseline)
- [ ] 7.10 Test PSO hyperparameter tuning (assert best params improve baseline)
- [ ] 7.11 Document metaheuristics in `AGENTS.md` (algorithm parameters, fitness functions, complexity)

## 8. Notebook: N3 Metrics & Visualizations

- [ ] 8.1 Create `notebooks/03-metaheuristics.ipynb` with:
  - GA: Convergence plot (best fitness vs generation), Feature importance bar chart
  - PSO: Convergence plot (best fitness vs iteration), Hyperparameter surface plot
- [ ] 8.2 Generate PPTX-ready charts (N2 Agent + N3 Metaheuristics)
- [ ] 8.3 Document N3 metrics: accuracy, F1-score, feature subset size, hyperparameter values
- [ ] 8.4 Add `notebooks/04-rag-evaluation.ipynb` with RAG evaluation metrics (retrieval accuracy, answer relevance)
- [ ] 8.5 Create `notebooks/05-metrics-n3.ipynb` with before/after comparison tables
- [ ] 8.6 Save all chart images to `data/charts/` for PPTX inclusion

## 9. Tests & Quality Assurance

- [ ] 9.1 Create `tests/conftest.py` with `async_engine` (SQLite in-memory), `async_session`, `test_client` fixtures
- [ ] 9.2 Create `tests/test_predictor.py` with tests for `POST /predict` (valid, invalid, model missing)
- [ ] 9.3 Create `tests/test_evaluar.py` with tests for `POST /evaluar` (valid payload, invalid payload, workflow trigger)
- [ ] 9.4 Create `tests/test_agent.py` with tests for `POST /agent/query` (4 tools, session persistence, empty question)
- [ ] 9.5 Create `tests/test_agent_train.py` with tests for `POST /agent/train` (dataset not found, metaheuristics)
- [ ] 9.6 Create `tests/test_workflow.py` with tests for `POST /workflow/trigger` (adapter found, not found, external failure)
- [ ] 9.7 Create `tests/test_health.py` with tests for `GET /health` (healthy, unhealthy)
- [ ] 9.8 Create `tests/test_models.py` with CRUD tests for all 5 SQLModel tables (`lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`)
- [ ] 9.9 Add `pytest.ini` with `asyncio_mode = auto` and `testpaths = tests`
- [ ] 9.10 Run full test suite and ensure coverage > 80% for services and routers

## 10. Documentation & Integration

- [ ] 10.1 Update `Project/microservice/AGENTS.md` with:
  - Architecture overview (5 models, 6 endpoints, 3 services)
  - API contract summary (request/response schemas with exact 13 features)
  - LangChain agent details (tools, prompt, memory, `create_agent()` + `InMemorySaver`)
  - Metaheuristics details (GA params: 50 ind × 20 gen, PSO params: 30 part × 30 iter)
  - RAG details (Chroma config, `SentenceTransformer` model, knowledge base)
  - Database schema (5 tables in plural, cross-module FKs)
  - Test instructions (pytest, SQLite, coverage > 80%)
  - Deployment notes (port 8001, env vars, model file, ChromaDB)
- [ ] 10.2 Update `Project/AGENTS.md` with microservice integration section (cross-module communication, `workflow_id` mapping)
- [ ] 10.3 Create `scripts/bootstrap.sh` to automate setup:
  - Install requirements
  - Download `heart.csv` from UCI
  - Run notebooks 01-02 (EDA + training)
  - Run `bootstrap_chroma.py`
  - Run Alembic migration
  - Start microservice
- [ ] 10.4 Verify end-to-end flow:
  - Backend calls `POST /predict` with exact 13 features → gets prediction with `clasificacion`, `probabilidad`, `versionModelo`
  - Backend calls `POST /evaluar` with n8n payload → gets `Evaluacion` with `paciente_id`, `lectura_id`, `prediccion_id`
  - Agent answers clinical question using RAG + prediction tools
  - Metaheuristics improve model performance (accuracy +9pp, features −46%)
  - Workflow triggers external Adapter via `ejecutarFlujo()`
- [ ] 10.5 Verify all 5 UML models implemented with exact attributes:
  - `Lectura`: 13 features + `target` + `fechaCreacion`
  - `Evaluacion`: `fechaEvaluacion`, `origenDatos`, `paciente_id`, `lectura_id`, `prediccion_id`
  - `Prediccion`: `versionModelo`, `probabilidad`, `clasificacion`, `importanciaVariables`, `tiempoMs`, `fecha`, `metadataTecnica`
  - `Documento`: `titulo`, `contenido`, `embedding` (ARRAY 384), `fuente`, `fechaIndexacion`, `activo`, `prediccion_id`
  - `Adapter`: `proveedor`, `endpoint`, `flujo`, `token`, `activo`, `fechaCreacion`
- [ ] 10.6 Verify rubric N2: LangChain Agent (`create_agent` + 4 tools + RAG + `InMemorySaver`) → PPTX slides
- [ ] 10.7 Verify rubric N3: DEAP AG (50 ind × 20 gen) + PSO manual (30 part × 30 iter) → PPTX slides
- [ ] 10.8 Verify all 5 tables are plural: `lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`
- [ ] 10.9 Final review: All tests pass, coverage > 80%, no lint errors, no security vulnerabilities
- [ ] 10.10 Archive change with `openspec archive change "microservicio-ia-corregido"`
- [ ] 10.11 Mark all 10 phases as complete in `tasks.md`
