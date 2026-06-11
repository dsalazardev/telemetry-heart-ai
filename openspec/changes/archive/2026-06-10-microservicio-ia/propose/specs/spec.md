# Spec.md

## Requisitos del AGENTS.md del Microservicio

## Funcionales

### RF-1: Stack Documentado
El AGENTS.md debe listar **todos** los componentes tecnológicos con:
- Nombre de la tecnología
- Versión mínima (validada con ctx7)
- Propósito en una frase

**Tecnologías obligatorias:**
1. FastAPI (framework web)
2. SQLModel (ORM)
3. LangChain (agente, v0.3.0+ con `create_agent()`)
4. ChromaDB (vector store, `PersistentClient`)
5. DEAP (metaheurísticas, AG + PSO manual)
6. sentence-transformers (embeddings, `all-MiniLM-L6-v2`)
7. scikit-learn (RandomForestClassifier)
8. PostgreSQL (misma BD que backend)
9. asyncpg (driver async)
10. pytest + pytest-asyncio (testing)
11. OpenAI / gpt-4o-mini (LLM)

### RF-2: Modelos Exactos del UML
Deben documentarse los **5 modelos** con atributos exactos de `Documents/Diagrama UML.md`:

1. **Lectura** (`<<microservice>>`)
   - 13 features: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
   - target: bool nullable
   - Method: `exportarVector(): List~Float~`

2. **Evaluacion** (`<<microservice>>`)
   - fechaEvaluacion, origenDatos
   - FK: paciente_id → pacientes.id (cross-module)
   - FK: lectura_id → lecturas.id
   - FK: prediccion_id → predicciones.id

3. **Prediccion** (`<<microservice>>`)
   - versionModelo, probabilidad, clasificacion
   - importanciaVariables: JSON
   - tiempoMs, fecha, metadataTecnica: JSON
   - Method: `interpretarResultado(): String`

4. **Documento** (`<<microservice>>`)
   - titulo, contenido, embedding: ARRAY Float
   - fuente, fechaIndexacion, activo
   - FK: prediccion_id → predicciones.id (nullable)
   - Method: `buscarSimilares(query): List~Documento~`

5. **Adapter** (`<<n8n>>`)
   - proveedor, endpoint, flujo: Object/JSON, token
   - Implements: `Workflow` (`<<Interface>>`)
   - Methods: `ejecutarFlujo(triggerTipo, payload): JSON`, `notificarUrgencia(medico, mensaje): Boolean`
   - Referenced by: Triaje.workflow_id, Evento.workflow_id

### RF-3: Endpoints Documentados
Deben listarse **6 endpoints** con: método, ruta, servicio, descripción:

| # | Método | Ruta | Servicio |
|---|--------|------|----------|
| 1 | POST | `/predict` | predictor |
| 2 | POST | `/evaluar` | predictor |
| 3 | POST | `/agent/query` | langchain_agent |
| 4 | POST | `/agent/train` | predictor |
| 5 | POST | `/workflow/trigger` | workflow_service |
| 6 | GET | `/health` | — |

### RF-4: Comunicación Cross-Module
Debe documentarse:
- Backend → Microservice: HTTP/httpx (:8001)
- n8n → Microservice: HTTP/JSON (:8001)
- Microservice → PostgreSQL: asyncpg (misma BD que backend)
- Cross-module FK: `paciente_id` → `pacientes.id`
- Conceptual FK: `workflow_id` → `adapters.id`

### RF-5: Cobertura Rúbrica N2
Debe mapear **N2 — LangChain** (diapositivas 07-09) a artefactos concretos:

| PPTX | Criterio | Artefacto |
|------|----------|-----------|
| 07 | LLM | `services/langchain_agent.py` — `model="openai:gpt-4o-mini"` |
| 07 | ChatPromptTemplate | System prompt + medico_id rule |
| 07 | Tools | 4 `@tool` decorators |
| 07 | Chain/Agent | `create_agent()` + `InMemorySaver()` + `thread_id` |
| 08 | Código | `notebooks/02-entrenamiento.ipynb` |
| 08 | CoT | `docs/ejemplo-cot.log` |
| 08 | RAG | `services/rag_service.py` — Chroma + `SentenceTransformer` |
| 09 | Video | YouTube 4-10 min |

### RF-6: Cobertura Rúbrica N3
Debe mapear **N3 — Metaheurísticas** (diapositivas 10-11) a artefactos concretos:

| PPTX | Criterio | Artefacto |
|------|----------|-----------|
| 10 | Selección | ADR-010 — AG + PSO combinados |
| 10 | Codificación | `services/genetic_engine.py` — binary 13 bits |
| 10 | Parámetros | 50 ind × 20 gen, tournament k=3, cxUniform p=0.8 |
| 10 | Parámetros PSO | `services/pso_engine.py` — `Particle` class, 30 part, 3 dim, 30 iter |
| 11 | Métrica #1 | Accuracy: 0.82 → 0.87 → 0.91 (+9pp) |
| 11 | Métrica #2 | Features: 13 → 7 (−46%) |
| 11 | Visualización | Curves convergence, confusion matrix |

### RF-7: ADRs Referenciados
Deben listarse **8 ADRs** (008-015) con one-line summary:
- ADR-008: Framework de Agente (`create_agent()` + `InMemorySaver`)
- ADR-009: Vector Store (Chroma `PersistentClient`)
- ADR-010: Metaheurísticas (DEAP AG + PSO manual)
- ADR-011: Clasificador (RandomForest)
- ADR-012: Embeddings (`sentence-transformers`)
- ADR-013: Memoria Agent (`InMemorySaver` + `thread_id`)
- ADR-014: Migración BD (`branch_labels` + `depends_on`)
- ADR-015: Modelo Adapter (corrección UML)

### RF-8: Convenciones
Deben documentarse las mismas convenciones que backend:
- Archivos: `snake_case`
- Modelos: Singular (Lectura, Prediccion)
- Routers: Plural (predict.py, evaluaciones.py)
- Servicios: Sufijo `_service` (predictor_service.py)
- Schemas: Sufijo de operación (PredictRequest, PredictResponse)
- Tests: Prefijo `test_` (test_predictor.py)

## No Funcionales

### RNF-1: Formato
- Markdown válido
- Tablas con alineación consistente
- Diagramas ASCII donde aplique
- Mermaid para diagramas complejos

### RNF-2: Tono
- Técnico pero accesible
- En español (igual que backend AGENTS.md)
- Sin explicaciones de primer principio (asume agente técnico)
- Referencias a archivos con rutas relativas

### RNF-3: Consistencia
- Misma estructura que `backend/AGENTS.md`
- Mismas convenciones que backend
- Mismos estilos de tabla y diagrama
- Mismos niveles de heading

### RNF-4: Referencias
- `Documents/Diagrama UML.md` — source of 5 models
- `Rubric/Proyecto final_SI1_UCaldas.md` — rubric mapping
- `exploracion-definitiva.md` — ADRs and ctx7 findings
- `backend/AGENTS.md` — template structure

### RNF-5: Actualización Padre
- `Project/AGENTS.md` debe actualizarse en:
  - Índice de divulgación progresiva (línea 37)
  - Stack tecnológico (nueva subsección)
- Sin modificar otras secciones del padre

## Criterios de Aceptación

- [x] `microservice/AGENTS.md` contiene todas las secciones listadas
- [x] Los 5 modelos tienen atributos exactos del UML
- [x] Los 6 endpoints están documentados
- [x] N2 y N3 tienen mapeo a artefactos concretos
- [x] ADRs 008-015 están referenciados
- [x] Convenciones coinciden con backend
- [x] Parent `AGENTS.md` tiene índice actualizado
- [x] Parent `AGENTS.md` tiene stack resumido
- [x] Sin código de implementación
- [x] Sin cambios a BD

## Notas

- Este es un artefacto de **especificación**, no de implementación
- La implementación se hará en cambio separado (`/opsx-apply`)
- El AGENTS.md resultante debe ser legible por cualquier agente sin contexto previo
