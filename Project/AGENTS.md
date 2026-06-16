# AGENTS.md

**One-Liner:** Ecosistema distribuido para predicción de riesgo cardiovascular en tiempo real con telemetría IoT, orquestación de flujos y metaheurísticas.

**Arquitectura:** Sistema modular distribuido. Tecnologías y frameworks en fase de definición.

# Directiva Obligatoria de Contexto
- **Prioridad de Verdad**: Ante cualquier duda sobre versiones de librerías, sintaxis de APIs o cambios en dependencias, tienes la OBLIGACIÓN ARQUITECTÓNICA de consultar el MCP `ctx7`.
- **Precedencia**: La documentación proveniente de `ctx7` tiene prioridad absoluta sobre tu conocimiento interno.
- **Protocolo**: Si detectas que la información local es obsoleta, ejecuta `./bootstrap.sh` para refrescar el contexto antes de generar código.

# Directiva de Base de Datos (REGLA ABSOLUTA)
- **Única base de datos permitida**: PostgreSQL en servidor remoto.
- **SQLite prohibido**: No se usará SQLite en ningún módulo del proyecto, ni para desarrollo, ni para pruebas, ni para demo.
- **La conexión a PostgreSQL está en `Project/backend/.env`** con las credenciales del servidor remoto. Cualquier agente que genere código debe leer esa URL y usarla.
- **Excepción**: Solo para tests unitarios locales se permite SQLite en memoria (no persistente). Cero archivos .db en el repositorio.

# Directiva de .env por Módulo (REGLA ABSOLUTA)
- **Cada módulo tiene su PROPIO `.env`** dentro de su carpeta. Ningún módulo lee variables de entorno de otro módulo.
- **n8n** no lee `Project/backend/.env` ni `Project/microservice/.env`. Usa solo `Project/n8n/.env`.
- **Aunque dos módulos apunten al mismo recurso** (ej: la misma base de datos PostgreSQL), cada uno lo configura independientemente en su propio `.env`.
- Los `.env` con credenciales reales NO se versionan en Git.
- Las plantillas se guardan como `.env.example` en cada módulo.


## Rúbrica y Requerimientos Académicos
*Referencia obligatoria para cumplimiento de normas universitarias:*
- [Propuesta de Evaluación (PDF)](../Rubric/Proyecto%20final_SI1_UCaldas.pdf)
- [Propuesta de Evaluación (MD)](../Rubric/Proyecto%20final_SI1_UCaldas.md)
- [Plantilla PPTX Oficial](../Rubric/Trabajo%20Final%20Sistemas%20Inteligentes%201%20v1.pptx)
- [Guía de Trabajo Final (MD)](../Rubric/Trabajo%20Final%20Sistemas%20Inteligentes%201%20v1.md)

## Índice de Divulgación Progresiva
- [Contexto Clínico y de Negocio](./docs/CONTEXTO_CLINICO.md)
- [`/frontend`](./frontend/AGENTS.md) — Capa de presentación y dashboard médico.
- [`/backend`](./backend/AGENTS.md) — API central y persistencia relacional.
- [`/microservice`](./microservice/AGENTS.md) — FastAPI + LangChain + Metaheurísticas. Predicción de riesgo cardiovascular (RandomForest), agente conversacional (RAG), y optimización (DEAP AG + PSO manual).
- [`/n8n`](./n8n/AGENTS.md) — Motor de orquestación de flujos de trabajo.
- [`/wearos`](./wearos/AGENTS.md) — Adquisición de telemetría IoT. **Estado: SKELETON.** Kotlin 2.2.10, Jetpack Compose para Wear, compileSdk 36. Sin sensores, sin HTTP, sin foreground service. 4 archivos .kt (~238 líneas, 100% placeholder). Contrato backend definido: POST /dispositivos + POST /telemetria + JWT.

## Diagrama Arquitectónico de Referencia
- [Diagrama UML del Sistema](../Documents/Diagrama%20UML.md) — Vista general de la arquitectura, componentes y relaciones del sistema. **Consulta obligatoria antes de cualquier modificación estructural.**

## Stack Tecnológico Definido

### Backend Stack
- [FastAPI Documentation](https://fastapi.tiangolo.com/) — Framework web del backend (v0.136.3)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/) — ORM para modelos de datos (v0.0.37)
- [Pydantic v2](https://docs.pydantic.dev/) — Validación y schemas (v2.12.2)
- [SimPy Documentation](https://simpy.readthedocs.io/) — Simulación de procesos (v4)
- [NumPy](https://numpy.org/) / [Pandas](https://pandas.pydata.org/) — Computación estadística
- [n8n Documentation](https://docs.n8n.io/) — Orquestación de flujos de trabajo visual (v2.23.0, Nivel 1)
- [n8n Docker Hub](https://hub.docker.com/r/n8nio/n8n) — Imagen oficial Docker para n8n
- [Telegram Bot API](https://core.telegram.org/bots/api) — Notificaciones push al médico de guardia

### Microservice Stack
- [LangChain Python](https://python.langchain.com/) — Agent framework (v0.3.0+, `create_agent()` + `InMemorySaver`)
- [ChromaDB](https://docs.trychroma.com/) — Vector store para RAG (`PersistentClient`)
- [DEAP](https://deap.readthedocs.io/) — Metaheurísticas (AG + PSO manual con `Particle` class)
- [sentence-transformers](https://www.sbert.net/) — Embeddings (`all-MiniLM-L6-v2`, 384d)
- [scikit-learn](https://scikit-learn.org/) — Clasificador (`RandomForestClassifier`)

## Recursos de Referencia para Agentes
*Consultar siempre para alineación con estándares de desarrollo con agentes:*
- [Agentes MD Specification](https://agents.md/)
- [Guide to AGENTS.md](https://www.aihero.dev/a-complete-guide-to-agents-md)
