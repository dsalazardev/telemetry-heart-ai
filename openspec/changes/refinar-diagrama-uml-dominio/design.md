# Design — Refactor del Diagrama UML de Dominio

## Principios de diseño

1. **Ubicuidad del lenguaje**: Cada término del diagrama debe significar lo mismo para médicos, desarrolladores y agentes autónomos.
2. **Nombres simples en español**: Todas las clases usan nombres en singular, una sola palabra (Perfil, Evaluacion, Evento, Documento).
3. **Separación de responsabilidades**: Entidades de backend (persistencia, CRUD) vs microservice (ML, RAG) deben ser identificables.
4. **Desacoplamiento de técnicas SI1**: El modelo de dominio no debe cambiar si la técnica de Nivel 3 (AG, PSO, RL) cambia.
5. **Simplicidad académica**: El diagrama debe ser defendible en 10 min de presentación + 5 min de Q&A.

---

## 1. Separar Perfil en dos conceptos

### Problema original
`Perfil` mezclaba datos demográficos del paciente con feature vectors del dataset Cleveland y resultados del modelo.

### Diseño nuevo
Se reutiliza el nombre `Perfil` para los datos estables del paciente. Se crea `Evaluacion` para la snapshot clínica con datos fisiológicos + predicción.

```
Paciente "1" --> "1" Perfil : perfil
Paciente "1" --> "*" Evaluacion : evaluaciones
Evaluacion "1" --> "1" Prediccion : prediccion

class Evaluacion {
    -_id: ObjectId
    -fechaEvaluacion: DateTime
    -origenDatos: String          // "wearos", "manual", "lab"
    -datosFisiologicos: JSON      // {cp, trestbps, chol, fbs, ...}
    -prediccion: Prediccion
    +exportarVector() List~Float~
}

class Perfil {
    -_id: ObjectId
    -edad: Int
    -sexo: String
    -tipoSangre: String
    -alergias: String
    -paciente: Paciente
}
```

**Justificación**:
- `Perfil` conserva el nombre original pero ahora solo tiene datos estables
- `Evaluacion` representa UNA instancia de evaluación — permite histórico (relación 1:*)
- `datosFisiologicos: JSON` encapsula las variables del Cleveland sin acoplar la estructura al dominio
- El vector de características se exporta bajo demanda, no se almacena como entidad separada

---

## 2. Desacoplar Prediccion de parametros de AG

### Problema original
`Prediccion` contenía `generacionesAg`, `cromosomaOptimo`, `recallObtenido` — parámetros específicos de AG (Nivel 3).

### Diseño nuevo

```
class Prediccion {
    -_id: ObjectId
    -versionModelo: String
    -probabilidad: Float
    -clasificacion: String          // "bajo", "medio", "alto"
    -importanciaVariables: JSON
    -tiempoMs: Float
    -fecha: DateTime
    -metadataTecnica: JSON          // {tecnica: "AG", generaciones: 100, recall: 0.92, ...}
    +interpretarResultado() String
}
```

**Justificación**:
- `metadataTecnica: JSON` permite cualquier técnica SI1 (AG, PSO, RL, búsqueda) sin cambiar el esquema
- Se eliminan `generacionesAg`, `cromosomaOptimo`, `recallObtenido` como campos fijos
- La clasificación usa strings semánticos ("bajo", "medio", "alto") en vez de valores numéricos crípticos

---

## 3. Simplificar modelo de usuarios

### Problema original
`Medico` existía como entidad independiente. `Paciente` tenía datos demográficos. No había herencia ni concepto de autenticación.

### Diseño nuevo

```
class Usuario {
    -_id: ObjectId
    -documento: String
    -nombres: String
    -apellidos: String
    -telefono: String
    -activo: Boolean
}

class Paciente {
    -fechaNacimiento: Date
    -dispositivos: List~Dispositivo~
    -perfil: Perfil
    -evaluaciones: List~Evaluacion~
    -triajes: List~Triaje~
    -historiales: List~Historial~
    +generarAlerta() Alerta
}

class Medico {
    -especialidad: String
    -licencia: String
    -telegramChatId: String
    -passwordHash: String          // auth basica
    -triajes: List~Triaje~
    +atenderAlerta(id ObjectId) void
    +listarPendientes() List~Triaje~
}

Usuario <|-- Paciente
Usuario <|-- Medico
```

**Justificación**:
- `Usuario` como clase base evita duplicación de campos (documento, nombres, apellidos)
- `passwordHash` en Medico es lo único que necesita auth — simple, defendible en Q&A
- Paciente no tiene password — su autenticación es el dispositivo WearOS (token)
- Estructura clara para explicar en la presentación: "Tenemos usuarios, algunos son pacientes, otros son medicos"

---

## 4. Alerta como entidad de primera clase

### Problema original
`generarAlertas()` era un método en Paciente que devolvía `List` genérico — sin persistencia, sin trazabilidad.

### Diseño nuevo

```
class Alerta {
    -_id: ObjectId
    -tipo: String                  // "critico", "elevado", "informativo"
    -mensaje: String
    -leida: Boolean
    -atendida: Boolean
    -fechaEmision: DateTime
    -fechaAtencion: DateTime
    -paciente: Paciente
    -medico: Medico                // opcional, asignado al atender
    -triaje: Triaje                // opcional, si deriva en triaje
    +marcarLeida() void
    +asignarMedico(m Medico) void
}
```

**Relaciones**:
- `Paciente "1" --> "*" Alerta : alertas`
- `Medico "1" --> "*" Alerta : alertas` (alertas atendidas)
- `Alerta "0..1" --> "1" Triaje : triaje` (opcional)

**Justificación**:
- Alerta tiene ciclo de vida: emitida → leída → atendida → (opcional) triaje
- Se puede auditar, re-asignar, escalar
- En la demo: "llega alerta por Telegram → medico la atiende en el sistema → se genera triaje"

---

## 5. Documento para RAG

### Diseño nuevo

```
class Documento {
    -_id: ObjectId
    -titulo: String
    -contenido: String
    -embedding: List~Float~
    -fuente: String                // "uptodate", "guia_local", "pubmed"
    -fechaIndexacion: DateTime
    -activo: Boolean
    +buscarSimilares(query String) List~Documento~
}
```

**Justificación**:
- El microservice LangChain RAG necesita una fuente de documentos indexados
- `embedding` almacena el vector de búsqueda semántica (OpenAI / local)
- La fuente permite rastrear de dónde viene la información clínica — importante para la rúbrica: "justificar si RAG aplica"

---

## 6. Corregir Telemetria → Workflow

### Problema original
`Telemetria "1" --> "1" Workflow` — cada lectura individual de wearable dispara un workflow. Inviable para 30 pacientes en tiempo real.

### Diseño nuevo
Se introduce `Evento` como agregador intermedio entre las lecturas crudas y el workflow.

```
Telemetria "1" --> "*" Evento : genera
Evento "1" --> "1" Workflow : procesa

class Evento {
    -_id: ObjectId
    -tipo: String                  // "anomalia_ecg", "umbral_fc", "reporte_periodico"
    -ventanaInicio: DateTime
    -ventanaFin: DateTime
    -lecturas: Int
    -valorAgregado: JSON           // {fc_promedio, spo2_min, ...}
    -workflow: Workflow
    +evaluarUmbrales() Boolean
}
```

**Justificación**:
- `Evento` agrega N lecturas de telemetría en una ventana de tiempo antes de disparar el workflow
- Reduce drásticamente las ejecuciones de n8n (de 86k/día a ~288/día asumiendo ventanas de 5 min)
- Se puede configurar: cada 5 min, o solo cuando hay anomalía, o ambos

---

## 7. Fronteras backend ↔ microservice

Se añaden notas UML con los estereotipos `<<backend>>` y `<<microservice>>`:

| Modulo | Entidades |
|--------|-----------|
| `<<backend>>` | Usuario, Paciente, Medico, Perfil, Dispositivo, Telemetria, Evento, Triaje, Alerta, Log, Patologia, Historial |
| `<<microservice>>` | Evaluacion, Prediccion, Documento |
| `<<interface>>` compartida | Workflow |

Se incluye una leyenda al inicio del diagrama explicando los estereotipos.

---

## 8. Workflow interface

```
class Workflow {
    <<interface>>
    +ejecutarFlujo(triggerTipo: String, payload: JSON) JSON
    +notificarUrgencia(medicoChatId: String, mensaje: String) Boolean
}

class Adapter {
    <<microservice>>
    -proveedor: String
    -endpoint: String
    -flujo: Object
    -token: String
    +ejecutarFlujo(triggerTipo String, payload JSON) JSON
    +notificarUrgencia(medico Medico, mensaje String) Boolean
}

Adapter ..|> Workflow
```

La interfaz se mantiene con payload JSON genérico en el UML. La estructura concreta del payload para cada triggerType se documenta en la especificacion de orquestacion (`openspec/specs/orquestacion/spec.md`).
