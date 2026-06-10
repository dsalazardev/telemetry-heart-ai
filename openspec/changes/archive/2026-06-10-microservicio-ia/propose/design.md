# Design.md

## Overview

Design for the `AGENTS.md` rewrite of the microservice module and parent index update.

## Structure of `Project/microservice/AGENTS.md`

Based on `backend/AGENTS.md` as template, with microservice-specific content:

```
microservice/AGENTS.md
├── # AGENTS.md — Microservicio IA
├── ## One-Liner (1 línea)
├── ## Stack Tecnológico (tabla con versión + propósito)
├── ## Arquitectura (árbol de directorios + descripción de capas)
├── ## Endpoints (tabla: método, ruta, servicio, descripción)
├── ## Comunicación con otros módulos (diagrama ASCII + bullets)
├── ## Convenciones (snake_case, singular, plural, sufijos)
├── ## Base de Datos (misma PostgreSQL, 5 tablas nuevas)
├── ## Modelos SQLModel (5 modelos con atributos exactos del UML)
├── ## Cobertura Rúbrica (N2 + N3, mapeo a PPTX y código)
├── ## Decisiones Arquitectónicas (ADRs 008-015)
├── ## Mapeo UML → Código (tabla: concepto UML → implementación)
└── ## Estructura de Directorios (árbol completo)
```

## Sections Detail

### One-Liner

> Capa aislada de Inteligencia Artificial para predicción de riesgo cardiovascular. Expone API REST (FastAPI :8001) con modelo predictivo (RandomForest), agente conversacional (LangChain + RAG), y metaheurísticas (DEAP AG + PSO).

### Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|-----------|
| Framework web | FastAPI | 0.136.3 | API REST async (puerto 8001) |
| ORM | SQLModel | 0.0.37 | Modelos BD + schemas Pydantic |
| Framework agent | LangChain | 0.3.0+ | `create_agent()` + `InMemorySaver` |
| Vector store | ChromaDB | 0.5.0+ | `PersistentClient` para RAG |
| Metaheurísticas | DEAP | 1.4.0+ | AG + PSO manual (`Particle` class) |
| Embeddings | sentence-transformers | 3.0+ | `all-MiniLM-L6-v2` (384d) |
| Clasificador | scikit-learn | 1.4.0+ | `RandomForestClassifier` |
| Base de datos | PostgreSQL | — | Misma BD que backend (Aiven Cloud) |
| Driver async | asyncpg | 0.30+ | Conexión PostgreSQL async |
| Testing | pytest + pytest-asyncio | 9.0+ / 0.24+ | Tests async |
| LLM | OpenAI (gpt-4o-mini) | — | Vía `langchain` |

### Arquitectura

Same pattern as backend: Clean / Hexagonal with layers:

```
microservice/
├── app/
│   ├── main.py              # FastAPI app, lifespan (load model, init Chroma)
│   ├── config.py            # Settings, env vars
│   ├── models/              # 5 SQLModel tables
│   ├── schemas/             # Pydantic request/response
│   ├── routers/             # APIRouter endpoints
│   ├── services/            # Business logic
│   ├── core/                # Database, security
│   └── utils/               # Utilities
├── tests/
├── notebooks/               # EDA, baseline, metrics
├── scripts/                 # train.py, bootstrap.sh
├── alembic/                 # Migrations (branch_labels)
└── requirements.txt
```

### Endpoints

| Método | Ruta | Servicio | Descripción |
|--------|------|----------|-------------|
| POST | `/predict` | predictor | 13 features → probabilidad |
| POST | `/evaluar` | predictor | Pipeline completo (Lectura → Prediccion → Evaluacion) |
| POST | `/agent/query` | langchain_agent | Chat agente con memoria (thread_id) |
| POST | `/agent/train` | predictor | Entrenar modelo con dataset |
| POST | `/workflow/trigger` | workflow_service | Ejecutar Adapter (n8n/langchain/manual) |
| GET | `/health` | — | Health check |

### Comunicación

```
Backend ─── HTTP/httpx ───▶ Microservice (:8001 /predict)
n8n ─────── HTTP/JSON ─────▶ Microservice (:8001 /evaluar, /workflow/trigger)
Microservice ◀── asyncpg ──▶ PostgreSQL (misma BD que backend)
```

### Convenciones

Same as backend:
- Files: `snake_case`
- Models: Singular (`Lectura`, `Prediccion`)
- Routers: Plural (`predict.py`, `evaluaciones.py`)
- Services: Suffix `_service` (`predictor_service.py`)
- Schemas: Operation suffix (`PredictRequest`, `PredictResponse`)
- Tests: Prefix `test_` (`test_predictor.py`)

### Base de Datos

Same PostgreSQL server as backend. 5 new tables:
1. `lecturas` — 13 features + target
2. `evaluaciones` — paciente_id (FK → pacientes.id), lectura_id, prediccion_id
3. `predicciones` — probabilidad, clasificacion, importanciaVariables (JSON)
4. `documentos` — contenido, embedding (ARRAY Float(384)), prediccion_id
5. `adapters` — proveedor, endpoint, flujo (JSON), token

Migration: `branch_labels=("microservice",)` + `depends_on="7468eec37172"`

### Modelos SQLModel

Exact from UML (lines 41-235 of Documents/Diagrama UML.md):

| Modelo | Stereotype | Tabla | Key Attributes |
|--------|-----------|-------|----------------|
| Lectura | `<<microservice>>` | `lecturas` | 13 features, target (nullable), `exportarVector()` |
| Evaluacion | `<<microservice>>` | `evaluaciones` | paciente_id (FK → pacientes.id), lectura_id, prediccion_id |
| Prediccion | `<<microservice>>` | `predicciones` | probabilidad, clasificacion, importanciaVariables (JSON), `interpretarResultado()` |
| Documento | `<<microservice>>` | `documentos` | embedding (ARRAY), prediccion_id (nullable), `buscarSimilares()` |
| Adapter | `<<n8n>>` | `adapters` | proveedor, endpoint, flujo (JSON), token, implements `Workflow` interface |

### Cobertura Rúbrica

#### N2 — LangChain (30% del nivel 2)

| PPTX | Criterio | Artefacto | Ctx7 |
|------|----------|-----------|------|
| 07 | LLM | `services/langchain_agent.py` — `model="openai:gpt-4o-mini"` | T1 |
| 07 | ChatPromptTemplate | System prompt + `medico_id` rule | T1 |
| 07 | Tools | 4 `@tool` decorators | T1 |
| 07 | Chain/Agent | `create_agent()` + `InMemorySaver()` + `thread_id` | T1 |
| 08 | Código | `notebooks/02-entrenamiento.ipynb` | — |
| 08 | CoT | `docs/ejemplo-cot.log` | — |
| 08 | RAG | `services/rag_service.py` — Chroma + `SentenceTransformer` | T3, T5 |
| 09 | Video | YouTube 4-10 min | — |

#### N3 — Metaheurísticas (20% del nivel 3)

| PPTX | Criterio | Artefacto | Ctx7 |
|------|----------|-----------|------|
| 10 | Selección | ADR-010 — AG + PSO combinados | T4 |
| 10 | Codificación | `services/genetic_engine.py` — binary 13 bits, fitness accuracy | T4 |
| 10 | Parámetros | 50 ind × 20 gen, tournament k=3, cxUniform p=0.8 | T4 |
| 10 | Parámetros PSO | `services/pso_engine.py` — `Particle` class, 30 part, 3 dim, 30 iter | T4 |
| 11 | Métrica #1 | Accuracy: 0.82 → 0.87 → 0.91 (+9pp) | — |
| 11 | Métrica #2 | Features: 13 → 7 (−46%) | — |
| 11 | Visualización | Curves convergence, confusion matrix | — |

### Decisiones Arquitectónicas

Reference ADRs 008-015 from `exploracion-definitiva.md`:
- ADR-008: Framework de Agente (`create_agent()` + `InMemorySaver`)
- ADR-009: Vector Store (Chroma `PersistentClient`)
- ADR-010: Metaheurísticas (DEAP AG + PSO manual)
- ADR-011: Clasificador (RandomForest)
- ADR-012: Embeddings (`sentence-transformers`)
- ADR-013: Memoria Agent (`InMemorySaver` + `thread_id`)
- ADR-014: Migración BD (`branch_labels` + `depends_on`)
- ADR-015: Modelo Adapter (corrección UML — 5º modelo es Adapter, no Optimizacion)

### Mapeo UML → Código

| Concepto UML | Implementación |
|-------------|---------------|
| Clase `<<microservice>>` | Modelo SQLModel en `models/` |
| `Lectura.exportarVector()` | Método del modelo |
| `Prediccion.interpretarResultado()` | Método del modelo |
| `Documento.buscarSimilares()` | Delegado a `services/rag_service.py` |
| `Adapter.ejecutarFlujo()` | Delegado a `services/workflow_service.py` |
| `Adapter.notificarUrgencia()` | Delegado a `services/workflow_service.py` |
| `Workflow` (interface) | Protocol/ABC en `services/workflow_service.py` |
| Relación `Evaluacion → Paciente` | `paciente_id` FK → `pacientes.id` (backend) |
| Relación `Triaje → Workflow` | `workflow_id` → `adapters.id` (conceptual) |
| `embedding: List~Float~` | `sa_column=Column(ARRAY(Float(384)))` |
| `importanciaVariables: JSON` | `sa_type=JSON` |

## Structure of `Project/AGENTS.md` Update

### Current (line 37)
```markdown
- [`/microservice`](./microservice/AGENTS.md) — Capa aislada de Inteligencia Artificial y modelo predictivo.
```

### Proposed
```markdown
- [`/microservice`](./microservice/AGENTS.md) — FastAPI + LangChain + Metaheurísticas. Predicción de riesgo cardiovascular (RandomForest), agente conversacional (RAG), y optimización (DEAP AG + PSO manual).
```

### Stack section addition (after line 52)
```markdown
### Microservice Stack
- [LangChain Python](https://python.langchain.com/) — Agent framework (v0.3.0+, `create_agent()` + `InMemorySaver`)
- [ChromaDB](https://docs.trychroma.com/) — Vector store para RAG (`PersistentClient`)
- [DEAP](https://deap.readthedocs.io/) — Metaheurísticas (AG + PSO manual)
- [sentence-transformers](https://www.sbert.net/) — Embeddings (`all-MiniLM-L6-v2`, 384d)
- [scikit-learn](https://scikit-learn.org/) — Clasificador (`RandomForestClassifier`)
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Match backend structure | Consistency across all module AGENTS.md files |
| Include exact UML attributes | Source of truth from `Diagrama UML.md` |
| Document cross-module FKs | `paciente_id` → `pacientes.id`, `workflow_id` → `adapters.id` |
| Separate N2 and N3 tables | Clear rubric mapping for implementation phase |
| Reference ADRs by number | Traceability to `exploracion-definitiva.md` |

## Risks

| Risk | Mitigation |
|------|------------|
| Parent AGENTS.md format mismatch | Copy exact structure from backend AGENTS.md |
| Missing model attribute | Cross-reference line-by-line with UML diagram |
| Incorrect rubric weights | Use exact percentages from Rubric/Proyecto final_SI1_UCaldas.md |

## Status

- **Phase:** PROPOSE
- **Ready for:** IMPLEMENT

## References

- `exploracion-definitiva.md` — Source of truth
- `backend/AGENTS.md` — Template
- `Diagrama UML.md` — 5 models
- `Rubric/Proyecto final_SI1_UCaldas.md` — Rubric
- `microservice/AGENTS.md` — Current stub (to be rewritten)
