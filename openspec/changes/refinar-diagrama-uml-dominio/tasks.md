# Tasks — Refinar Diagrama UML de Dominio

## Tarea 1: Separar Perfil en Perfil (datos estables) + Evaluacion (snapshot)

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Mantener clase `Perfil` pero cambiar su contenido: ahora solo contiene _id, edad, sexo, tipoSangre, alergias, paciente (quitar los campos del Cleveland)
- [ ] Crear clase `Evaluacion` con: _id, fechaEvaluacion, origenDatos, datosFisiologicos (JSON), prediccion
- [ ] Agregar método `+exportarVector() List~Float~` en Evaluacion
- [ ] Mantener relación: `Paciente "1" --> "1" Perfil : perfil`
- [ ] Agregar relación: `Paciente "1" --> "*" Evaluacion : evaluaciones`
- [ ] Agregar relación: `Evaluacion "1" --> "1" Prediccion : prediccion`
- [ ] Quitar de Perfil: cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, puntuacionIa
- [ ] Quitar de Perfil: timestampEvaluacion, predicciones (esos van a Evaluacion)

**Verificación**: Perfil tiene solo datos estables del paciente. Evaluacion tiene una snapshot por evaluación con sus datos fisiológicos y predicción.

---

## Tarea 2: Desacoplar Prediccion de parametros de AG

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] En clase `Prediccion`, reemplazar estos atributos:
  - `generacionesAg: Int` → eliminar
  - `recallObtenido: Float` → eliminar
  - `cromosomaOptimo: String` → eliminar
  - Agregar: `metadataTecnica: JSON` (reemplaza los 3 anteriores)
- [ ] Cambiar tipo de `clasificacion: String` con valores semanticos ("bajo", "medio", "alto")

**Verificación**: Prediccion no menciona AG, PSO ni ninguna tecnica especifica. Todo va a `metadataTecnica`.

---

## Tarea 3: Simplificar modelo de usuarios

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Crear clase `Usuario` con: _id, documento, nombres, apellidos, telefono, activo
- [ ] Modificar `Paciente` para que herede de `Usuario`, conservando: fechaNacimiento, dispositivos, perfil, evaluaciones, triajes, historiales
- [ ] Cambiar `Paciente` — metodo `generarAlertas() List` por `generarAlerta() Alerta`
- [ ] Modificar `Medico` para que herede de `Usuario`, con: especialidad, licencia, telegramChatId, passwordHash, triajes
- [ ] Quitar de Medico: documento, nombres, apellidos (heredados de Usuario)
- [ ] Agregar relacion: `Usuario <|-- Paciente`
- [ ] Agregar relacion: `Usuario <|-- Medico`

**Verificación**: Paciente y Medico heredan de Usuario. Cada uno tiene solo sus atributos especificos.

---

## Tarea 4: Crear entidad Alerta

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Crear clase `Alerta` con: _id, tipo, mensaje, leida, atendida, fechaEmision, fechaAtencion, paciente, medico, triaje
- [ ] Agregar metodos: `+marcarLeida() void`, `+asignarMedico(m Medico) void`
- [ ] Agregar relacion: `Paciente "1" --> "*" Alerta : alertas`
- [ ] Agregar relacion: `Medico "1" --> "*" Alerta : alertas` (alertas atendidas)
- [ ] Agregar relacion: `Alerta "0..1" --> "1" Triaje : triaje` (opcional)
- [ ] Eliminar metodo `generarAlertas()` de Paciente

**Verificación**: Alerta tiene ciclo de vida completo (emision → lectura → atencion → triaje opcional).

---

## Tarea 5: Agregar Documento para RAG

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Crear clase `Documento` con: _id, titulo, contenido, embedding, fuente, fechaIndexacion, activo
- [ ] Agregar metodo: `+buscarSimilares(query String) List~Documento~`
- [ ] Marcar clase con estereotipo `<<microservice>>`

**Verificación**: La clase existe en el diagrama y pertenece al microservice (LangChain RAG).

---

## Tarea 6: Corregir Telemetria → Workflow con Evento

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Crear clase `Evento` con: _id, tipo, ventanaInicio, ventanaFin, lecturas, valorAgregado, workflow
- [ ] Agregar metodo: `+evaluarUmbrales() Boolean`
- [ ] Cambiar relacion: `Telemetria "1" --> "*" Evento : genera`
- [ ] Agregar relacion: `Evento "1" --> "1" Workflow : procesa`
- [ ] Eliminar relacion directa `Telemetria "1" --> "1" Workflow`

**Verificacion**: La telemetria se agrega en eventos antes de disparar workflows.

---

## Tarea 7: Anadir estereotipos de frontera backend/microservice

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Agregar `<<backend>>` en clases: Usuario, Paciente, Medico, Perfil, Dispositivo, Telemetria, Evento, Triaje, Alerta, Log, Patologia, Historial
- [ ] Agregar `<<microservice>>` en: Evaluacion, Prediccion, Documento
- [ ] Agregar `<<interface>>` en Workflow + nota "Compartido entre backend y microservice"
- [ ] Incluir leyenda al inicio del diagrama explicando los estereotipos

**Verificacion**: Al leer el diagrama se distingue inmediatamente que pertenece a cada modulo.

---

## Tarea 8: Limpieza general y consistencia

**Archivo**: `Documents/Diagrama UML.md`

**Cambios**:
- [ ] Verificar multiplicidades de todas las relaciones
- [ ] Verificar que todos los tipos de retorno de metodos sean especificos (no `List` generico sin parametro)
- [ ] Asegurar que la herencia use `--|>` en Mermaid
- [ ] Verificar que no haya clases sin relacion con el resto del diagrama
- [ ] Agregar titulo descriptivo y fecha de version
- [ ] Agregar nota: "UML de dominio — no incluye decisiones de infraestructura"

**Verificacion**: El diagrama es autonomo, completo y consistente.
