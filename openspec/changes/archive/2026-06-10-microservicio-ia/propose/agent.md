# Agent.md

## Change Metadata

- **Name:** `generate-microservice-agents-md`
- **Scope:** Documentation-only (no code implementation)
- **Status:** PROPOSE

## What

Generate a comprehensive `AGENTS.md` for the microservice module and update the parent `AGENTS.md` index.

## Files Affected

1. `Project/microservice/AGENTS.md` — **Complete rewrite** (currently 3-line stub)
2. `Project/AGENTS.md` — **Minor update** (index section only)

## Why

The current `Project/microservice/AGENTS.md` is a 3-line stub that doesn't reflect the actual architecture:
- No stack definition
- No model listing (5 SQLModel tables)
- No endpoint documentation
- No conventions
- No rubric mapping (N2 + N3)
- No cross-module relationships
- No ADR references

Any agent reading this file would have zero context about what the microservice does, how it communicates, or what decisions were made.

## Success Criteria

- [x] `microservice/AGENTS.md` is readable by any agent without prior context
- [x] Covers all 5 UML models (Lectura, Evaluacion, Prediccion, Documento, Adapter)
- [x] Documents N2 (LangChain) and N3 (Metaheuristics) rubric coverage
- [x] References ADRs 008-015
- [x] Matches parent `AGENTS.md` style and structure
- [x] Parent `AGENTS.md` index updated with microservice stack summary

## Risk Level

**None** — this is pure documentation. No code changes, no database changes, no deployment changes.

## Dependencies

- `exploracion-definitiva.md` — source of truth for all technical decisions
- `backend/AGENTS.md` — template for structure and conventions
- `Documents/Diagrama UML.md` — source of 5 models
- `Rubric/Proyecto final_SI1_UCaldas.md` — rubric mapping

## Time Estimate

30 minutes (2 files, documentation only)

## Notes

- Do NOT generate implementation code
- Do NOT modify any existing `.py` files
- Do NOT create new directories
- The implementation will be handled in a separate change (`/opsx-apply`)
