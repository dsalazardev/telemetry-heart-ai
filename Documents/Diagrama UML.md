# Diagrama UML Original — Sistema de Triaje Cardiovascular IoT

**Fecha de conversión:** 2026-06-06
**Version:** 2.0 — Refactor de dominio
**Nota:** UML de clases del dominio. No incluye decisiones de infraestructura.

---

**Leyenda de estereotipos:**
- `<<backend>>` — Entidad persistida en el modulo Backend (API REST + SQL)
- `<<microservice>>` — Entidad procesada en el Microservicio de IA (LangChain + ML)
- `<<interface>>` — Contrato compartido entre modulos

---

```mermaid
classDiagram
  direction TB

  %% ── Estereotipos y leyenda ──
  class BackendNote {
    <<Nota>>
    Las clases <<backend>> se persisten
    y exponen via API REST
  }
  class MicroNote {
    <<Nota>>
    Las clases <<microservice>> son
    internas del pipeline de IA
  }

  %% ── Usuarios ──
  class Usuario {
    <<backend>>
    -_id: ObjectId
    -documento: String
    -nombres: String
    -apellidos: String
    -telefono: String
    -activo: Boolean
  }

  class Paciente {
    <<backend>>
    -fechaNacimiento: Date
    -dispositivos: List~Dispositivo~
    -perfil: Perfil
    -evaluaciones: List~Evaluacion~
    -triajes: List~Triaje~
    -historiales: List~Historial~
    +generarAlerta() Alerta
  }

  class Medico {
    <<backend>>
    -especialidad: String
    -licencia: String
    -telegramChatId: String
    -passwordHash: String
    -triajes: List~Triaje~
    +atenderAlerta(id ObjectId) void
    +listarPendientes() List~Triaje~
  }

  %% ── Perfil y Evaluacion ──
  class Perfil {
    <<backend>>
    -_id: ObjectId
    -edad: Int
    -sexo: String
    -tipoSangre: String
    -alergias: String
    -paciente: Paciente
  }

  class Evaluacion {
    <<microservice>>
    -_id: ObjectId
    -fechaEvaluacion: DateTime
    -origenDatos: String
    -lectura: Lectura
    -prediccion: Prediccion
  }

  class Lectura {
    <<microservice>>
    -_id: ObjectId
    -cp: Int
    -trestbps: Int
    -chol: Int
    -fbs: Boolean
    -restecg: Int
    -thalach: Int
    -exang: Boolean
    -oldpeak: Float
    -slope: Int
    -ca: Int
    -thal: Int
    +exportarVector() List~Float~
  }

  class Prediccion {
    <<microservice>>
    -_id: ObjectId
    -versionModelo: String
    -probabilidad: Float
    -clasificacion: String
    -importanciaVariables: JSON
    -tiempoMs: Float
    -fecha: DateTime
    -metadataTecnica: JSON
    +interpretarResultado() String
  }

  %% ── Triaje y alertas ──
  class Triaje {
    <<backend>>
    -_id: ObjectId
    -probabilidadRiesgo: Float
    -nivelUrgencia: String
    -factoresCriticos: String
    -explicacionClinica: String
    -telegramEnviado: Boolean
    -atendida: Boolean
    -fechaEmision: DateTime
    -fechaAtencion: DateTime
    -workflow: Workflow
    -paciente: Paciente
    -medico: Medico
    -logs: List~Log~
    +notificarTelegram() Boolean
    +escalarUrgencia() void
  }

  class Alerta {
    <<backend>>
    -_id: ObjectId
    -tipo: String
    -mensaje: String
    -leida: Boolean
    -atendida: Boolean
    -fechaEmision: DateTime
    -fechaAtencion: DateTime
    -paciente: Paciente
    -medico: Medico
    -triaje: Triaje
    +marcarLeida() void
    +asignarMedico(m Medico) void
  }

  class Log {
    <<backend>>
    -_id: ObjectId
    -timestamp: DateTime
    -tipoEvento: String
    -detalle: String
    -exitoso: Boolean
    -errorMsg: String
    -triaje: Triaje
    +registrar() void
  }

  %% ── Clinico ──
  class Patologia {
    <<backend>>
    -_id: ObjectId
    -codigoCie11: String
    -nombre: String
    -categoria: String
    -factorRiesgoCardiaco: Boolean
    -pesoRiesgoModelo: Float
    -historiales: List~Historial~
    +esFactorDeRiesgo() Boolean
  }

  class Historial {
    <<backend>>
    -_id: ObjectId
    -fechaDiagnostico: Date
    -nivelSeveridad: String
    -controlada: Boolean
    -tratamientoActual: String
    -observaciones: String
    -ultimaRevision: DateTime
    -paciente: Paciente
    -patologia: Patologia
    +actualizarTratamiento() void
  }

  %% ── Telemetria ──
  class Dispositivo {
    <<backend>>
    -_id: ObjectId
    -tipo: String
    -modelo: String
    -sistemaOperativo: String
    -tokenAutenticacion: String
    -activo: Boolean
    -ultimoHeartbeat: DateTime
    -paciente: Paciente
    -telemetrias: List~Telemetria~
    +enviarTelemetria() void
    +revocarToken() void
  }

  class Telemetria {
    <<backend>>
    -_id: ObjectId
    -frecuenciaCardiaca: Float
    -anomaliaEcg: String
    -spo2: Float
    -timestamp: DateTime
    -estadoProcesamiento: String
    -dispositivo: Dispositivo
    -evento: Evento
    +validar() Boolean
    +enriquecerConLab() void
  }

  class Evento {
    <<backend>>
    -_id: ObjectId
    -tipo: String
    -ventanaInicio: DateTime
    -ventanaFin: DateTime
    -lecturas: Int
    -valorAgregado: JSON
    -workflow: Workflow
    +evaluarUmbrales() Boolean
  }

  %% ── Workflow ──
  class Workflow {
    <<interface>>
    +ejecutarFlujo(triggerTipo String, payload JSON) JSON
    +notificarUrgencia(medicoChatId String, mensaje String) Boolean
  }

  class Adapter {
    <<microservice>>
    -_id: ObjectId
    -proveedor: String
    -endpoint: String
    -flujo: Object
    -token: String
    +ejecutarFlujo(triggerTipo String, payload JSON) JSON
    +notificarUrgencia(medico Medico, mensaje String) Boolean
  }

  class Documento {
    <<microservice>>
    -_id: ObjectId
    -titulo: String
    -contenido: String
    -embedding: List~Float~
    -fuente: String
    -fechaIndexacion: DateTime
    -activo: Boolean
    +buscarSimilares(query String) List~Documento~
  }

  %% ── Relaciones ──

  %% Herencia
  Usuario <|-- Paciente
  Usuario <|-- Medico
  Adapter ..|> Workflow

  %% Paciente
  Paciente "1" --> "1" Perfil : perfil
  Paciente "1" --> "*" Evaluacion : evaluaciones
  Paciente "1" --> "*" Triaje : triajes
  Paciente "1" --> "*" Dispositivo : dispositivos
  Paciente "1" --> "*" Historial : historiales
  Paciente "1" --> "*" Alerta : alertas

  %% Evaluacion, Lectura y Prediccion
  Evaluacion "1" --> "1" Lectura : lectura
  Evaluacion "1" --> "1" Prediccion : prediccion

  %% Medico
  Medico "1" --> "*" Triaje : triajes
  Medico "1" --> "*" Alerta : alertas

  %% Alerta
  Alerta "0..1" --> "1" Triaje : triaje

  %% Triaje
  Triaje "1" --> "*" Log : logs
  Triaje "1" --> "1" Workflow : workflow

  %% Patologia
  Patologia "1" --> "*" Historial : historiales

  %% Dispositivo y Telemetria
  Dispositivo "1" --> "*" Telemetria : telemetrias

  %% Telemetria y Evento
  Telemetria "1" --> "*" Evento : genera
  Evento "1" --> "1" Workflow : procesa
```
