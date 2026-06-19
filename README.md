# Telemetry Heart AI

> Sistema de **triaje cardiovascular asistido por IA** con telemetría IoT, orquestación de flujos con n8n, un agente LangChain/LangGraph con RAG y optimización metaheurística (PSO).

**Proyecto Integrador — Sistemas Inteligentes 1**
Ingeniería de Sistemas y Computación · Facultad de Ingenierías y Arquitectura · Universidad de Caldas

| | |
|---|---|
| **Repositorio** | https://github.com/dsalazardev/telemetry-heart-ai |
| **Integrantes** | _(diligenciar: nombres completos)_ |
| **Docente** | _(diligenciar: nombre del docente)_ |
| **Período académico** | 2026-1 |

---

## 1. Tabla de contenidos

1. [Planteamiento del problema](#2-planteamiento-del-problema)
2. [Visión general de la solución](#3-visión-general-de-la-solución)
3. [Arquitectura del sistema](#4-arquitectura-del-sistema)
4. [Flujo de datos end-to-end](#5-flujo-de-datos-end-to-end)
5. [Módulos del ecosistema](#6-módulos-del-ecosistema)
6. [Cobertura de la rúbrica (Niveles 1, 2 y 3)](#7-cobertura-de-la-rúbrica)
7. [Comparativa n8n vs LangChain](#8-comparativa-n8n-vs-langchain)
8. [Resultados de la metaheurística (N3)](#9-resultados-de-la-metaheurística-n3)
9. [Puesta en marcha](#10-puesta-en-marcha)
10. [Estructura del repositorio](#11-estructura-del-repositorio)
11. [Entregables y recursos](#12-entregables-y-recursos)
12. [Declaración de uso de IA](#13-declaración-de-uso-de-ia)

---

## 2. Planteamiento del problema

Las enfermedades cardiovasculares son la principal causa de mortalidad mundial y el triaje tradicional en urgencias enfrenta tres barreras críticas:

1. **Saturación cognitiva y latencia.** El personal médico debe correlacionar manualmente hasta **13 variables fisiológicas** (presión arterial, colesterol, anomalías ECG, etc.) bajo presión de tiempo.
2. **Falsos negativos por desbalance de clases.** Los historiales tienen muchos pacientes sanos y pocos enfermos; los modelos clásicos se sesgan hacia la clase mayoritaria y disparan la tasa de **falsos negativos** — el escenario más letal (enviar a casa a un paciente infartado).
3. **Falta de telemetría.** Los signos vitales dependen del ingreso manual, lo que estanca el flujo de pacientes.

> Contexto clínico completo en [`Project/docs/CONTEXTO_CLINICO.md`](Project/docs/CONTEXTO_CLINICO.md).

---

## 3. Visión general de la solución

**Telemetry Heart AI** es un ecosistema de microservicios que automatiza el triaje cardiovascular:

- **Captura** signos vitales de forma continua mediante dispositivos vestibles (Wear OS).
- **Orquesta** la ingesta, las reglas de umbral y las notificaciones con **n8n** (Nivel 1).
- **Predice el riesgo** y **prioriza** al paciente con un agente **LangChain/LangGraph** que combina un motor de riesgo ponderado, RAG sobre guías clínicas y un LLM explicativo (Nivel 2).
- **Optimiza** los pesos y umbrales del clasificador de prioridad con **PSO** (Particle Swarm Optimization), minimizando los falsos negativos críticos (Nivel 3).
- **Visualiza** alertas, pacientes y explicaciones clínicas en un **dashboard Angular** para el personal médico.

---

## 4. Arquitectura del sistema

```mermaid
flowchart LR
    WO["⌚ Wear OS<br/>(adquisición IoT)"] -->|telemetría| N8N
    subgraph ORQ["Orquestación — Nivel 1"]
        N8N["n8n<br/>:5678<br/>workflows"]
    end
    N8N -->|"INSERT + HTTP"| BE
    subgraph CORE["Núcleo de dominio"]
        BE["Backend FastAPI<br/>:8000<br/>pacientes · triajes · alertas · auth"]
    end
    BE -->|"POST /predecir<br/>(Bearer interno)"| MS
    subgraph IA["IA — Niveles 2 y 3"]
        MS["Microservicio FastAPI<br/>:8001<br/>ClinicalGraph (LangGraph)"]
        RE["RiskEngine<br/>(11 pesos, sigmoid)"]
        TP["TriagePriorityService<br/>(7 pesos + 2 umbrales · PSO | ML)"]
        RAG["RAG ChromaDB<br/>+ embeddings"]
        LLM["LLM<br/>(OpenAI / LM Studio)"]
        MS --- RE
        MS --- TP
        MS --- RAG
        MS --- LLM
    end
    FE["🖥️ Frontend Angular<br/>:4200<br/>dashboard médico"] -->|JWT| BE
    N8N -.->|"alertas Telegram"| TG["📱 Telegram"]
    BE <--> DB[("PostgreSQL<br/>Aiven Cloud")]
    N8N <--> DB
```

**Principios de diseño:**

- **Separación de responsabilidades:** el backend gobierna el dominio clínico y la persistencia; el microservicio aísla toda la IA en un solo agente `ClinicalGraph`; n8n orquesta sin lógica de negocio; el frontend solo presenta.
- **La IA nunca toca la BD del dominio directamente:** se comunica vía contrato HTTP (`POST /predecir`, `POST /explicar`) autenticado con token interno.
- **PostgreSQL compartida** (Aiven Cloud) entre backend y n8n; el microservicio persiste su RAG en ChromaDB (`PersistentClient`).

---

## 5. Flujo de datos end-to-end

```
Wear OS / simulación
   │ POST /webhook/telemetria
   ▼
n8n  ── INSERT telemetría en PostgreSQL ──► agrupa en "Evento"
   │ HTTP Request
   ▼
Backend (FastAPI :8000)
   │ evento_service.evaluar_umbrales()
   │ prediccion_service.procesar_prediccion()
   │ POST /predecir  (Authorization: Bearer <internal_token>)
   ▼
Microservicio (FastAPI :8001) — ClinicalGraph (LangGraph, 1 solo agente)
   normalize_and_predict → RiskEngine.predict()        (riesgo 11-pesos, sigmoid)
   prioritize            → TriagePriorityService.classify()  (prioridad: PSO 7-pesos o ML RandomForest)
   retrieve_rag          → ChromaDB (26 guías clínicas indexadas)
   explain               → LLM (gpt-4o-mini) + ChatPromptTemplate → ClinicalExplanation
   format_response       → PredictionResponse
   ▼
Backend adapta la respuesta:
   risk_level  → Triaje.nivelUrgencia
   risk_score  → Triaje.probabilidadRiesgo
   priority*   → Evento.valorAgregado
   threshold_exceeded == true → genera Alerta
   ▼
Frontend (Angular :4200)  ── GET /alertas, /pacientes ──►  dashboard médico
n8n (Schedule)            ── notifica triajes pendientes ──►  Telegram
```

---

## 6. Módulos del ecosistema

| Módulo | Carpeta | Stack | Puerto | Responsabilidad |
|--------|---------|-------|--------|-----------------|
| **Backend** | [`Project/backend`](Project/backend) | FastAPI 0.136, SQLModel, Alembic, JWT, asyncpg | `8000` | API central, dominio clínico, persistencia, auth por roles, cliente del microservicio |
| **Microservicio IA** | [`Project/microservice`](Project/microservice) | FastAPI, LangGraph (1 agente: ClinicalGraph), ChromaDB, PSO, scikit-learn | `8001` | Predicción de riesgo + priorización + RAG (26 guías) + explicación clínica + `/explicar` (N2 y N3) |
| **n8n** | [`Project/n8n`](Project/n8n) | n8n (Docker), PostgreSQL, OpenAI, Telegram | `5678` | Orquestación visual: ingesta de telemetría, reglas, asistente LLM, notificaciones (N1) |
| **Frontend** | [`Project/frontend`](Project/frontend) | Angular (standalone components), RxJS | `4200` | Dashboard médico, gestión de pacientes, alertas, evaluación IA |
| **Wear OS** | [`Project/wearos`](Project/wearos) | Kotlin 2.2, Jetpack Compose for Wear | — | Adquisición de telemetría IoT · **estado: skeleton/placeholder** |

> Cada módulo tiene su propio `README.md` y `AGENTS.md` con la documentación detallada de su arquitectura interna.

---

## 7. Cobertura de la rúbrica

El proyecto articula los tres niveles acumulativos sobre un mismo caso de uso (triaje cardiovascular).

### Nivel 1 — n8n (≤ 3.5)

| Requisito | Implementación |
|-----------|----------------|
| Trigger → procesamiento → salida | 3 workflows en [`Project/n8n/workflows`](Project/n8n/workflows) |
| Workflow **Webhook Telemetría** (5 nodos) | Webhook POST → INSERT PostgreSQL → HTTP al microservicio → logging |
| Workflow **Asistente LLM** (15 nodos) | Telegram → LLM genera SQL (filtro `medico_id`) → ejecuta → responde médico |
| Workflow **Schedule Pendientes** (7 nodos) | Cron `*/5 * * * *` → triajes sin atender → alerta Telegram |
| Manejo de errores | Ramas de reintento y logging a tabla `logs` (`tipoEvento` prefijo `n8n_`) |
| JSON exportado | `*.json` versionados en `Project/n8n/workflows/` |

### Nivel 2 — LangChain / LangGraph (≤ 4.5)

| Componente | Artefacto |
|------------|-----------|
| **LLM** (temperatura, parámetros) | `microservice/app/providers/llm_openai.py` (gpt-4o-mini, `temperature=0.0`) |
| **ChatPromptTemplate** | `CLINICAL_PROMPT`, `MEDICO_EXPLAIN_PROMPT` en `agents/clinical_subgraph.py` |
| **Tools** | `@tool optimize_triage_priority_tool` (`tools/pso_tools.py`) — ejecuta PSO offline |
| **Chain / Agent** | `ClinicalGraph` — `StateGraph` LangGraph (1 solo agente): `predict → prioritize → RAG → explain → format` |
| **RAG / persistencia** | ChromaDB (`PersistentClient`) + embeddings HuggingFace `all-MiniLM-L6-v2`, 26 guías clínicas |
| **Cadena de pensamiento** | Razonamiento estructurado validado contra el schema `ClinicalExplanation` con fallback seguro |

### Nivel 3 — Metaheurística: PSO (≤ 0.5)

| Requisito | Artefacto |
|-----------|-----------|
| **Codificación de la solución** | Partícula = 7 pesos + 2 umbrales del `TriagePriorityService` |
| **Función objetivo** | Fitness multiobjetivo que penaliza falsos negativos (`services/optimizers/pso.py`, `metrics_service.py`) |
| **Parámetros** | `n_particles`, `max_iter` configurables en el `@tool` (corre **offline**; el endpoint `POST /optimize` solo persiste resultados ya calculados) |
| **Análisis de convergencia** | `convergence_curve.json` + `GET /metrics/convergence` + `app/data/charts/convergence.png` |
| **Métricas (≥ 2)** | accuracy, F1, macro/critical recall, overtriage, fitness — `GET /metrics/evaluation` |
| **Mejora vs baseline** | Comparación baseline vs. optimizado (`MetricsService.compare`) |
| **Notebooks** | `03-metaheuristics.ipynb`, `05-metrics-n3.ipynb` |
| **Estrategia alternativa** | `PRIORITY_STRATEGY=ml` activa `MLPriorityService` (RandomForest, `model.pkl`, accuracy 0.99) como fallback/clasificador complementario |

---

## 8. Comparativa n8n vs LangChain

> Requerida por la rúbrica (Nivel 2, sección 6.3). Mismo caso de uso resuelto con ambos paradigmas.

| Dimensión | n8n (Nivel 1) | LangChain/LangGraph (Nivel 2) |
|-----------|---------------|-------------------------------|
| **Paradigma** | Automatización visual por nodos | Código Python programático |
| **Rol en el sistema** | Orquestación: ingesta, reglas de umbral, notificaciones | Razonamiento clínico: predicción, priorización, explicación |
| **Lógica de IA** | Llamadas puntuales a LLM (generar SQL desde lenguaje natural) | Agente con estado, RAG, tools y validación estructurada de salida |
| **Control de flujo** | Editor visual, condicionales por nodo | `StateGraph` con edges condicionales (`_should_explain`) |
| **Trazabilidad** | Ejecuciones en la UI de n8n | LangSmith (tracing nativo por nodo) |
| **Extensibilidad** | Rápida para integraciones (Telegram, HTTP, SQL) | Alta para lógica compleja, testeable con pytest |
| **Curva de aprendizaje** | Baja (no-code/low-code) | Media-alta (requiere Python + framework) |
| **Versionado** | JSON exportado | Código en Git, modular, con tests |
| **Ideal para** | Pegamento entre servicios y disparadores | Razonamiento, RAG y decisiones explicables |

**Conclusión:** los dos enfoques son **complementarios**, no excluyentes. n8n aporta la orquestación y las notificaciones con mínimo código; LangChain/LangGraph aporta el razonamiento clínico explicable y testeable. En este proyecto, n8n **invoca** al agente LangChain a través del backend, integrando ambos en un único pipeline.

---

## 9. Resultados de la metaheurística (N3)

Optimización del clasificador de prioridad de triaje con **PSO** (versión `pso-2026-06-demo`):

| Métrica | Valor optimizado |
|---------|------------------|
| Accuracy | **0.99** |
| F1-score | **0.9879** |
| Macro recall | **0.989** |
| **Critical recall** (casos ALTA detectados) | **1.00** |
| Overtriage rate | 0.0081 |
| Ordinal error | 0.005 |
| Fitness (a minimizar) | 0.009054 |

**Pesos óptimos encontrados** (7 features): `heart_rate=0.74`, `spo2=1.0`, `systolic_bp=0.74`, `cholesterol=0.31`, `chest_pain=0.01`, `age=1.0`, `other_risk_factors=0.0`. Umbrales: `[0.291, 0.419]`.

> El `critical_recall = 1.0` es el resultado clave: el optimizador prioriza **no dejar pasar ningún caso de alto riesgo** (cero falsos negativos críticos), que es exactamente la barrera #2 del planteamiento del problema.

Visualizaciones: [`convergence.png`](Project/microservice/app/data/charts/convergence.png), [`pso_weights.png`](Project/microservice/app/data/charts/pso_weights.png). Configuración actual: `PRIORITY_STRATEGY=ml` (RandomForest, `model.pkl`); alternar a PSO cambiando la variable de entorno.

---

## 10. Puesta en marcha

> Requisitos: Python 3.12+, Node.js 20+, Docker, y una instancia PostgreSQL (o las credenciales de Aiven Cloud).

### Backend (:8000)
```bash
cd Project/backend
pip install -r requirements.txt
cp .env.example .env          # configurar DATABASE_URL, JWT, INTERNAL_TOKEN, MICROSERVICE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Microservicio IA (:8001)
```bash
cd Project/microservice
pip install -r requirements.txt
cp .env.example .env          # configurar llm_provider, embedding_provider, internal_token
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend (:4200)
```bash
cd Project/frontend
npm install
npm start                     # http://localhost:4200
```

### n8n (:5678)
```bash
cd Project/n8n
cp .env.example .env
openssl rand -hex 32          # → N8N_ENCRYPTION_KEY
docker compose up -d          # http://localhost:5678
# Importar los workflows de ./workflows/ y configurar credenciales
```

> **Importante para la demo:** los triggers de Telegram y Webhook requieren una URL HTTPS pública. Para desarrollo local usar `ngrok http 5678` y fijar `WEBHOOK_URL` en el `.env` de n8n.

### Verificación rápida
```bash
# Backend
curl http://localhost:8000/health

# Microservicio — health + readiness
curl http://localhost:8001/health | python -m json.tool
curl http://localhost:8001/ready

# Microservicio — predecir (token interno del .env)
curl -s -X POST http://localhost:8001/predecir \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"paciente_id":1,"heart_rate":72,"spo2":98,"systolic_bp":118,"diastolic_bp":76,"cholesterol":180,"glucose":90,"age":35,"sex":"F","smoker":false,"previous_condition":false,"explain":true}' | python -m json.tool

# Microservicio — pregunta al médico
curl -s -X POST http://localhost:8001/explicar \
  -H "Authorization: Bearer dev-token-cambiar-en-prod" \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Por qué este paciente tiene riesgo alto?","prediction_context":{"risk_score":0.82,"risk_level":"alto","dominant_factors":["taquicardia","hipoxemia","hipertensión sistólica"]}}' | python -m json.tool

# Métricas PSO
curl http://localhost:8001/metrics/evaluation | python -m json.tool
curl http://localhost:8001/metrics/convergence | python -m json.tool
```

---

## 11. Estructura del repositorio

```
telemetry-heart-ai/
├── README.md                  # (este archivo)
├── Project/
│   ├── AGENTS.md              # Directiva de contexto global del proyecto
│   ├── backend/               # API central FastAPI (dominio clínico, persistencia, auth)
│   ├── microservice/          # IA: ClinicalGraph (LangGraph) + RAG ChromaDB + PSO offline + ML Priority
│   ├── n8n/                   # Workflows de orquestación (+ JSON exportados)
│   ├── frontend/              # Dashboard Angular (standalone components)
│   ├── wearos/                # App Wear OS (skeleton: Kotlin + Jetpack Compose for Wear)
│   └── docs/                  # CONTEXTO_CLINICO.md
├── openspec/                  # Propuestas de cambio y especificaciones (OpenSpec workflow)
├── Documents/                 # Diagrama UML, dataset y material de apoyo
└── Rubric/                    # Plantilla PPTX oficial y rúbrica de evaluación
```

Documentación por módulo: cada subcarpeta de `Project/` contiene `README.md` (resumen) y `AGENTS.md` (arquitectura detallada, contratos y mapeo a la rúbrica).

---

## 12. Entregables y recursos

| Entregable | Estado | Ubicación / enlace |
|------------|--------|--------------------|
| JSON de los flujos n8n | ✅ | [`Project/n8n/workflows/`](Project/n8n/workflows) |
| Código LangChain/LangGraph | ✅ | [`Project/microservice/app/agents/clinical_subgraph.py`](Project/microservice/app/agents/clinical_subgraph.py) |
| Notebooks de métricas (N3) | ✅ | [`Project/microservice/notebooks/`](Project/microservice/notebooks) |
| Pesos PSO + convergencia | ✅ | `triage_priority_weights.json` (v. `pso-2026-06-demo`), `convergence_curve.json` |
| Plantilla PPTX diligenciada | ⏳ | _(diligenciar / adjuntar enlace)_ |
| Video Nivel 1 — n8n (3–8 min) | ⏳ | _(adjuntar enlace YouTube/Drive)_ |
| Video Nivel 2 — LangChain (4–10 min) | ⏳ | _(adjuntar enlace YouTube/Drive)_ |
| Video Nivel 3 — Metaheurística (4–8 min) | ⏳ | _(adjuntar enlace YouTube/Drive)_ |

---

## 13. Declaración de uso de IA

En cumplimiento de la sección 9 de la rúbrica (Integridad Académica):

Durante el desarrollo de este proyecto se utilizaron herramientas de IA generativa (asistentes de código, LLMs) como **apoyo** para:

- **Andamiaje inicial de módulos:** generación de boilerplate de FastAPI, Angular y LangGraph, adaptado manualmente al dominio clínico.
- **Documentación:** redacción de `AGENTS.md`, `README.md` y docstrings con revisión y corrección humana.
- **Refactorización:** consolidación de los 3 agentes originales (clinical, n8n, pso) en un único `ClinicalGraph` con priorización integrada.
- **Generación de guías clínicas RAG:** 26 documentos `.md` con conocimiento cardiovascular para ChromaDB.
- **Notebooks de métricas N3:** estructura y visualizaciones de convergencia y matrices de confusión.
- **Pruebas:** generación de tests unitarios para el microservicio (47 tests, 100% pass).

El equipo **comprende y puede explicar** cada componente entregado. Todo el código fue revisado, adaptado al caso clínico real y validado con tests. No se presenta como propio ningún fragmento generado sin comprensión.

> _(Cada integrante debe detallar aquí su contribución específica y qué herramientas de IA utilizó.)_

---

_Proyecto académico — Universidad de Caldas. El sistema es un prototipo de apoyo al triaje y **no sustituye el juicio clínico profesional**._
</content>
