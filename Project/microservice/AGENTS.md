# AGENTS.md — Microservicio IA

**One-Liner:** Capa aislada de Inteligencia Artificial para predicción de riesgo cardiovascular. Expone API REST (FastAPI :8001) con modelo predictivo (RandomForest), agente conversacional (LangChain + RAG), y metaheurísticas (DEAP AG + PSO).

---

## Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|-----------|
| Framework web | FastAPI | 0.136.3 | API REST async (puerto 8001) |
| ORM | SQLModel | 0.0.37 | Modelos BD + schemas Pydantic unificados |
| Framework agent | LangChain | 0.3.0+ | `create_agent()` + `InMemorySaver` (ctx7 T1) |
| Vector store | ChromaDB | 0.5.0+ | `PersistentClient` para RAG (ctx7 T3) |
| Metaheurísticas | DEAP | 1.4.0+ | AG + PSO manual (`Particle` class, ctx7 T4) |
| Embeddings | sentence-transformers | 3.0+ | `all-MiniLM-L6-v2` (384d, ctx7 T5) |
| Clasificador | scikit-learn | 1.4.0+ | `RandomForestClassifier` |
| Base de datos | PostgreSQL | — | Misma BD que backend (Aiven Cloud) |
| Driver async | asyncpg | 0.30+ | Conexión PostgreSQL async |
| Testing | pytest + pytest-asyncio | 9.0+ / 0.24+ | Tests async |
| LLM | OpenAI (gpt-4o-mini) | — | Vía `langchain` |

---

## Arquitectura

Limpia / Hexagonal con capas organizadas según la guía oficial de FastAPI "Bigger Applications":

```
microservice/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan (load model, init Chroma)
│   ├── config.py            # Settings, env vars via pydantic-settings
│   │
│   ├── models/              # SQLModel (5 tablas de BD)
│   │   ├── __init__.py
│   │   ├── lectura.py       # Lectura (13 features + target)
│   │   ├── evaluacion.py    # Evaluacion (FK a pacientes, lecturas, predicciones)
│   │   ├── prediccion.py    # Prediccion (probabilidad, clasificacion, JSON)
│   │   ├── documento.py     # Documento (RAG: contenido, embedding ARRAY)
│   │   └── adapter.py       # Adapter (Workflow: proveedor, endpoint, flujo, token)
│   │
│   ├── schemas/             # Pydantic (request/response, no BD)
│   │   ├── __init__.py
│   │   ├── predict.py       # PredictRequest, PredictResponse
│   │   ├── evaluar.py       # EvaluarRequest, EvaluarResponse
│   │   ├── agent.py         # AgentQuery, AgentResponse
│   │   └── workflow.py      # WorkflowTrigger, WorkflowResponse
│   │
│   ├── routers/             # APIRouter (endpoints REST)
│   │   ├── __init__.py
│   │   ├── predict.py       # POST /predict
│   │   ├── evaluar.py       # POST /evaluar
│   │   ├── agent.py         # POST /agent/query, /agent/train
│   │   ├── workflow.py      # POST /workflow/trigger
│   │   └── health.py        # GET /health
│   │
│   ├── services/            # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── predictor_service.py      # RandomForest: train, predict, save, load
│   │   ├── langchain_agent_service.py # create_agent() + 4 tools + InMemorySaver
│   │   ├── rag_service.py            # Chroma PersistentClient + SentenceTransformer
│   │   ├── workflow_service.py       # Adapter.ejecutarFlujo + notificarUrgencia
│   │   ├── genetic_engine.py         # DEAP AG: feature selection
│   │   └── pso_engine.py             # DEAP PSO manual: hyperparameters
│   │
│   ├── core/                # Configuración central
│   │   ├── __init__.py
│   │   ├── database.py      # Engine, session factory
│   │   └── settings.py      # pydantic-settings (env vars)
│   │
│   └── utils/               # Utilidades
│       ├── __init__.py
│       └── embeddings.py    # Wrapper SentenceTransformer
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures: test db, client, agent
│   ├── test_predictor.py
│   ├── test_agent.py
│   ├── test_rag.py
│   ├── test_genetic.py
│   └── test_pso.py
│
├── notebooks/               # Jupyter notebooks
│   ├── 01-eda.ipynb         # EDA dataset heart.csv
│   ├── 02-baseline.ipynb    # RandomForest baseline
│   ├── 03-feature-importance.ipynb  # feature_importances_
│   ├── 04-metaheuristics.ipynb      # AG + PSO visualización
│   └── 05-metrics-n3.ipynb  # Métricas antes/después
│
├── scripts/
│   ├── bootstrap.sh         # Descargar heart.csv, instalar deps
│   ├── train.py             # Entrenar modelo .pkl
│   └── evaluate.py          # Evaluar métricas
│
├── alembic/                 # Migraciones automáticas
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

---

## Endpoints Principales

| Método | Ruta | Servicio | Descripción |
|--------|------|----------|-------------|
| POST | `/predict` | predictor_service | 13 features → probabilidad de riesgo |
| POST | `/evaluar` | predictor_service | Pipeline completo: Lectura → Prediccion → Evaluacion |
| POST | `/agent/query` | langchain_agent_service | Chat agente con memoria (thread_id=medico_id) |
| POST | `/agent/train` | predictor_service | Entrenar modelo con dataset |
| POST | `/workflow/trigger` | workflow_service | Ejecutar Adapter (n8n/langchain/manual) |
| GET | `/health` | — | Health check |

---

## Comunicación con otros módulos

```
Backend ─── HTTP/httpx ───▶ Microservice (:8001 /predict, /evaluar)
n8n ─────── HTTP/JSON ─────▶ Microservice (:8001 /evaluar, /workflow/trigger)
Microservice ◀── asyncpg ──▶ PostgreSQL (misma BD que backend)
```

- **Con backend**: HTTP síncrono vía `httpx.AsyncClient` desde `services/microservice_client.py` (backend)
- **Con n8n**: Webhooks REST — n8n llama al microservicio para ejecutar evaluaciones y workflows
- **Con PostgreSQL**: Misma base de datos que backend, 5 tablas nuevas (`lecturas`, `evaluaciones`, `predicciones`, `documentos`, `adapters`)

---

## Convenciones

- **Archivos**: `snake_case`
- **Modelos**: Singular (`Lectura`, `Prediccion`) — SQLModel usa el nombre de la clase como tabla
- **Routers**: Plural (`predict.py`, `evaluaciones.py`)
- **Servicios**: Sufijo `_service` (`predictor_service.py`, `langchain_agent_service.py`)
- **Schemas**: Sufijo de operación (`PredictRequest`, `PredictResponse`, `EvaluarRequest`)
- **Endpoints**: Plural (`/predict`, `/evaluar`)
- **Tests**: Prefijo `test_` + `_` + nombre del módulo (`test_predictor.py`)
- **BD**: PostgreSQL en Aiven Cloud (remoto), conexión vía URL con python-dotenv
- **Notebooks**: Prefijo numérico (`01-eda.ipynb`, `02-baseline.ipynb`)
- **Scripts**: Verbo en infinitivo (`train.py`, `evaluate.py`, `bootstrap.sh`)

---

## Base de Datos

**Misma instancia PostgreSQL que backend** (Aiven Cloud). El microservicio agrega 5 tablas nuevas:

1. **`lecturas`** — 13 features cardiovascular + target (nullable)
2. **`evaluaciones`** — paciente_id (FK → `pacientes.id`), lectura_id, prediccion_id
3. **`predicciones`** — probabilidad, clasificacion, importanciaVariables (JSON), metadataTecnica (JSON)
4. **`documentos`** — contenido, embedding (ARRAY Float(384)), fuente, prediccion_id (nullable)
5. **`adapters`** — proveedor, endpoint, flujo (JSON), token

**Migración**: `branch_labels=("microservice",)` + `depends_on="7468eec37172"` (ctx7 T6)

```bash
alembic revision -m "add microservice tables" \
    --head=microservice@head \
    --depends-on=7468eec37172
```

---

## Modelos SQLModel

Basados en las clases `<<microservice>>` y `<<n8n>>` del diagrama UML:

### Lectura (`<<microservice>>`)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | int PK | Auto-incremental |
| age | int | Edad en años |
| sex | int | 1 = masculino, 0 = femenino |
| cp | int | Tipo de dolor torácico (0-3) |
| trestbps | int | Presión arterial en reposo (mmHg) |
| chol | int | Colesterol sérico (mg/dl) |
| fbs | bool | Glucosa en ayunas > 120 mg/dl |
| restecg | int | Resultados electrocardiográficos (0-2) |
| thalach | int | Frecuencia cardíaca máxima alcanzada |
| exang | bool | Angina inducida por ejercicio |
| oldpeak | float | Depresión ST inducida por ejercicio |
| slope | int | Pendiente del segmento ST (0-2) |
| ca | int | Número de vasos principales coloreados (0-3) |
| thal | int | Talasemia (0-3) |
| target | bool nullable | null = pendiente, true = enfermo, false = sano |
| fechaCreacion | datetime | Timestamp automático |

**Método**: `exportarVector(): List[float]` — devuelve las 13 features como vector numérico

### Evaluacion (`<<microservice>>`)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | int PK | Auto-incremental |
| fechaEvaluacion | datetime | Timestamp automático |
| origenDatos | str | "telemetria" \| "manual" \| "batch" |
| paciente_id | int FK | → `pacientes.id` (backend, cross-module) |
| lectura_id | int FK | → `lecturas.id` |
| prediccion_id | int FK | → `predicciones.id` |

### Prediccion (`<<microservice>>`)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | int PK | Auto-incremental |
| versionModelo | str | Versión del modelo (ej: "rf-v1.2") |
| probabilidad | float | Probabilidad de riesgo (0.0 - 1.0) |
| clasificacion | str | "bajo" \| "medio" \| "alto" |
| importanciaVariables | JSON | Dict con feature_importances_ |
| tiempoMs | float | Tiempo de inferencia en milisegundos |
| fecha | datetime | Timestamp automático |
| metadataTecnica | JSON | Config del modelo, hiperparámetros, etc. |

**Método**: `interpretarResultado(): String` — devuelve "Riesgo {clasificacion}: {probabilidad:.1%}"

### Documento (`<<microservice>>`)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | int PK | Auto-incremental |
| titulo | str | Título del documento clínico |
| contenido | str | Texto completo |
| embedding | ARRAY(Float(384)) | Vector de 384 dimensiones (ctx7 T2: `sa_column=Column(ARRAY(Float(384)))`) |
| fuente | str | Origen del documento |
| fechaIndexacion | datetime | Timestamp automático |
| activo | bool | ¿Disponible para RAG? |
| prediccion_id | int FK nullable | → `predicciones.id` |

**Método**: `buscarSimilares(query): List[Documento]` — delegado a `RAGService`

### Adapter (`<<n8n>>`)

Implementa la interfaz `Workflow` del UML.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| id | int PK | Auto-incremental |
| proveedor | str | "n8n" \| "langchain" \| "manual" |
| endpoint | str | URL del webhook o endpoint |
| flujo | JSON | Configuración del workflow (ctx7 T2: `sa_type=JSON`) |
| token | str | Auth token si aplica |
| activo | bool | ¿Activo? |
| fechaCreacion | datetime | Timestamp automático |

**Métodos**:
- `ejecutarFlujo(triggerTipo: str, payload: dict): dict` — delegado a `WorkflowService`
- `notificarUrgencia(medico_id: int, mensaje: str): bool` — delegado a `WorkflowService`

**Relaciones cross-module**:
- `Triaje.workflow_id` (backend) → `adapters.id` (conceptual)
- `Evento.workflow_id` (backend) → `adapters.id` (conceptual)

---

## Cobertura Rúbrica

### N2 — LangChain (30% del nivel 2)

| PPTX | Criterio | Artefacto | Ctx7 |
|------|----------|-----------|------|
| 07 | LLM | `services/langchain_agent_service.py` — `model="openai:gpt-4o-mini"` | T1 |
| 07 | ChatPromptTemplate | System prompt + regla `medico_id` | T1 |
| 07 | Tools | 4 `@tool` decorators (predict_risk, query_patients, rag_explain, format_response) | T1 |
| 07 | Chain/Agent | `create_agent()` + `InMemorySaver()` + `thread_id` | T1 |
| 08 | Código | `notebooks/02-baseline.ipynb` (fragmento Python) | — |
| 08 | CoT | `docs/ejemplo-cot.log` — log del loop ReAct | — |
| 08 | RAG | `services/rag_service.py` — Chroma + `SentenceTransformer` | T3, T5 |
| 09 | Video | YouTube 4-10 min demostración | — |

### N3 — Metaheurísticas (20% del nivel 3)

| PPTX | Criterio | Artefacto | Ctx7 |
|------|----------|-----------|------|
| 10 | Selección | ADR-010 — AG + PSO combinados | T4 |
| 10 | Codificación | `services/genetic_engine.py` — binario 13 bits, fitness = accuracy | T4 |
| 10 | Parámetros | 50 ind × 20 gen, torneo k=3, cxUniform p=0.8 | T4 |
| 10 | Parámetros PSO | `services/pso_engine.py` — `Particle` class, 30 part, 3 dim, 30 iter | T4 |
| 11 | Métrica #1 | Accuracy: 0.82 → 0.87 → 0.91 (+9 puntos porcentuales) | — |
| 11 | Métrica #2 | Features: 13 → 7 (−46%) | — |
| 11 | Visualización | Curvas de convergencia, matriz de confusión | — |

---

## Decisiones Arquitectónicas

Ver `exploracion-definitiva.md` para detalles completos de cada ADR:

- **ADR-008**: Framework de Agente — `create_agent()` + `InMemorySaver` (ctx7 T1)
- **ADR-009**: Vector Store — Chroma `PersistentClient` (ctx7 T3)
- **ADR-010**: Metaheurísticas — DEAP AG + PSO manual (ctx7 T4)
- **ADR-011**: Clasificador — RandomForest (`feature_importances_` directo)
- **ADR-012**: Embeddings — `sentence-transformers/all-MiniLM-L6-v2` (ctx7 T5)
- **ADR-013**: Memoria Agent — `InMemorySaver()` + `thread_id` (ctx7 T1)
- **ADR-014**: Migración BD — `branch_labels` + `depends_on` (ctx7 T6)
- **ADR-015**: Modelo Adapter — Corrección UML: 5º modelo es Adapter, no Optimizacion

---

## Mapeo UML → Código

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
| `embedding: List~Float~` | `sa_column=Column(ARRAY(Float(384)))` (ctx7 T2) |
| `importanciaVariables: JSON` | `sa_type=JSON` (ctx7 T2) |
| `flujo: Object` | `sa_type=JSON` (ctx7 T2) |

---

## Estructura de Directorios

```
Project/microservice/
├── app/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── config.py               # Settings
│   ├── models/
│   │   ├── lectura.py          # 13 features + target
│   │   ├── evaluacion.py       # FK a pacientes, lecturas, predicciones
│   │   ├── prediccion.py       # probabilidad + JSON
│   │   ├── documento.py        # RAG: embedding ARRAY(384)
│   │   └── adapter.py          # Workflow: proveedor, endpoint, flujo
│   ├── schemas/
│   │   ├── predict.py          # PredictRequest/Response
│   │   ├── evaluar.py          # EvaluarRequest/Response
│   │   ├── agent.py            # AgentQuery/Response
│   │   └── workflow.py         # WorkflowTrigger/Response
│   ├── routers/
│   │   ├── predict.py          # POST /predict
│   │   ├── evaluar.py          # POST /evaluar
│   │   ├── agent.py            # POST /agent/query, /agent/train
│   │   ├── workflow.py         # POST /workflow/trigger
│   │   └── health.py           # GET /health
│   ├── services/
│   │   ├── predictor_service.py         # RandomForest
│   │   ├── langchain_agent_service.py  # create_agent + 4 tools
│   │   ├── rag_service.py             # Chroma + embeddings
│   │   ├── workflow_service.py        # Adapter + notificaciones
│   │   ├── genetic_engine.py          # DEAP AG
│   │   └── pso_engine.py              # DEAP PSO manual
│   ├── core/
│   │   ├── database.py         # Engine + session
│   │   └── settings.py         # pydantic-settings
│   └── utils/
│       └── embeddings.py       # SentenceTransformer wrapper
├── tests/
│   ├── conftest.py             # Fixtures
│   ├── test_predictor.py
│   ├── test_agent.py
│   ├── test_rag.py
│   ├── test_genetic.py
│   └── test_pso.py
├── notebooks/
│   ├── 01-eda.ipynb            # EDA
│   ├── 02-baseline.ipynb       # Baseline
│   ├── 03-feature-importance.ipynb
│   ├── 04-metaheuristics.ipynb
│   └── 05-metrics-n3.ipynb     # Métricas
├── scripts/
│   ├── bootstrap.sh            # Setup
│   ├── train.py                # Entrenar .pkl
│   └── evaluate.py             # Métricas
├── alembic/                    # Migraciones
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

---

## Referencias

- `../Documents/Diagrama UML.md` — 5 modelos exactos del sistema
- `../Rubric/Proyecto final_SI1_UCaldas.md` — Rúbrica N2 + N3
- `../openspec/changes/microservicio-ia/exploracion-definitiva.md` — ADRs y validación ctx7
- `../Project/backend/AGENTS.md` — Template de estructura y convenciones
- `../Project/backend/app/services/microservice_client.py` — Contrato HTTP con backend
- `../Project/backend/app/core/settings.py` — `MICROSERVICE_URL = "http://localhost:8001"`
- `../Project/backend/alembic/versions/7468eec37172_init.py` — Migración base (depends_on)
