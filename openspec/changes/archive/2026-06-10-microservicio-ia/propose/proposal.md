# Proposal.md

## What we are building

A comprehensive `AGENTS.md` for the microservice module (`Project/microservice/AGENTS.md`) and a minor update to the parent `Project/AGENTS.md` index.

## Why we are building it

The current `Project/microservice/AGENTS.md` is a 3-line stub:
```markdown
# AGENTS.md — Microservicio de Metaheurísticas

Esta es una capa aislada y dedicada a Inteligencia Artificial. Debe contener la lógica matemática del modelo predictivo, la ejecución de los algoritmos de racionalidad (metaheurísticas/algoritmos genéticos) y el procesamiento del agente conversacional (RAG) para dar explicabilidad clínica.
```

This is insufficient for any agent to understand:
- What stack to use (FastAPI, LangChain, DEAP, Chroma, etc.)
- What models exist (5 SQLModel tables)
- What endpoints to implement (POST /predict, /evaluar, /agent/query)
- How to communicate with backend/n8n
- What conventions to follow (snake_case, suffix _service, plural routers)
- What rubric items to cover (N2: LangChain, N3: Metaheuristics)
- What ADRs apply (008-015)
- What cross-module relationships exist (paciente_id → pacientes.id, workflow_id → adapters.id)

## Scope

### In Scope

- [x] **Complete rewrite** of `Project/microservice/AGENTS.md` with sections:
  - Stack Tecnológico (validated with ctx7)
  - Arquitectura (FastAPI + 5 SQLModel models)
  - Endpoints (POST /predict, /evaluar, /agent/query, GET /health)
  - Convenciones (snake_case, singular models, plural routers, _service suffix)
  - Comunicación con otros módulos (backend via httpx, n8n via HTTP)
  - Base de Datos (same PostgreSQL as backend, 5 new tables)
  - Cobertura Rúbrica (N2 + N3 mapping)
  - ADRs (008-015 references)
  - Mapeo UML → Código (5 models exact)
  - Estructura de Directorios

- [x] **Minor update** to `Project/AGENTS.md`:
  - Update microservice index line: add "FastAPI + LangChain + Metaheurísticas"
  - Add microservice stack summary to Stack Tecnológico section
  - Update any architecture references

### Out of Scope

- [x] No implementation code (no `.py` files)
- [x] No database migrations
- [x] No changes to backend/frontend/n8n/wearos
- [x] No new dependencies
- [x] No CI/CD changes

## Key Design Decisions

| # | Decision | Justification |
|---|----------|---------------|
| 1 | Match backend AGENTS.md structure | Consistency across modules |
| 2 | Include ctx7-validated stack | Requirement from Project/AGENTS.md directive |
| 3 | Document all 5 UML models | Source of truth from Diagrama UML.md |
| 4 | Map N2+N3 to concrete artifacts | Rubric requirement |
| 5 | Reference ADRs 008-015 | Decision traceability |

## Success Criteria

- [x] `microservice/AGENTS.md` is readable by any agent without prior context
- [x] Covers all 5 UML models with exact attributes
- [x] Documents N2 (LangChain: create_agent + 4 tools + RAG) and N3 (DEAP AG + PSO manual)
- [x] References ADRs 008-015
- [x] Matches parent `AGENTS.md` style and structure
- [x] Parent `AGENTS.md` index updated with microservice stack summary

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Structure mismatch with backend | Low | Low | Copy backend AGENTS.md structure exactly |
| Missing model attribute | Low | Medium | Cross-reference with Diagrama UML.md line-by-line |
| Incorrect rubric mapping | Low | High | Cross-reference with Rubric/Proyecto final_SI1_UCaldas.md |

## Timeline

| Step | Task | Estimate |
|------|------|----------|
| 1 | Read exploration + backend template | 5 min |
| 2 | Draft microservice/AGENTS.md | 15 min |
| 3 | Draft parent AGENTS.md update | 5 min |
| 4 | Review consistency | 5 min |
| | **Total** | **30 min** |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Keep 3-line stub | Agents would have zero context |
| Only update parent AGENTS.md | Microservice still undocumented |
| Add inline comments instead | AGENTS.md is the standard agent entry point |

## Status

- **Phase:** PROPOSE
- **Ready for:** IMPLEMENT
- **Blocked by:** None

## Next Steps

1. Run `/opsx-apply` to start implementation
2. Or continue reviewing this proposal

## Questions

1. ¿Should the microservice AGENTS.md include a `decisions/` directory reference for ADRs 008-015?
2. ¿Should we add a `MICROSERVICE_URL` reference to the backend communication section?

## References

- `exploracion-definitiva.md` — Source of truth
- `backend/AGENTS.md` — Template structure
- `Diagrama UML.md` — 5 models
- `Rubric/Proyecto final_SI1_UCaldas.md` — N2 + N3
