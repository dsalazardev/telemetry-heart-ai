# Análisis Profundo — Diagrama UML de Clases v2.0

**Fecha:** 2026-06-07
**Diagrama analizado:** `Documents/Diagrama UML.md`
**Versión del diagrama:** Exportado desde Lucidchart, con refinamientos post-refactor

---

## PARTE 1: MAQUETA DEL DOMINIO

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SISTEMA DE DOMINIO                         │
│              18 clases, 3 módulos, 18 relaciones                    │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  <<BACKEND>>  (12 clases)                                       │
  │  ─────────────────────────────────────────────                   │
  │  Persiste datos en SQL y expone vía API REST.                   │
  │  Núcleo transaccional del sistema.                              │
  │                                                                  │
  │  Usuario ──┬── Paciente                                          │
  │            └── Medico                                            │
  │  Perfil, Triaje, Alerta, Log                                     │
  │  Patologia, Historial                                            │
  │  Dispositivo, Telemetria, Evento                                 │
  │                                                                  │
  │  CRITERIO: Si la entidad almacena estado clínico o de            │
  │  configuración que debe ser consultable por el frontend           │
  │  o por n8n, es <<backend>>.                                      │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  <<MICROSERVICE>>  (5 clases)                                    │
  │  ──────────────────────────────────────                          │
  │  Internas del pipeline de IA (LangChain + ML).                   │
  │  NO persisten directamente — consumen datos del backend.         │
  │                                                                  │
  │  Evaluacion, Lectura, Prediccion                                 │
  │  Documento, Adapter                                              │
  │                                                                  │
  │  CRITERIO: Si la entidad es un snapshot de evaluación,           │
  │  resultado de modelo de ML, o recurso de RAG, es                 │
  │  <<microservice>>.                                               │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  <<INTERFACE>>  (1 clase)                                        │
  │  ─────────────────────────                                       │
  │  Contrato compartido entre módulos.                              │
  │                                                                  │
  │  Workflow                                                        │
  │                                                                  │
  │  CRITERIO: Define el contrato de orquestación. Backend lo        │
  │  usa (Triaje, Evento), Adapter lo implementa (microservice).    │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘
```

### Matriz completa de clasificación

| Módulo | Clases | Porcentaje |
|--------|--------|-----------|
| `<<backend>>` | Usuario, Paciente, Medico, Perfil, Triaje, Alerta, Log, Patologia, Historial, Dispositivo, Telemetria, Evento | **66.7%** |
| `<<microservice>>` | Evaluacion, Lectura, Prediccion, Documento, Adapter | **27.8%** |
| `<<interface>>` | Workflow | **5.5%** |

---

## PARTE 2: ANÁLISIS DE CADA CLASE

---

### Clase: Usuario
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Base de identidad del sistema. Contiene los datos personales y credenciales de autenticación. Es la clase padre de Paciente y Medico.
**Atributos clave:**
- `correo + password`: Modelo de autenticación unificado. Notable mejora respecto a la versión anterior donde Medico tenía passwordHash y Paciente no tenía nada.
- `documento`: Identificador civil único (cédula). Clave para integración con sistemas de salud colombianos.
- `activo`: Permite desactivar usuarios sin borrarlos (soft delete).
**Métodos clave:** Ninguno — es una clase puramente de datos.
**Relaciones:**
- `Usuario <|-- Paciente` (herencia)
- `Usuario <|-- Medico` (herencia)
**¿Podría moverse a microservice?** No. La autenticación es responsabilidad del backend. El microservicio no debe gestionar usuarios.

---

### Clase: Paciente
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Sujeto clínico central del sistema. Representa a la persona siendo monitoreada. Agrega todos sus datos clínicos y de monitoreo.
**Atributos clave:**
- `fechaNacimiento`: Permite calcular edad dinámicamente (no almacenada).
- `alertas: List~Alerta~`: Referencia a las alertas generadas. Relación bidireccional.
**Métodos clave:**
- `registrarIngreso(): void` — Marca la entrada del paciente al sistema de triaje (ej. cuando llega a urgencias).
- `generarAlertas(): List` — Crea alertas basadas en las evaluaciones de riesgo. Devuelve lista genérica (podría tipificarse mejor).
**Relaciones:**
- `Paciente "1" --> "1" Perfil : perfil`
- `Paciente "1" --> "*" Evaluacion : evaluaciones`
- `Paciente "1" --> "*" Triaje : triajes`
- `Paciente "1" --> "*" Dispositivo : dispositivos`
- `Paciente "1" --> "*" Historial : historiales`
- `Paciente "1" --> "*" Alerta : alertas`
**¿Podría moverse a microservice?** No. Es la entidad principal del backend. El microservicio no debe gestionar pacientes.

---

### Clase: Medico
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Profesional de la salud que atiende alertas y gestiona triajes. Hereda datos de autenticación de Usuario.
**Atributos clave:**
- `telegramChatId`: Canal de notificación. El médico recibe alertas por Telegram.
- `licencia`: Identificador profesional (tarjeta profesional). Importante para auditoría clínica.
- `especialidad`: Permite asignar alertas al médico apropiado (cardiólogo vs. general).
**Métodos clave:**
- `atenderAlerta(id ObjectId): void` — El médico marca una alerta como "en atención". La alerta existe como entidad separada, este método la actualiza.
- `listarPendientes(): List~Triaje~` — Consulta los triajes no resueltos. Útil para el dashboard del frontend.
**Relaciones:**
- `Medico "1" --> "*" Triaje : triajes`
- `Medico "1" --> "*" Alerta : alertas`
**¿Podría moverse a microservice?** No. La gestión de médicos y su autenticación es del backend.

---

### Clase: Perfil
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Datos demográficos y clínicos estables del paciente. Es 1:1 con Paciente.
**Atributos clave:**
- `edad, sexo, tipoSangre`: Variables demográficas que el modelo predictivo可能需要como entrada (edad, sexo) o para contexto clínico (tipoSangre).
- `alergias`: Información crítica para la seguridad del paciente.
**Métodos clave:** Ninguno.
**Relaciones:**
- `Paciente "1" --> "1" Perfil : perfil`
- `Perfil - paciente: Paciente` (bidireccional)
**¿Podría moverse a microservice?** Podría argumentarse, pero tiene sentido en backend porque los datos demográficos son persistentes y los consulta el frontend independientemente de la IA. Además, el microservice accede a ellos a través del backend (por diseño, según README).

---

### Clase: Triaje
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Resultado clínico de la evaluación de riesgo. Es el artefacto central del flujo de trabajo médico: contiene la decisión de urgencia y su justificación.
**Atributos clave:**
- `probabilidadRiesgo + nivelUrgencia`: El output del modelo (probabilidad numérica + clasificación semántica "bajo/medio/alto").
- `explicacionClinica`: Texto generado por el RAG para que el médico entienda el "por qué" de la alerta.
- `factoresCriticos`: Las variables que más contribuyeron al riesgo (ej: "oldpeak elevado + thal reversible").
- `alerta`: Referencia cruzada a la alerta (bidireccional).
**Métodos clave:**
- `notificarTelegram(): Boolean` — Envía la alerta al médico vía Workflow. Usa el Adapter correspondiente (n8n o LangChain).
- `escalarUrgencia(): void` — Si el médico no responde en X tiempo, escala a otro médico o supervisor.
**Relaciones:**
- `Triaje "1" --> "*" Log : logs`
- `Triaje "1" --> "1" Workflow : workflow`
- `Paciente "1" --> "*" Triaje`
- `Medico "1" --> "*" Triaje`
- `Alerta "0..1" --> "1" Triaje`
- `Triaje - alerta, paciente, medico, workflow` (atributos de referencia)
**¿Podría moverse a microservice?** No. El triaje es el resultado clínico que persiste y se consulta. El microservicio produce la evaluación, no el triaje.

---

### Clase: Alerta
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Notificación de evento crítico con ciclo de vida completo: emitida → leída → atendida → (opcional) triaje.
**Atributos clave:**
- `leida + atendida`: Flags que modelan el ciclo de vida. Una alerta puede estar leída pero no atendida.
- `fechaEmision + fechaAtencion`: Permiten medir tiempo de respuesta (métrica clave para la rúbrica).
**Métodos clave:**
- `marcarLeida(): void` — El médico vio la alerta (acción más rápida, desde Telegram).
- `asignarMedico(medico: Medico): void` — Asigna un médico responsable. La alerta puede ser re-asignada.
**Relaciones:**
- `Alerta "0..1" --> "1" Triaje : triaje` — Una alerta PUEDE (pero no necesariamente) tener un triaje asociado.
- `Paciente "1" --> "*" Alerta : alertas`
- `Medico "1" --> "*" Alerta : alertas`
- `Triaje - alerta` (bidireccional)
**¿Podría moverse?** No. La alerta es puramente del backend. El microservicio no debe gestionar el ciclo de vida de notificaciones.

---

### Clase: Log
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Registro de auditoría para operaciones de triaje. Trazabilidad de cada acción.
**Atributos clave:**
- `tipoEvento`: Clasifica el log (ej: "notificacion_enviada", "triaje_creado", "alerta_atendida").
- `exitoso + errorMsg`: Permite monitorear fallos en notificaciones o procesos.
**Métodos clave:**
- `registrar(): void` — Persiste el log en la base de datos.
**Relaciones:**
- `Triaje "1" --> "*" Log : logs`
- `Log - triaje: Triaje` (cada log pertenece a un triaje)
**¿Podría moverse?** No. Es infraestructura del backend. El microservicio podría enviar eventos de log, pero el backend los persiste.

---

### Clase: Patologia
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Catálogo de condiciones clínicas codificadas según CIE-11, con peso de riesgo para el modelo predictivo.
**Atributos clave:**
- `codigoCie11`: Estándar internacional de codificación de enfermedades. Crítico para interoperabilidad clínica.
- `pesoRiesgoModelo`: Factor de ponderación que el modelo predictivo usa para ajustar el riesgo según comorbilidades.
**Métodos clave:**
- `esFactorDeRiesgo(): Boolean` — Evalúa si esta patología es un factor de riesgo cardiovascular conocido.
**Relaciones:**
- `Patologia "1" --> "*" Historial : historiales`
**¿Podría moverse?** No. Es un catálogo clínico que el backend gestiona y expone. El microservicio lo consulta indirectamente.

---

### Clase: Historial
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Diagnóstico específico de un paciente para una patología dada. Representa una condición activa o pasada.
**Atributos clave:**
- `fechaDiagnostico`: Cuándo se diagnosticó. Permite trazar la línea de tiempo clínica.
- `controlada`: Indica si la condición está siendo tratada exitosamente.
- `tratamientoActual`: Texto libre para el plan de tratamiento.
**Métodos clave:**
- `actualizarTratamiento(): void` — El médico modifica el tratamiento para esta condición.
**Relaciones:**
- `Paciente "1" --> "*" Historial : historiales`
- `Patologia "1" --> "*" Historial : historiales`
- `Historial - paciente, patologia`
**¿Podría moverse?** No. Es historial clínico puro, responsabilidad del backend.

---

### Clase: Dispositivo
**Estereotipo:** `<<backend>>`
**Responsabilidad:** WearOS vinculado a un paciente. Gestiona la autenticación del dispositivo y su estado.
**Atributos clave:**
- `tokenAutenticacion`: Token que identifica al dispositivo. El wearable se autentica con este token, no con credenciales de usuario.
- `ultimoHeartbeat`: Timestamp del último contacto. Permite detectar dispositivos caídos.
- `activo`: Permite desvincular dispositivos sin borrarlos.
**Métodos clave:**
- `enviarTelemetria(): void` — Inicia el envío de datos desde el dispositivo (llamado desde WearOS).
- `revocarToken(): void` — Invalida el token de autenticación (ej: si el dispositivo se pierde).
**Relaciones:**
- `Dispositivo "1" --> "*" Telemetria : telemetrias`
- `Paciente "1" --> "*" Dispositivo : dispositivos`
**¿Podría moverse?** No. La gestión de dispositivos es del backend. El microservicio no debe gestionar dispositivos IoT.

---

### Clase: Telemetria
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Lectura cruda de sensor enviada por el WearOS. Contiene los signos vitales en un instante de tiempo.
**Atributos clave:**
- `frecuenciaCardiaca + spo2 + anomaliaEcg`: Las tres señales vitales principales. La anomalía ECG es un string descriptivo (ej: "depresion_st", "taquicardia").
- `estadoProcesamiento`: Indica si esta telemetría ya fue procesada, está pendiente, o tuvo error.
- `evento`: Referencia al Evento que agrupa esta telemetría (bidireccional).
**Métodos clave:**
- `validar(): Boolean` — Valida que los valores estén en rangos fisiológicos (ej: FC entre 30-250).
- `enriquecerConLab(): void` — Cruza los datos de telemetría con resultados de laboratorio (si están disponibles).
**Relaciones:**
- `Dispositivo "1" --> "*" Telemetria : telemetrias`
- `Evento "1" --> "*" Telemetria : agrupa`
- `Telemetria - dispositivo, evento`
**¿Podría moverse?** Parcialmente. La telemetría cruda podría ser procesada por el microservicio, pero el backend la persiste para consulta del frontend. El diseño actual es correcto.

---

### Clase: Evento
**Estereotipo:** `<<backend>>`
**Responsabilidad:** Agregador de telemetría en una ventana temporal. Evita que cada lectura individual dispare un workflow.
**Atributos clave:**
- `ventanaInicio + ventanaFin`: Define el período de agregación (ej: 5 minutos). Crítico para reducir la carga del workflow.
- `valorAgregado: JSON`: Contiene estadísticas de la ventana (FC promedio, SpO2 mínima, número de anomalías, etc.).
- `lecturas: Int`: Contador de cuántas telemetrías individuales se agregaron.
- `telemetrias: List~Telemetria~`: Bidireccional con Telemetria.
**Métodos clave:**
- `evaluarUmbrales(): Boolean` — Compara el valor agregado contra umbrales clínicos configurables. Si supera un umbral, el workflow se disparará.
**Relaciones:**
- `Evento "1" --> "*" Telemetria : agrupa`
- `Evento "1" --> "1" Workflow : procesa`
- `Evento - workflow, telemetrias`
**¿Podría moverse?** No. Es lógica de negocio (evaluar umbrales, agregar datos) que el backend orquesta. El microservicio recibe eventos ya agregados.

---

### Clase: Evaluacion
**Estereotipo:** `<<microservice>>`
**Responsabilidad:** Snapshot completo de una evaluación de riesgo. Agrupa la lectura de datos fisiológicos y la predicción del modelo.
**Atributos clave:**
- `fechaEvaluacion`: Cuándo se realizó la evaluación. Permite reconstruir la línea de tiempo.
- `origenDatos`: Indica si los datos vinieron de WearOS, ingreso manual, o laboratorio ("wearos", "manual", "lab").
- `lectura + prediccion`: Referencias 1:1 a Lectura y Prediccion.
**Métodos clave:** Ninguno — es un contenedor (aggregate).
**Relaciones:**
- `Evaluacion "1" --> "1" Lectura : lectura`
- `Evaluacion "1" --> "1" Prediccion : prediccion`
- `Paciente "1" --> "*" Evaluacion : evaluaciones`
**¿Podría moverse?** Si se moviera al backend, el microservicio perdería su razón de ser (es quien produce la evaluación). No.

---

### Clase: Lectura
**Estereotipo:** `<<microservice>>`
**Responsabilidad:** Vector de características fisiológicas para el modelo predictivo. Mapea directamente a las 13 variables del Cleveland Heart Disease dataset.
**Atributos clave:**
- `cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal`: Las 11 variables del Cleveland dataset que el modelo predictivo usa como features.
- `evaluacion: Evaluacion`: Bidireccional (back-reference).
**Métodos clave:**
- `exportarVector(): List~Float~` — Exporta las variables como un vector numérico en el orden exacto que espera el modelo predictivo. Este método es el puente entre el dominio y el ML.
**Relaciones:**
- `Evaluacion "1" --> "1" Lectura : lectura`
- `Lectura - evaluacion`
**¿Podría moverse a backend?** No. La Lectura es el feature vector para el modelo de ML. Pertenece al microservicio porque es el input del pipeline de IA.

---

### Clase: Prediccion
**Estereotipo:** `<<microservice>>`
**Responsabilidad:** Resultado del modelo predictivo. Contiene la clasificación de riesgo, la importancia de variables, y metadatos de la técnica SI1 usada.
**Atributos clave:**
- `probabilidad: Float + clasificacion: String`: Output del modelo. Probabilidad numérica + etiqueta semántica ("bajo", "medio", "alto").
- `importanciaVariables: JSON`: Qué variables del Cleveland contribuyeron más al resultado (SHAP values o similar).
- `metadataTecnica: JSON`: Metadatos de la técnica SI1. Permite que Prediccion no se acople a AG/PSO/RL específicamente. Ej: `{"tecnica": "AG", "generaciones": 100, "recall": 0.92}`.
- `documentos: List~Documento~`: Documentos RAG relevantes para esta predicción (nueva relación bidireccional).
**Métodos clave:**
- `interpretarResultado(): String` — Genera una explicación en lenguaje natural del resultado, usando RAG para contextualizar clínicamente.
**Relaciones:**
- `Evaluacion "1" --> "1" Prediccion : prediccion`
- `Prediccion "1" --> "*" Documento : consulta` (nueva relación RAG)
- `Prediccion - evaluacion, documentos`
**¿Podría moverse a backend?** No. Es el núcleo del pipeline de IA.

---

### Clase: Documento
**Estereotipo:** `<<microservice>>`
**Responsabilidad:** Fuente de conocimiento clínico indexada para RAG. Contiene guías médicas, artículos, o cualquier documento que el LLM consulta para generar explicaciones.
**Atributos clave:**
- `contenido + embedding`: El texto del documento y su vector de búsqueda semántica. El embedding se genera con un modelo de embeddings (OpenAI, local, etc.).
- `fuente`: Procedencia del documento ("uptodate", "guia_local", "pubmed"). Permite auditar de dónde viene la información clínica.
- `prediccion: Prediccion`: Bidireccional con Prediccion.
**Métodos clave:**
- `buscarSimilares(query String): List~Documento~` — Búsqueda semántica por similitud de embeddings. Usado por el RAG para encontrar documentos relevantes a una consulta.
**Relaciones:**
- `Prediccion "1" --> "*" Documento : consulta`
- `Documento - prediccion`
**¿Podría moverse a backend?** Técnicamente sí — los documentos podrían persistirse en el backend. Pero el embedding y la búsqueda semántica son operaciones del microservicio. Mantenerlo en <<microservice>> es correcto porque es parte del pipeline RAG.

---

### Clase: Workflow
**Estereotipo:** `<<Interface>>`
**Responsabilidad:** Contrato de orquestación. Define cómo se ejecutan los flujos de trabajo y cómo se notifican las urgencias. Es la interfaz que separa la lógica de negocio de la implementación concreta (n8n vs. LangChain).
**Atributos clave:** Ninguno (es interfaz).
**Métodos clave:**
- `ejecutarFlujo(triggerTipo: String, payload: JSON): JSON` — Dispara un flujo de trabajo. El `triggerTipo` determina qué flujo ejecutar. El `payload` contiene los datos contextuales.
- `notificarUrgencia(medico: Medico, mensaje: String): Boolean` — Envía una notificación urgente a un médico específico.
**Relaciones:**
- `Adapter ..|> Workflow` (realización)
- `Triaje "1" --> "1" Workflow : workflow`
- `Evento "1" --> "1" Workflow : procesa`
**¿Podría moverse?** No. Es el contrato compartido. Por definición, es transversal.

---

### Clase: Adapter
**Estereotipo:** `<<microservice>>`
**Responsabilidad:** Implementación concreta del Workflow para un proveedor específico (n8n o LangChain). Cada proveedor tiene su propio Adapter con su configuración.
**Atributos clave:**
- `proveedor`: Identifica el motor ("n8n", "langchain"). Permite seleccionar la implementación en tiempo de ejecución.
- `endpoint + token`: Configuración de conexión al proveedor. Para n8n sería la URL del webhook; para LangChain sería la configuración interna.
- `flujo: Object`: Definición del flujo (podría ser el JSON de n8n o la definición de la cadena de LangChain).
**Métodos clave:**
- `ejecutarFlujo(triggerTipo, payload): JSON` — Implementa la interfaz. Delega en el proveedor concreto.
- `notificarUrgencia(medico, mensaje): Boolean` — Implementa la interfaz. Envía la notificación según el proveedor.
**Relaciones:**
- `Adapter ..|> Workflow` (realización)
**¿Podría moverse?** Está correctamente ubicado en <<microservice>> porque la implementación concreta del workflow (especialmente si es LangChain) es responsabilidad del microservicio. Si el proveedor es n8n, la comunicación es vía HTTP, pero el Adapter sigue siendo del microservicio.

---

## PARTE 3: ANÁLISIS DE RELACIONES

### 3a. Herencia: Usuario → Paciente / Medico

```
         ┌──────────────┐
         │   Usuario    │
         │ documento    │
         │ nombres      │
         │ apellidos    │
         │ correo       │
         │ password     │  ← Autenticación centralizada
         │ telefono     │
         │ activo       │
         └──────┬───────┘
                 │
      ┌──────────┼──────────┐
      ▼                     ▼
┌────────────┐      ┌────────────┐
│  Paciente  │      │   Medico   │
│ fechaNac   │      │ especialid │
│ perfil     │      │ licencia   │
│ dispositivos│     │ telegramId │
│ evaluacion │      │ triajes    │
│ triajes    │      │ alertas    │
│ historiales│      │ +atender() │
│ alertas    │      │ +pendientes│
│ +registrar │
│ +generarAl │
└────────────┘      └────────────┘
```

**¿Tiene sentido?** Sí. Ambos roles comparten datos de identidad (documento, nombres, apellidos). Sin herencia, estos campos se duplicarían. La herencia también refleja correctamente la relación "es-un": un Médico es un Usuario, un Paciente es un Usuario.

**¿Qué más podría heredar?**
- **Administrador**: Usuario con permisos de gestión del sistema, sin relación con pacientes ni triajes.
- **Investigador**: Acceso de solo lectura a datos anonimizados para estudios. Podría heredar y tener métodos como `exportarDataset()`.

**Decisión de diseño notable**: Usuario tiene `correo + password`. Esto centraliza la autenticación. El Médico ya no tiene `passwordHash` (como en versiones anteriores del diagrama). Paciente hereda `password`, aunque en la práctica el paciente se autentica mediante el token del dispositivo WearOS, no con credenciales. Esto es un poco confuso — ver Pregunta Abierta #4.

### 3b. Realización: Adapter ..|> Workflow

```
┌───────────────────┐           ┌──────────────────────┐
│   <<Interface>>   │           │     Adapter          │
│     Workflow      │◄──────────│   <<microservice>>    │
│                   │  realiza  │                      │
│ +ejecutarFlujo()  │           │ +ejecutarFlujo()     │
│ +notificarUrg()   │           │ +notificarUrg()      │
└───────────────────┘           │ -proveedor           │
                                │ -endpoint            │
                                │ -flujo               │
                                │ -token               │
                                └──────────────────────┘
```

**¿Qué implica?** El sistema puede tener MÚLTIPLES implementaciones del Workflow sin que Triaje o Evento lo sepan. Esto permite:
- **Nivel 1**: Adapter(n8n) — el flujo visual de n8n orquesta la evaluación
- **Nivel 2**: Adapter(LangChain) — LangChain reemplaza a n8n, con un Adapter que llama al chain/agent directamente

**Problema detectado**: En el diagrama solo hay UNA clase Adapter que almacena `proveedor` como atributo para distinguir n8n de LangChain. Esto es más un **Strategy parametrizado** que un **polimorfismo de herencia**. En código, sería:
```python
if self.proveedor == "n8n":
    # llamar a webhook
elif self.proveedor == "langchain":
    # ejecutar chain local
```
No es incorrecto, pero pierde la oportunidad de tener subclasses `N8nAdapter` y `LangChainAdapter`.

### 3c. Agregación vs. Composición: Evaluacion → Lectura + Prediccion

```
┌────────────────────────────────────────────┐
│               Evaluacion                    │
│  -fechaEvaluacion: DateTime                │
│  -origenDatos: String                      │
├────────────────────────────────────────────┤
│  -lectura: Lectura        ──── 1:1         │
│  -prediccion: Prediccion  ──── 1:1         │
└────────────────────────────────────────────┘
```

**Es COMPOSICIÓN (no agregación)**, porque:
1. Una Lectura no existe sin una Evaluacion (no hay relación "Lectura → Evaluacion?")
2. Una Prediccion no existe sin una Evaluacion
3. El ciclo de vida está ligado: si se borra la Evaluacion, se borran Lectura y Prediccion
4. En UML, composición se representa con rombo relleno ◆—, pero el diagrama usa flecha simple -->. **Esto es una imprecisión del diagrama**: debería usar ◆-- para indicar que Evaluacion es el todo y Lectura/Prediccion son partes.

### 3d. Asociaciones clave

**Evento "1" --> "*" Telemetria : agrupa**

¿Por qué Evento → Telemetria y no al revés? Porque el **Evento es el contenedor** que agrupa múltiples telemetrías. La dirección es: Evento conoce a sus Telemetrias. Esto permite que Evento calcule `valorAgregado` (promedio, mínimo, máximo) de todas las telemetrías en su ventana.

Flujo:
1. Llegan N telemetrías en 5 minutos
2. El backend las asigna a un Evento activo (o crea uno nuevo si no existe)
3. Cuando la ventana se cierra, Evento.evaluarUmbrales() decide si dispara el workflow

**Prediccion "1" --> "*" Documento : consulta**

¿Cómo fluye la información?
1. Prediccion tiene un resultado (probabilidad=0.85, clasificacion="alto")
2. interpretarResultado() necesita explicar por qué
3. Construye un query con los factores críticos
4. Llama a Documento.buscarSimilares(query) que devuelve documentos relevantes
5. El LLM usa esos documentos para generar la explicación clínica

**Alerta "0..1" --> "1" Triaje : triaje**

¿Por qué "0..1" y no "1"? Porque una alerta puede existir sin un triaje asociado. Ejemplo:
- Se detecta una anomalía menor que no requiere triaje completo
- Se envía una alerta informativa al médico
- El médico la revisa y decide que no necesita acción → nunca se crea un Triaje

Cuando una alerta SÍ deriva en triaje, la relación se activa (se convierte en 1).

**Triaje "1" --> "1" Workflow : workflow**

¿Qué significa esta relación 1:1? Que CADA triaje tiene EXACTAMENTE UN workflow asociado. Esto tiene sentido porque:
1. Cuando se crea un triaje, se ejecuta un workflow para notificar al médico
2. Ese workflow es específico para ese triaje
3. No hay triaje sin workflow asociado

Pero OJO: esto NO significa que Triaje y Workflow tengan el mismo ciclo de vida. El Workflow puede existir independientemente (es una interfaz). La relación es de uso, no de composición.

---

## PARTE 4: FLUJO DE DATOS COMPLETO

```
LEGEND:
  [Backend] → procesado por el backend
  [Micro]   → procesado por el microservicio
  [n8n]     → orquestado por n8n
  (if)      → decisión condicional
  ===      → límite de módulo

┌─────────────────────────────────────────────────────────────────────┐
│                  FLUJO COMPLETO: WEAROS → MÉDICO                    │
└─────────────────────────────────────────────────────────────────────┘

PASO 1: Telemetría desde WearOS
───────── ──────────────────────
[WearOS] → POST /api/telemetria (REST)
[Backend] → Dispositivo.enviarTelemetria()
  Crea: Telemetria { frecuenciaCardiaca, spo2, anomaliaEcg, timestamp }
  Ejecuta: Telemetria.validar()  ← (if) valores en rango fisiológico?
    ├── Sí: continúa
    └── No: Log.registrar("telemetria_invalida") → descarta

PASO 2: Agregación en Evento
───────── ────────────────
[Backend] → Busca Evento activo para este Dispositivo
    ├── (if) ¿Existe Evento abierto en ventana?
    │     └── Sí: asigna Telemetria a Evento existente
    │     └── No: crea nuevo Evento { ventanaInicio=now, ventanaFin=now+5min }
    │
[Backend] → Evento.lecturas++
[Backend] → Evento.valorAgregado = { fc_promedio, spo2_min, num_anomalias, ... }

PASO 3: Evaluación del Evento
───────── ────────────────
[Backend] → (if) ¿ventanaFin alcanzada O anomalía crítica?
    ├── No: esperar más telemetrías
    └── Sí:
         [Backend] → Evento.evaluarUmbrales()  
              └── (if) ¿supera umbral?
                    ├── No: Log.registrar("evento_descartado")
                    └── Sí: continúa

PASO 4: Disparo del Workflow
───────── ──────────────
[Backend] → Workflow.ejecutarFlujo("evaluacion_riesgo", {
    eventoId, dispositivoId, pacienteId, valorAgregado
  })
              │
              ▼
    ┌─── Realiza ───┐
    │               │
[Adapter(n8n)]   [Adapter(LangChain)]
    │               │
    │  Nivel 1      │  Nivel 2
    │  (orquesta     │  (ejecuta chain/
    │   vía n8n)    │   agent directo)
    └───────┬───────┘
            │
            ▼

PASO 5: Evaluación de Riesgo (Microservicio)
───────── ──────────────────────────
[Micro] → Recibe payload del Workflow
[Micro] → Crea Evaluacion { fechaEvaluacion, origenDatos }
[Micro] → Crea Lectura { cp, trestbps, chol, ..., thal }
[Micro] → Ejecuta: Lectura.exportarVector() → [63.0, 145.0, 233.0, ...]
[Micro] → Modelo predictivo recibe vector → output { probabilidad, clasificacion }
[Micro] → Crea Prediccion { versionModelo, probabilidad, clasificacion, 
                             importanciaVariables, metadataTecnica, tiempoMs }
[Micro] → (if) ¿metadataTecnica indica técnica aplicada?
              └── Almacena { tecnica, generaciones, recall, etc }

PASO 6: Explicabilidad (RAG)
───────── ──────────────
[Micro] → Evaluacion.prediccion.interpretarResultado()
              │
              ▼
[Micro] → Construye query con factores críticos
[Micro] → Documento.buscarSimilares(query)
              │
              ▼
[Micro] → Recibe documentos relevantes
[Micro] → LLM genera explicación clínica
[Micro] → Almacena explicacionClinica

PASO 7: Retorno del Workflow
───────── ──────────────
[Adapter] → Devuelve resultado al backend vía Workflow
[Backend] → Recibe: { evaluacionId, prediccion {prob, clasif}, explicacion }

PASO 8: Creación de Triaje
───────── ─────────────
[Backend] → (if) ¿clasificacion == "alto" O "medio"?
    ├── No: Log.registrar("evaluacion_sin_riesgo")
    │         (opcional) Alerta informativa
    └── Sí:
         [Backend] → Crea Triaje {
             probabilidadRiesgo, nivelUrgencia,
             factoresCriticos, explicacionClinica,
             workflow, paciente, medico
           }
         [Backend] → Workflow.notificarUrgencia(medico, mensaje)
         [Backend] → Triaje.notificarTelegram()

PASO 9: Generación de Alerta
───────── ──────────────
[Backend] → Paciente.generarAlertas()
[Backend] → Crea Alerta { tipo, mensaje, paciente, triaje }
[Backend] → Asigna médico disponible (o deja sin asignar)
[Backend] → Log.registrar("alerta_creada")

PASO 10: Recepción Médica
───────── ─────────────
[Médico] ← Recibe notificación en Telegram
[Médico] ← Ve Alerta en frontend
[Médico] → Alerta.marcarLeida()
[Médico] → Alerta.asignarMedico(médico) 
[Médico] → (if) Revisa Triaje
              │
              ├── Triaje.atendida = true
              ├── Triaje.fechaAtencion = now
              └── Log.registrar("triaje_atendido")
```

---

## PARTE 5: IDENTIFICACIÓN DE PATRONES

| Patrón | ¿Dónde aparece? | ¿Cómo se implementa? |
|--------|-----------------|----------------------|
| **Strategy** | Workflow + Adapter | La interfaz Workflow define el contrato. Adapter lo implementa con un `proveedor` que selecciona la estrategia (n8n vs LangChain) |
| **Aggregate Root** | Evaluacion | Evaluacion es el root que encapsula Lectura + Prediccion. Nadie más referencia a Lectura o Prediccion directamente. |
| **Repository** | (implícito) | Las clases `<<backend>>` se persistirían vía un patrón Repository. No está en el diagrama UML, pero es implícito en la arquitectura. |
| **Observer (implícito)** | Alerta → Medico | Cuando se crea una Alerta, el médico es notificado vía Telegram. Es un observer: el sujeto (Triaje) notifica al observador (Medico) mediante un evento (Alerta). |
| **Composite** | (parcial) | Paciente "contiene" Perfil, Dispositivos, Evaluaciones, Triajes, etc. Es agregación, no Composite puro. |
| **Adapter (GoF)** | Adapter | Adapter adapta la interfaz Workflow a la implementación concreta (n8n webhook / LangChain chain). |
| **Value Object** | Lectura | Lectura es un value object: sus atributos (cp, trestbps...) definen su identidad. No tiene identidad propia más allá de sus valores. |

### Análisis detallado de cada patrón

**Strategy**
```
Problema que resuelve: Triaje y Evento necesitan ejecutar flujos de
trabajo sin conocer el motor específico (n8n vs LangChain).

Solución: Workflow define la interfaz. Adapter la implementa.
Triaje y Evento dependen de Workflow (abstracción), no de Adapter
(concreto).

¿Es realmente Strategy? Parcialmente. Strategy puro tendría múltiples
clases concretas (N8nAdapter, LangChainAdapter). En el diagrama actual,
Adapter es una sola clase con un atributo 'proveedor' que hace switch.
Esto es 'Strategy con parametrización', válido pero menos expresivo.
```

**Aggregate Root (Evaluacion)**
```
Problema que resuelve: Garantizar consistencia entre la lectura de
datos y la predicción del modelo. No puede existir una predicción
sin su lectura correspondiente.

Solución: Evaluacion es el único punto de entrada para crear/modificar
Lectura y Prediccion. Ninguna otra clase del sistema referencia
directamente a Lectura o Prediccion.

Invariante: Evaluacion siempre tiene exactamente 1 Lectura y 1 Prediccion.
```

**Observer (implícito)**
```
Problema que resuelve: Notificar al médico cuando hay una alerta sin
acoplar el Triaje al sistema de notificaciones.

Solución: 
1. Triaje se crea (sujeto)
2. Triaje.notificarTelegram() dispara la notificación
3. Internamente, llama a Workflow.notificarUrgencia()
4. El médico recibe el mensaje en Telegram

No es Observer formal (no hay interface Observer<T> ni lista de
suscriptores), pero el flujo de eventos es el mismo.

Limitación: Si un triaje necesita notificar a MÚLTIPLES médicos
(escalar), el patrón actual no lo soporta sin modificación.
```

---

## PARTE 6: MAPEO A LA RÚBRICA ACADÉMICA

### Nivel 1 — n8n (0.0 - 3.5)

**Clases relevantes:**
- `Workflow` (interface) — el contrato que n8n implementa
- `Adapter` (proveedor="n8n") — la implementación concreta para n8n
- `Triaje.notificarTelegram()` — la acción que n8n ejecuta
- `Alerta` — el objeto de la notificación
- `Log` — auditoría de la ejecución del flujo

**¿Qué cubre el diagrama?**
- El flujo trigger → procesamiento → salida está cubierto por Evento → Workflow → Triaje
- Las notificaciones vía Telegram están cubiertas por Triaje.notificarTelegram()
- La auditoría está cubierta por Log

**¿Qué falta?**
- No hay una representación explícita del flujo n8n en el diagrama (no debería — es un detalle de implementación)
- El JSON exportado de n8n no tiene representación en el diagrama

**¿Qué sobra?** Nada para este nivel. El diagrama cubre bien el Nivel 1.

### Nivel 2 — LangChain (3.5 - 4.5)

**Clases relevantes:**
- `Evaluacion` — el contexto de la evaluación que LangChain procesa
- `Lectura` — el feature vector que el modelo predictivo consume
- `Prediccion.interpretarResultado()` — genera explicación vía LLM
- `Documento` — base de conocimiento para RAG
- `Documento.buscarSimilares()` — retrieval semántico

**¿Qué cubre el diagrama?**
- ChatPromptTemplate → Evaluacion + Lectura (el LLM recibe los datos del paciente)
- Tools → exportarVector() es una tool que el agente LangChain puede llamar
- RAG → Documento con embeddings y búsqueda semántica
- Chain/Agent → interpretarResultado() es la cadena de razonamiento

**¿Qué falta?**
- No hay representación explícita de ChatPromptTemplate (no debería — es detalle de LangChain)
- Memory / historial de conversación no está modelado (¿el médico puede hacer preguntas de seguimiento?)
- La cadena de pensamiento (CoT) no está visible en el diagrama

**¿Qué sobra?** Nada.

### Nivel 3 — Metaheurísticas (+0.5)

**Clases relevantes:**
- `Prediccion.metadataTecnica: JSON` — contiene los parámetros de la técnica SI1
- `Prediccion.versionModelo` — versión del modelo optimizado
- `Lectura.exportarVector()` — genera el feature vector que la metaheurística optimiza

**¿Qué cubre el diagrama?**
- `metadataTecnica` permite cualquier técnica (AG, PSO, RL, búsquedas) sin cambiar el esquema
- `versionModelo` permite rastrear qué versión del modelo se usó

**¿Qué falta?**
- No hay representación de la función objetivo ni del espacio de búsqueda
- No hay métricas de rendimiento de la técnica (generaciones, recall, fitness) visibles en el diagrama — aunque están en metadataTecnica

**¿Qué sobra?** Nada. El diseño es intencionalmente agnóstico a la técnica específica.

### Resumen del mapeo

```
NIVEL 1 (n8n)    ─── Workflow, Adapter, Triaje, Alerta, Log
                              
                                  TRANSICIÓN n8n → LangChain
                                  El Adapter cambia de proveedor="n8n" 
                                  a proveedor="langchain". El resto del
                                  sistema no se modifica.
                              
NIVEL 2 (LangChain) ─── Evaluacion, Lectura, Prediccion, Documento
                         interpretarResultado(), exportarVector(),
                         buscarSimilares()

                                  EXTENSIÓN con metaheurísticas
                                  metadataTecnica captura los parámetros
                                  de la técnica sin cambiar el esquema.
                              
NIVEL 3 (Metaheurísticas) ─── metadataTecnica: JSON en Prediccion
                               exportarVector() en Lectura
```

---

## PARTE 7: PREGUNTAS ABIERTAS

Estas son preguntas que UN AGENTE AUTÓNOMO NO PUEDE RESPONDER solo con el diagrama y necesitaría especificación adicional:

| # | Pregunta | Impacto | ¿Dónde debería responderlo? |
|---|----------|---------|----------------------------|
| 1 | **¿Cada cuánto se envía telemetría desde WearOS?** ¿Cada 1s? ¿5s? ¿Ante cada latido? | Determina la ventana del Evento y la frecuencia de evaluaciones. | `specs/telemetria/spec.md` |
| 2 | **¿Cuánto dura la ventana de tiempo de un Evento?** ¿5 minutos? ¿10? ¿Configurable? | Determina cuántas telemetrías se agregan y cada cuánto se dispara el workflow. | `specs/evento/spec.md` |
| 3 | **¿Cuáles son los umbrales de riesgo concretos?** ¿FC > 120 y SpO2 < 90% disparan alerta? ¿O depende del perfil del paciente? | Sin esto, `evaluarUmbrales()` no puede implementarse. | `specs/triaje/spec.md` |
| 4 | **¿Cómo se autentica realmente el Paciente?** Usuario tiene `password`, pero el paciente se autentica vía token del dispositivo WearOS. ¿El paciente tiene login? | Conflicto en el modelo de dominio: Paciente hereda password de Usuario pero no lo usa. | `specs/autenticacion/spec.md` |
| 5 | **¿Qué contiene exactamente el `payload: JSON` del Workflow?** ¿Qué estructura tiene para cada `triggerTipo`? | Sin esto, no se puede implementar la comunicación entre módulos. | `specs/orquestacion/spec.md` |
| 6 | **¿El Médico puede atender una alerta sin crear un Triaje?** Es decir, ¿puede marcar "falso positivo" y cerrar el ciclo? | Afecta el flujo Alerta → Triaje y el método `atenderAlerta()`. | `specs/alerta/spec.md` |
| 7 | **¿Quién alimenta el Documento (RAG)?** ¿Hay un proceso de indexación? ¿Sube el médico los documentos? | Sin fuente de datos, Documento.buscarSimilares() no tiene qué buscar. | `specs/rag/spec.md` |
| 8 | **¿Qué modelo de ML se usa?** ¿Random Forest? ¿XGBoost? ¿Red Neuronal? ¿Se entrena desde cero o se usa pre-entrenado? | Afecta Lectura.exportarVector() (¿mismo orden de features?) y Prediccion.versionModelo. | `specs/modelo-predictivo/spec.md` |
| 9 | **¿Se necesita WebSocket para telemetría en tiempo real en el frontend?** ¿O el médico hace polling REST? | Impacta la implementación del backend y del frontend. | `specs/frontend/spec.md` |
| 10 | **¿Qué ocurre si el Workflow falla?** ¿Reintento? ¿Cola de mensajes? ¿Notificar a otro médico? | Afecta Log, Triaje.escalarUrgencia(), y la confiabilidad del sistema. | `specs/orquestacion/spec.md` |
| 11 | **¿Cómo se maneja la reconexión de WearOS?** Si el dispositivo pierde conexión y recupera, ¿se reenvían telemetrías perdidas? | Afecta Dispositivo.ultimoHeartbeat y la integridad de los eventos. | `specs/wearos/spec.md` |
| 12 | **¿Cuál es el orden exacto de los 11 atributos en exportarVector()?** ¿Coincide con el orden que espera el modelo entrenado? | Si el orden no coincide, el modelo produce basura. | `specs/modelo-predictivo/spec.md` |

---

## PARTE 8: ANÁLISIS CRÍTICO

### Fortalezas (Top 3)

**1. Separación clara de responsabilidades**
Las fronteras entre módulos están bien definidas. Backend (persistencia + API), Microservice (IA + RAG), Interface compartida (Workflow). Un agente autónomo puede leer el diagrama y saber inmediatamente qué clase pertenece a qué módulo.

**2. Evento como agregador**
La introducción de Evento entre Telemetria y Workflow resuelve elegantemente el problema de "86k workflows/día". Es el tipo de decisión arquitectónica que un docente premiaría en Q&A porque muestra comprensión de escalabilidad.

**3. Desacoplamiento de técnicas SI1**
`Prediccion.metadataTecnica: JSON` es una jugada maestra para la rúbrica. Permite cambiar de AG a PSO a RL sin modificar el modelo de dominio. El estudiante puede explicar: "El diagrama no cambia si cambio la técnica del Nivel 3 — solo cambia el JSON de metadata."

### Debilidades (Top 3)

**1. Ausencia de relación Evento → Evaluacion**
El flujo de datos tiene un agujero: Evento dispara Workflow, Workflow es una interfaz, pero no hay ninguna relación que muestre cómo el resultado del Workflow se conecta con Evaluacion. ¿Quién crea la Evaluacion? ¿El microservicio al recibir el payload del Workflow? ¿El backend después de recibir la respuesta del Workflow? El diagrama no lo dice.

**2. Relaciones "1" --> "*" sin contexto temporal**
Paciente "1" --> "*" Evaluacion es correcto pero no captura la frecuencia. Un paciente podría tener 1 evaluación o 1000. No hay un límite o política de retención. Para ~30 pacientes en simulación no es problema, pero la omisión existe.

**3. Adapter no es polimórfico**
El Adapter es una sola clase que usa un atributo `proveedor` para distinguir implementaciones. Esto significa que en código habrá un `if proveedor == "n8n"` que viola el principio Open/Closed. Un diseño más limpio sería: `N8nAdapter` y `LangChainAdapter` como clases separadas que implementan `Workflow`. Esto es un punto débil para Q&A si el docente pregunta "¿cómo agregarían un tercer proveedor?"

### Riesgos

| Riesgo | Severidad | Explicación |
|--------|-----------|-------------|
| **R1. Contrato Workflow sin especificar** | Alta | `triggerTipo` y `payload` son genéricos. Sin especificar la estructura, backend y microservice no pueden comunicarse. Es la dependencia más crítica. |
| **R2. Documento aislado** | Alta | Documento tiene relación solo con Prediccion, pero no se muestra quién lo crea, indexa o mantiene. Si el RAG no tiene documentos, es una capacidad fantasma. |
| **R3. Sin representación de errores** | Media | Excepto Log.errorMsg, no hay modelado de fallos. ¿Qué pasa si el microservicio falla? ¿Si Telegram está caído? ¿Si n8n no responde? |
| **R4. Sin modelo de autorización** | Media | Usuario tiene password, pero no hay roles ni permisos. ¿Puede un médico ver todos los pacientes? ¿Puede un paciente ver sus propios datos? |
| **R5. Métricas de rendimiento no modeladas** | Baja | `tiempoMs` en Prediccion es la única métrica. No hay tiempo de respuesta de alertas, tasa de falsos positivos, ni SLAs. |

### Puntuación: 8.5 / 10

**Desglose:**
- **Completitud (2.5/3.0)**: 18 clases cubren el dominio. Falta conectar Evento→Evaluacion y especificar contratos.
- **Claridad (2.0/2.0)**: Estereotipos, nombres en español, relaciones etiquetadas. Meridianamente claro.
- **Consistencia (1.5/2.0)**: Algunas bidireccionalidades no se reflejan en ambas direcciones. Adapter no es polimórfico.
- **Acople (1.5/2.0)**: Backend y microservice están bien separados. Workflow como interfaz es correcto. Falta Evento→Evaluacion.
- **Implementabilidad (1.0/1.0)**: Un agente autónomo puede implementar contra este diagrama con las specs adecuadas.

### Resumen final

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VEREDICTO                                        │
│                                                                     │
│  El diagrama UML v2.0 es SÓLIDO.                                   │
│                                                                     │
│  • Las 18 clases están bien definidas y ubicadas                    │
│  • Las fronteras entre módulos son claras                           │
│  • Los patrones (Strategy, Aggregate, Observer) son correctos       │
│  • El diseño soporta los 3 niveles académicos sin modificación      │
│  • metadataTecnica es una solución elegante para el Nivel 3         │
│                                                                     │
│  Lo ÚNICO que falta para ser implementable es:                      │
│  1. Conectar Evento → Evaluacion (el eslabón perdido)              │
│  2. Especificar el contrato del Workflow payload                   │
│  3. Especificar umbrales de riesgo                                 │
│  4. Definir quién alimenta el Documento RAG                        │
│                                                                     │
│  NOTA SOBRE EVOLUCIÓN: Este diagrama ya incorpora refinamientos     │
│  importantes respecto a la versión analizada en                      │
│  Documents/exploracion-diagrama.md:                                  │
│  • Usuario ahora tiene correo + password (auth centralizada)        │
│  • Relaciones bidireccionales añadidas (Evaluacion↔Lectura,         │
│    Prediccion↔Documento, Evento↔Telemetria)                         │
│  • Nueva relación Prediccion "1"→"*" Documento (consulta RAG)      │
│  • Nueva relación Evento "1"→"*" Telemetria (agrupa)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
