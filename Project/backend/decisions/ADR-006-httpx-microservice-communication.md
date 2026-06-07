# ADR-006: Comunicación Backend ↔ Microservice vía HTTP Async

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El backend y el microservicio son procesos independientes. El backend necesita solicitar predicciones al microservicio cuando se completa un Evento de telemetría.

Requisitos:
- Comunicación síncrona (el backend espera la predicción antes de continuar)
- Tipado fuerte en ambos lados
- Mínima latencia (el bottleneck es el LLM, no la red)
- Desacoplamiento (cada módulo puede evolucionar independientemente)

## Opciones Consideradas

### Opción 1: HTTP Async con httpx
- `httpx.AsyncClient` en el backend para llamar endpoints del microservicio
- JSON como formato de intercambio
- OpenAPI en ambos lados para documentación
- Timeout configurable para llamadas largas (LLM puede tardar)

### Opción 2: Mensajería (RabbitMQ / Redis Queue)
- Cola de mensajes entre módulos
- Desacoplamiento total
- Complejidad innecesaria para 30 pacientes
- Otro servicio que mantener en la demo

### Opción 3: gRPC
- Alto rendimiento, contratos definidos (.proto)
- Overkill para el alcance académico
- Curva de aprendizaje alta

### Opción 4: Llamada directa a función (mismo proceso)
- Viola la separación de módulos
- Acopla backend y microservice
- No es una opción real

## Decisión

**HTTP Async con httpx.AsyncClient**

## Fundamentos

1. **Simplicidad**: El microservicio expone endpoints REST. El backend los consume con httpx. No hay infraestructura adicional.
2. **Async**: httpx.AsyncClient no bloquea el event loop de FastAPI mientras espera la respuesta del LLM.
3. **Contrato explícito**: La API del microservicio se documenta con OpenAPI. El backend sabe exactamente qué enviar y qué esperar.
4. **Alineación con n8n**: n8n también se comunica vía HTTP con el backend. Mismo patrón.
5. **Debuggeable**: Se puede probar con curl, Postman, o directamente desde el navegador.

## Consecuencias

- Positivas: Sin infraestructura extra, fácil de debuggear, documentación automática
- Negativas: Llamada HTTP tiene latencia de red (~1ms en localhost — insignificante vs LLM)
- Negativas: Timeout y reintentos deben manejarse explícitamente

## Flujo de Comunicación

```
Backend                              Microservice
   │                                      │
   │  POST /microservice/predict          │
   │  {                                    │
   │    "age": 63,                         │
   │    "sex": 1,                          │
   │    "cp": 3,                           │
   │    "trestbps": 145,                   │
   │    ...                                │
   │    "thal": 2                          │
   │  }                                    │
   │                                      │
   │                    ┌─────────────────┤
   │                    │ exportarVector()│
   │                    │ → [63,1,3,...]  │
   │                    │ modelo.predict()│
   │                    │ → 0.85          │
   │                    │ interpretar()   │
   │                    │ → "explicación" │
   │                    └─────────────────┤
   │                                      │
   │  200 OK                              │
   │  {                                    │
   │    "probabilidad": 0.85,             │
   │    "clasificacion": "alto",          │
   │    "explicacionClinica": "...",      │
   │    "tiempoMs": 2340                  │
   │  }                                   │
   │                                      │
```

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Timeout por LLM lento | Media | Timeout de 30s en httpx. Si falla, reintentar o escalar a médico humano |
| Microservicio caído | Baja | Circuit breaker: si el microservice no responde, el backend opera en modo degradado |
| ContratoOpenAPI desincronizado | Media | Tests de integración que verifican que backend y microservice hablan el mismo formato |

## Referencias

- [httpx Documentation](https://www.python-httpx.org/)
- ctx7: `/encode/httpx` — v0.27.2
- [FastAPI + httpx Async Client](https://fastapi.tiangolo.com/advanced/async-tests/)
