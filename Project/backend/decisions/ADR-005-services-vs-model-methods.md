# ADR-005: Lógica de Negocio en Services (no en Modelos)

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El diagrama UML define métodos en las clases:
- `Triaje.notificarTelegram()`
- `Alerta.marcarLeida()`
- `Evento.evaluarUmbrales()`
- `Dispositivo.revocarToken()`
- `Paciente.generarAlertas()`

¿Dónde implementar estos métodos en el código?

## Opciones Consideradas

### Opción 1: Métodos en los modelos SQLModel
- `Triaje` tendría un método `notificar_telegram()`
- El modelo contendría lógica de negocio
- Parece fiel al UML

### Opción 2: Capa de Servicios separada
- `services/triaje_service.py` contiene `notificar_telegram()`
- Los modelos SQLModel son puramente datos + relaciones
- La lógica de negocio vive en servicios

## Decisión

**Capa de Servicios separada** (Arquitectura Hexagonal / Clean Architecture)

## Fundamentos

1. **Separación de responsabilidades**: El modelo debe representar datos y relaciones. La lógica de negocio cambia por razones distintas a los datos.
2. **Testeabilidad**: Los servicios se prueban con mocks de BD. Los modelos no necesitan tests de lógica.
3. **Dependencias externas**: `notificarTelegram()` llama al Workflow (que llama a n8n o LangChain). Eso no debería estar en un modelo de BD.
4. **Escalabilidad**: Si la lógica crece (ej: algoritmo de escalado de urgencia), el modelo no debería crecer con ella.
5. **UML ≠ Implementación**: El diagrama UML muestra responsabilidades conceptuales, no estructura de código. Los métodos en UML indican "esta clase tiene la responsabilidad de notificar", no "esta clase debe tener un método notificar()".

## Consecuencias

- Positivas: Modelos limpios, servicios testeables, lógica centralizada
- Positivas: Fácil de explicar en Q&A (Arquitectura Hexagonal)
- Negativas: Más archivos (un service por cada clase UML con métodos)
- Neutras: Los métodos del UML se convierten en funciones de servicio

## Mapeo UML → Services

| Método UML | Service | Módulo |
|-----------|---------|--------|
| Triaje.notificarTelegram() | `triaje_service.notificar_telegram()` | backend |
| Triaje.escalarUrgencia() | `triaje_service.escalar_urgencia()` | backend |
| Alerta.marcarLeida() | `alerta_service.marcar_leida()` | backend |
| Alerta.asignarMedico() | `alerta_service.asignar_medico()` | backend |
| Evento.evaluarUmbrales() | `evento_service.evaluar_umbrales()` | backend |
| Dispositivo.revocarToken() | `dispositivo_service.revocar_token()` | backend |
| Dispositivo.enviarTelemetria() | `telemetria_service.recibir_telemetria()` | backend |
| Telemetria.validar() | `telemetria_service.validar()` | backend |
| Telemetria.enriquecerConLab() | `telemetria_service.enriquecer_con_lab()` | backend |
| Log.registrar() | `triaje_service.registrar_log()` | backend |
| Paciente.registrarIngreso() | `paciente_service.registrar_ingreso()` | backend |
| Paciente.generarAlertas() | `paciente_service.generar_alertas()` | backend |

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Services muy grandes | Media | Dividir por entidad (un archivo por dominio) |
| Acoplamiento entre services | Media | Inyectar dependencias, no importar services directamente |

## Referencias

- [Arquitectura Hexagonal (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
