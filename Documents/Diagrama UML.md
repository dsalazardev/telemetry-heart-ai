# Diagrama UML Original — Sistema de Triaje Cardiovascular IoT

**Fecha:** 2026-06-07
**Fuente:** Exportado desde Lucidchart (documento 2547e999-8026-4161-ac86-f46c584d174c)
**Nota:** Convertido desde PDF sin modificaciones.

---

```mermaid
classDiagram
  direction TB

  class Usuario {
    <<backend>>
    -_id: ObjectId
    -documento: String
    -nombres: String
    -apellidos: String
    -correo: String
    -password: String
    -telefono: String
    -activo: Boolean
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
    + marcarLeida(): void
    + asignarMedico(medico: Medico): void
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
    -evaluacion: Evaluacion
    + exportarVector(): List~Float~
  }

  class Evaluacion {
    <<microservice>>
    -_id: ObjectId
    -fechaEvaluacion: DateTime
    -origenDatos: String
    -lectura: Lectura
    -prediccion: Prediccion
  }

  class Medico {
    <<backend>>
    -especialidad: String
    -licencia: String
    -telegramChatId: String
    -triajes: List~Triaje~
    -alertas: LIst~Alerta~
    + atenderAlerta(id ObjectId): void
    + listarPendientes(): List~Triaje~
  }

  class Perfil {
    <<backend>>
    -_id: ObjectId
    -edad: Int
    -sexo: String
    -tipoSangre: String
    -alergias: String
    -paciente: Paciente
  }

  class Paciente {
    <<backend>>
    -fechaNacimiento: Date
    -perfil: Perfil
    -dispositivos: List~Dispositivo~
    -evaluaciones: List~Evaluacion~
    -triajes: List~Triaje~
    -historiales: List~Historial~
    -alertas: List~Alerta~
    + registrarIngreso(): void
    + generarAlertas(): List
  }

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
    -alerta: Alerta
    -logs: List~Log~
    + notificarTelegram(): Boolean
    + escalarUrgencia(): void
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
    + registrar(): void
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
    -evaluacion: Evaluacion
    -documentos: List~Documento~
    + interpretarResultado(): String
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
    -prediccion: Prediccion
    + buscarSimilares(query String): List~Documento~
  }

  class Patologia {
    <<backend>>
    -_id: ObjectId
    -codigoCie11: String
    -nombre: String
    -categoria: String
    -factorRiesgoCardiaco: Boolean
    -pesoRiesgoModelo: Float
    -historiales: List~Historial~
    + esFactorDeRiesgo(): Boolean
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
    + actualizarTratamiento(): void
  }

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
    + enviarTelemetria(): void
    + revocarToken(): void
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
    -telemetrias: List~Telemetria~
    + evaluarUmbrales(): Boolean
  }

  class Workflow {
    <<Interface>>
    + ejecutarFlujo (triggerTipo: String, payload: JSON): JSON
    + notificarUrgencia (medico: Medico, mensaje: String): Boolean
  }

  class Adapter {
    <<microservice>>
    -_id: ObjectId
    -proveedor: String
    -endpoint: String
    -flujo: Object
    -token: String
    + ejecutarFlujo(triggerTipo: String, payload: JSON): JSON
    + notificarUrgencia (medico: Medico, mensaje: String): Boolean
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
    + validar(): Boolean
    + enriquecerConLab(): void
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

  %% Evaluacion, Lectura, Prediccion
  Evaluacion "1" --> "1" Lectura : lectura
  Evaluacion "1" --> "1" Prediccion : prediccion

  %% Prediccion y RAG
  Prediccion "1" --> "*" Documento : consulta

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

  %% Dispositivo
  Dispositivo "1" --> "*" Telemetria : telemetrias

  %% Evento y Telemetria
  Evento "1" --> "*" Telemetria : agrupa
  Evento "1" --> "1" Workflow : procesa
```
