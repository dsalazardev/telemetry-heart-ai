# ADR-001: FastAPI vs Django

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El backend del sistema de triaje cardiovascular necesita un framework web Python que:
- Exponga una API REST para frontend, microservicio, n8n y WearOS
- Maneje telemetría entrante de forma asíncrona (múltiples dispositivos simultáneos)
- Comparta tipos/schemas con el microservicio (también Python)
- Sea defendible en una presentación académica de 10 minutos

## Opciones Consideradas

### Opción 1: Django + Django REST Framework
- Framework maduro con "baterías incluidas" (admin, auth, ORM)
- Síncrono por defecto (Channels para async, pero complejidad extra)
- Separación de modelos (Django ORM) y serializadores (DRF)
- Comunidad enorme, pero overhead para el alcance del proyecto

### Opción 2: FastAPI
- Async nativo (uvicorn, ASGI) — ideal para telemetría concurrente
- Pydantic nativo — mismos tipos que el microservicio
- OpenAPI automática — n8n puede importar la spec
- Rendimiento cercano a Node/Go en benchmarks
- Menos código boilerplate que Django para API puras

### Opción 3: Flask
- Microframework, demasiado minimalista
- Sin async nativo (extensiones)
- Demasiado trabajo manual para un proyecto académico

## Decisión

**FastAPI v0.136.3**

## Fundamentos

1. **Async nativo**: WearOS envía telemetría concurrente. Con FastAPI, cada request no bloquea al resto.
2. **Pydantic compartido**: Los schemas del backend y del microservicio usan el mismo `BaseModel`. Se pueden definir tipos comunes.
3. **OpenAPI automática**: Endpoints documentados. n8n puede importar la spec para configurar webhooks.
4. **Velocidad de desarrollo**: Para un proyecto que se presenta en 10 minutos, cada hora cuenta.
5. **Q&A defendible**: "FastAPI es el framework moderno para APIs en Python. Django es para aplicaciones web completas con template engine — nosotros solo necesitamos una API REST."

## Consecuencias

- Positivas: Código más limpio, async real, documentación automática
- Negativas: No tiene admin panel ni ORM integrado (usamos SQLModel)
- Neutras: Hay que estructurar manualmente con routers + services

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| El equipo no conoce FastAPI | Media | FastAPI es intuitivo si ya saben Python. La doc oficial es excelente |
| Falta de "baterías incluidas" | Baja | Solo necesitamos API REST. No necesitamos admin, templates, ni forms |

## Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- ctx7: `/fastapi/fastapi` — v0.136.3
- FastAPI "Bigger Applications": https://fastapi.tiangolo.com/tutorial/bigger-applications/
