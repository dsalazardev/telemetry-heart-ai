## Why

The Telemetry Heart AI project requires a dedicated microservice to process cardiac telemetry data using AI/ML techniques. The existing backend handles data ingestion but lacks the capability to perform real-time cardiac risk prediction, intelligent triage evaluation, and automated AI-assisted documentation. This microservice will provide the AI engine that powers the clinical workflow, enabling automated prediction, triage, and report generation.

## What Changes

- **New microservice**: Create a standalone FastAPI service on port 8001 with its own database models, services, and endpoints
- **5 new database models**: `Lectura`, `Evaluacion`, `Prediccion`, `Documento`, `Adapter` (SQLModel + PostgreSQL)
- **6 new API endpoints**: `POST /predict`, `POST /evaluar`, `POST /agent/query`, `POST /agent/train`, `POST /workflow/trigger`, `GET /health`
- **RandomForest predictor**: Trainable model for cardiac risk prediction using 13 features (age, sex, chest pain, etc.)
- **LangChain AI agent**: ReAct agent with 4 tools (predict_cardiac_risk, evaluate_triage, generate_document, search_knowledge) and persistent memory via `InMemorySaver`
- **RAG pipeline**: ChromaDB vector store with `sentence-transformers/all-MiniLM-L6-v2` embeddings for clinical knowledge retrieval
- **Metaheuristics engine**: DEAP-based genetic algorithm for feature selection + custom PSO implementation for hyperparameter tuning
- **Alembic migration**: Cross-project migration with `branch_labels` and `depends_on` the backend base migration
- **Test suite**: pytest-asyncio with SQLite in-memory for unit and integration tests
- **Documentation**: EDA notebooks, baseline training, and N3 metrics visualization

## Capabilities

### New Capabilities
- `ai-prediction`: Cardiac risk prediction via RandomForest with 13-feature input
- `ai-triage-evaluation`: Automated triage evaluation with score calculation and risk level determination
- `ai-agent`: LangChain ReAct agent with tool-based reasoning and persistent memory
- `ai-rag`: Retrieval-augmented generation for clinical knowledge queries
- `ai-metaheuristics`: Feature selection (AG) and hyperparameter tuning (PSO) via DEAP
- `ai-workflow`: Adapter-based workflow execution for external systems integration
- `ai-health`: Health check endpoint for service monitoring

### Modified Capabilities
- None (this is a greenfield microservice, no existing specs to modify)

## Impact

- **Code**: New directory `Project/microservice/` with ~55 files (models, services, routers, tests, notebooks, config)
- **Database**: New PostgreSQL schema with 5 tables. Shared Aiven Cloud instance. Cross-module FKs to `backend.Triaje` and `backend.Dispositivo`
- **APIs**: New service on port 8001. Backend `MicroserviceClient` calls `POST /predict` with timeout 10s
- **Dependencies**: FastAPI, SQLModel, LangChain, ChromaDB, DEAP, scikit-learn, sentence-transformers, torch (~200MB), joblib
- **Migration**: New Alembic migration depends on backend `7468eec37172_init` (conditional `depends_on` for test environments)
- **Rubric**: Covers N2 (LangChain Agent + RAG) and N3 (Metaheuristics) requirements
- **Integration**: Backend communicates via `MICROSERVICE_URL=http://localhost:8001`. `workflow_id` fields in backend models reference `Adapter.id` conceptually
