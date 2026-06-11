## Context

The Telemetry Heart AI project is a multi-module system for cardiac telemetry monitoring. The existing backend (`Project/backend/`) handles data ingestion via `Triaje` and `Dispositivo` models. The backend communicates with an external AI microservice via `MicroserviceClient` (`POST /predict`, 10s timeout). The `workflow_id` fields in `Triaje` and `Dispositivo` are `Optional[int] = None` with no FK constraint, but conceptually reference the `Adapter` table in the microservice. The microservice needs to be a standalone FastAPI application on port 8001, sharing the same PostgreSQL Aiven Cloud database as the backend. The project must satisfy the academic rubric (N2: LangChain Agent + RAG, N3: Metaheuristics).

## Goals / Non-Goals

**Goals:**
- Implement a complete FastAPI microservice on port 8001 with 5 SQLModel tables
- Provide a trained RandomForest model for cardiac risk prediction (13 features → 3 classes)
- Implement a LangChain ReAct agent with 4 tools and persistent memory (`InMemorySaver`)
- Implement RAG pipeline with ChromaDB and sentence-transformers embeddings
- Implement DEAP-based genetic algorithm for feature selection and custom PSO for hyperparameter tuning
- Provide 6 API endpoints with proper request/response contracts
- Create Alembic migration with cross-project dependency on backend base migration
- Provide tests (pytest-asyncio) and documentation (notebooks, AGENTS.md)

**Non-Goals:**
- Real-time streaming inference (batch/REST only)
- GPU acceleration (CPU-only PyTorch)
- Multi-tenant isolation
- Authentication/authorization (handled by backend gateway)
- Model versioning and A/B testing (single model deployment)
- Complex MLOps pipeline (manual training via notebooks)

## Decisions

### 1. LangChain v0.3+ API (create_agent + InMemorySaver)
**Decision**: Use `create_agent()` from `langchain.agents` with `InMemorySaver` for memory, NOT legacy `AgentExecutor`.
**Rationale**: The `AgentExecutor` class is deprecated in v0.3.x. The new `create_agent()` factory function with `thread_id` is the recommended API. This provides built-in checkpoint persistence and native tool integration.
**Alternatives considered**: `AgentExecutor` (legacy, deprecated), `create_structured_chat_agent` (more complex, not needed for ReAct).
**Impact**: All agent code must use the new API. `InMemorySaver` provides in-memory persistence; for production, it could be replaced with PostgreSQL persistence.

### 2. SQLModel with ARRAY and JSON columns
**Decision**: Use `sa_column=Column(ARRAY(Float(384)))` for embedding vectors and `sa_type=JSON` for flexible metadata fields.
**Rationale**: SQLModel 0.0.22 supports `sa_column` for SQLAlchemy-specific types and `sa_type=JSON` for JSON fields. The `ARRAY` type is needed for ChromaDB embedding vectors (384 dimensions). `JSON` is needed for `importanciaVariables`, `metadataTecnica`, `flujo` (complex nested data).
**Alternatives considered**: Separate table for embeddings (overkill), Pydantic model as JSON string (loses queryability), native Python list (not supported by SQLModel for PostgreSQL).
**Impact**: Requires `sqlalchemy.dialects.postgresql.ARRAY` and `sqlalchemy.JSON` imports.

### 3. ChromaDB PersistentClient
**Decision**: Use `chromadb.PersistentClient(path="./chroma_db")` for local vector storage.
**Rationale**: The client-server mode (`chromadb.HttpClient`) is the recommended architecture for production, but the PersistentClient provides simpler local deployment suitable for a microservice. Data persists across restarts.
**Alternatives considered**: `HttpClient` (requires separate Chroma server, adds complexity), `sqlite3` (no vector search), `faiss` (lower-level, no document management).
**Impact**: `./chroma_db/` directory must be created and excluded from git. Persistence is file-based.

### 4. Sentence-Transformers Embeddings
**Decision**: Use `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) via `HuggingFaceEmbeddings`.
**Rationale**: This model is lightweight, fast on CPU, and widely used for semantic search. The 384 dimensions are sufficient for clinical knowledge retrieval. `HuggingFaceEmbeddings` wraps it for LangChain compatibility.
**Alternatives considered**: `OpenAIEmbeddings` (requires API key, not free), `all-mpnet-base-v2` (768d, slower, marginal quality improvement), `instructor-xl` (too heavy for CPU).
**Impact**: Requires `torch` (~200MB) and `sentence-transformers` packages. Install with `--index-url https://download.pytorch.org/whl/cpu` for CPU-only.

### 5. DEAP for Metaheuristics
**Decision**: Use DEAP for the genetic algorithm (feature selection) and a custom PSO implementation (not DEAP's built-in PSO).
**Rationale**: DEAP provides a flexible framework for evolutionary algorithms. For AG (feature selection), DEAP's `creator` and `toolbox` are perfect. For PSO, DEAP has no mature PSO module; the custom implementation is ~100 lines and more transparent for academic demonstration (N3 rubric).
**Alternatives considered**: `pyswarm` (abandoned, Python 2 only), `optuna` (Bayesian optimization, not population-based), `scikit-optimize` (GP, not evolutionary).
**Impact**: DEAP must be installed. PSO requires custom `Particle` class and update loop.

### 6. RandomForest + joblib
**Decision**: Use `RandomForestClassifier` from scikit-learn, serialized with `joblib`.
**Rationale**: RandomForest is robust, interpretable, and provides `feature_importances_` which is useful for PPTX 11. `joblib` is the recommended serialization format for sklearn models (handles numpy arrays efficiently).
**Alternatives considered**: `XGBoost` (better performance but harder to deploy), `LogisticRegression` (too simple, no feature importance), `SVM` (slower, no probability natively).
**Impact**: Model file `model.pkl` will be ~1-5MB. Must be loaded at startup.

### 7. Project Structure
**Decision**: Mirror backend structure: `app/models/`, `app/services/`, `app/routers/`, `app/core/`, `tests/`, `notebooks/`.
**Rationale**: Consistency with the existing backend makes it easier for the development team to navigate. The `app/` pattern is standard for FastAPI.
**Alternatives considered**: Flat structure (harder to scale), separate package (more complex imports).
**Impact**: All files must follow the same naming convention: snake_case for modules, CamelCase for classes.

### 8. Cross-Module Database Migration
**Decision**: Use `branch_labels` and `depends_on` for the Alembic migration to create a dependency on the backend's base migration.
**Rationale**: The microservice shares the same database. The migration must run after the backend's initial migration (`7468eec37172`). `branch_labels` allows the migration to be identified as belonging to the microservice branch. `depends_on` ensures ordering.
**Alternatives considered**: Separate database (violates shared DB requirement), manual migration (error-prone), no dependency (risk of table creation before backend tables exist).
**Impact**: The migration file must include `branch_labels = ("microservice",)` and `depends_on = "7468eec37172"`. In test environments where the backend migration doesn't exist, the migration runs independently.

### 9. SQLite for Tests Only
**Decision**: Use SQLite in-memory for tests, PostgreSQL for production.
**Rationale**: The project explicitly prohibits SQLite in production. However, SQLite in-memory is acceptable for fast unit tests. PostgreSQL is used in production via the same Aiven Cloud instance as the backend.
**Alternatives considered**: PostgreSQL for tests (slower, requires Docker), mock database (loses integration coverage).
**Impact**: `database.py` must switch between SQLite and PostgreSQL based on environment. `create_async_engine("sqlite+aiosqlite:///:memory:")` for tests.

## Risks / Trade-offs

### [LangChain API Instability] → Mitigation: Pin exact version and wrap in service layer
LangChain v0.3+ is relatively new and API changes may occur. We will pin `langchain==0.3.x` and `langchain-openai==0.2.x` in `requirements.txt`. All LangChain calls are wrapped in `AgentService` to localize changes.

### [torch 200MB Dependency] → Mitigation: CPU-only install + Docker multi-stage build
The `torch` package is ~200MB. We will install with `--index-url https://download.pytorch.org/whl/cpu` to avoid GPU dependencies. For Docker, use a multi-stage build to keep the final image small.

### [DEAP PSO Manual Implementation] → Mitigation: Thorough unit tests + documented algorithm
The custom PSO is ~100 lines but could have bugs. We will write comprehensive unit tests for the `Particle` class and update loop. The algorithm will be documented in the code comments and in a markdown file.

### [Dataset Not in Repository] → Mitigation: Download script in bootstrap
The `heart.csv` dataset is not in the repo. We will include a `download_heart.py` script in the bootstrap process that downloads from Kaggle or UCI.

### [Cross-Module FKs Without Enforcement] → Mitigation: Document + soft validation
The `workflow_id` fields in backend models have no FK constraint. The microservice will not enforce referential integrity. We will document this in AGENTS.md and add soft validation in the `AdapterService`.

### [Latency Budget] → Mitigation: Async endpoints + caching
Total latency: Chroma 5ms + embeddings 50ms + LLM 2-4s + predict 1ms = ~2-5s. This is within the 10s backend timeout. We will use async endpoints and add optional Redis caching for predictions.

## Migration Plan

1. **Phase 1**: Deploy new tables via Alembic migration (5 tables)
2. **Phase 2**: Start microservice on port 8001 (independent of backend)
3. **Phase 3**: Update backend `MICROSERVICE_URL` to point to production microservice
4. **Phase 4**: Train model via notebook and save `model.pkl` to shared storage
5. **Phase 5**: Run bootstrap script to populate ChromaDB with clinical knowledge
6. **Rollback**: Stop microservice. Database tables remain (no data loss). Backend falls back to no AI mode.

## Open Questions

1. **LLM Provider**: OpenAI API vs local LLM (Ollama)? For the academic project, OpenAI is simpler but requires API key. Decision: Use OpenAI with `OPENAI_API_KEY` env var, but structure code to allow Ollama fallback.
2. **Dataset Source**: Kaggle or UCI? The `heart.csv` dataset is available on both. Decision: Use UCI (direct download, no API key needed).
3. **Chroma Persistence Path**: Should it be in a Docker volume or local directory? Decision: Local `./chroma_db/` for development, Docker volume for production.
4. **PSO Hyperparameter Space**: What are the hyperparameters to optimize? Decision: RandomForest `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`.
5. **AG Fitness Function**: Use accuracy or F1-score? Decision: Use F1-score weighted to handle class imbalance.
