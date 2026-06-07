# Propuesta: Refinar Diagrama UML de Dominio

## Resumen
Refinar el diagrama UML de clases del sistema de triaje cardiovascular para corregir problemas estructurales identificados en la revisión arquitectónica: Perfil como feature vector, ausencia de frontera backend/microservice, acoplamiento Prediccion-AG, y modelo de autenticación sobredimensionado.

## Problemas identificados

| # | Problema | Impacto |
|---|----------|---------|
| P1 | `Perfil` contiene columnas del Cleveland Dataset (cp, trestbps, chol...) mezcladas con `puntuacionIa`. Es un feature vector disfrazado de entidad clínica. | Rompe separación de responsabilidades. Mezcla input del ML con output. |
| P2 | `Paciente "1" --> "1" Perfil` — relación 1:1 implica que cada evaluación sobrescribe la anterior. | Se pierde histórico de evaluaciones de riesgo. |
| P3 | `Prediccion` embeda parámetros del Algoritmo Genético (generacionesAg, cromosomaOptimo, recallObtenido). | Acopla la entidad resultado a una técnica específica de SI1. Si cambias a PSO o RL, la estructura no sirve. |
| P4 | Sin demarcación backend ↔ microservice. | Riesgo de implementar lógica de ML en backend o persistencia en microservice. |
| P5 | Modelo de auth sobredimensionado: `Medico` existe pero no hay `Usuario` base, login, roles. | Complejidad innecesaria para el alcance real (solo médico con auth básica + paciente con reloj). |
| P6 | `Telemetria "1" --> "1" Workflow` — cada lectura de telemetría dispara un workflow. | Inviable para 30 pacientes en tiempo real (~86k eventos/día por paciente). |
| P7 | No existe entidad `Alerta`. `generarAlertas()` es un método en Paciente sin representación persistible. | Las alertas no se pueden auditar, re-asignar, ni escalar. |
| P8 | No existe modelo para RAG clínico (Documento/Embedding). | El microservice LangChain no tiene representación en el modelo de dominio. |
| P9 | Workflow interface tiene `payload JSON` genérico. | Oculta el contrato real entre componentes. |

## Alcance

### Incluye
1. Separar `Perfil` en dos entidades: `Perfil` (datos estables del paciente, se reutiliza el nombre) y `Evaluacion` (una snapshot por evaluación con datos fisiológicos + predicción)
2. Desacoplar `Prediccion` de parámetros de AG — mover metadatos del algoritmo a metadata genérica
3. Simplificar modelo de usuarios: `Usuario` (base), `Paciente` (con WearOS) y `Medico` (con auth básica + Telegram)
4. Agregar entidad `Alerta` como ciudadano de primera clase
5. Agregar entidad `Documento` para el RAG del microservice
6. Corregir relación Telemetria → Workflow agregando `Evento` como agregador intermedio
7. Añadir notas de demarcación (estereotipos) indicando qué pertenece al backend y qué al microservice
8. Refinar Workflow interface con tipos concretos

### Excluye
- Sistema completo de autenticación con roles múltiples (se deja auth básica para médico)
- Implementación de código — solo diagrama UML y specs
- Cambios en la arquitectura de despliegue o infraestructura
- Modelo de datos para hospitales, departamentos o centros médicos

## Criterios de éxito
- El diagrama UML refactorizado se puede leer y entender sin necesidad del análisis previo
- Cada entidad tiene una responsabilidad única y clara
- Las fronteras backend ↔ microservice son visibles en el diagrama
- El diagrama es implementable directamente por un agente autónomo
