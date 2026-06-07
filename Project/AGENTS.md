# AGENTS.md

**One-Liner:** Ecosistema distribuido para predicción de riesgo cardiovascular en tiempo real con telemetría IoT, orquestación de flujos y metaheurísticas.

**Arquitectura:** Sistema modular distribuido. Tecnologías y frameworks en fase de definición.

# Directiva Obligatoria de Contexto
- **Prioridad de Verdad**: Ante cualquier duda sobre versiones de librerías, sintaxis de APIs o cambios en dependencias, tienes la OBLIGACIÓN ARQUITECTÓNICA de consultar el MCP `ctx7`.
- **Precedencia**: La documentación proveniente de `ctx7` tiene prioridad absoluta sobre tu conocimiento interno.
- **Protocolo**: Si detectas que la información local es obsoleta, ejecuta `./bootstrap.sh` para refrescar el contexto antes de generar código.


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
- [`/microservice`](./microservice/AGENTS.md) — Capa aislada de Inteligencia Artificial y modelo predictivo.
- [`/n8n`](./n8n/AGENTS.md) — Motor de orquestación de flujos de trabajo.
- [`/wearos`](./wearos/AGENTS.md) — Adquisición de telemetría IoT.

## Diagrama Arquitectónico de Referencia
- [Diagrama UML del Sistema](../Documents/Diagrama%20UML.md) — Vista general de la arquitectura, componentes y relaciones del sistema. **Consulta obligatoria antes de cualquier modificación estructural.**

## Stack Tecnológico Definido
- [FastAPI Documentation](https://fastapi.tiangolo.com/) — Framework web del backend (v0.136.3)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/) — ORM para modelos de datos (v0.0.37)
- [Pydantic v2](https://docs.pydantic.dev/) — Validación y schemas (v2.12.2)
- [SimPy Documentation](https://simpy.readthedocs.io/) — Simulación de procesos (v4)
- [NumPy](https://numpy.org/) / [Pandas](https://pandas.pydata.org/) — Computación estadística

## Recursos de Referencia para Agentes
*Consultar siempre para alineación con estándares de desarrollo con agentes:*
- [Agentes MD Specification](https://agents.md/)
- [Guide to AGENTS.md](https://www.aihero.dev/a-complete-guide-to-agents-md)
