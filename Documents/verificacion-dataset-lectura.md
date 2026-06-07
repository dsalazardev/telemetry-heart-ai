# Verificación: Dataset Cleveland vs Clase Lectura (UML)

**Fecha:** 2026-06-07
**Archivos analizados:**
- `Documents/Input/heart.csv` — dataset Cleveland con 303 muestras, 14 columnas
- `Documents/Diagrama UML.md` — clases Lectura (11 atributos) y Perfil (4 atributos)

---

## 1. Tabla Comparativa CSV vs UML

```
CSV HEADER: age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target
           └──────────────────────── 13 FEATURES ────────────────────────┘└─OUTPUT─┘
```

| # | Variable CSV | Tipo en CSV  | ¿En UML Lectura? | Tipo UML Lectura | ¿En UML Perfil? | Tipo UML Perfil | ¿Coinciden? |
|---|-------------|-------------|-------------------|------------------|-----------------|-----------------|-------------|
| 1 | `age`       | int (29-77)  | ❌ **AUSENTE**    | —                | ✅ `edad`       | Int             | ⚠️ Nombre difiere (age→edad) |
| 2 | `sex`       | int (0/1)    | ❌ **AUSENTE**    | —                | ✅ `sexo`       | **String**      | 🔴 **Tipo incorrecto** CSV es 0/1, UML es String |
| 3 | `cp`        | int (0-3)    | ✅                | Int              | ❌              | —               | ✅ |
| 4 | `trestbps`  | int (94-200) | ✅                | Int              | ❌              | —               | ✅ |
| 5 | `chol`      | int (126-564)| ✅                | Int              | ❌              | —               | ✅ |
| 6 | `fbs`       | int (0/1)    | ✅                | **Boolean**      | ❌              | —               | ⚠️ CSV es int 0/1, UML es Boolean (convertible) |
| 7 | `restecg`   | int (0-2)    | ✅                | Int              | ❌              | —               | ✅ |
| 8 | `thalach`   | int (71-202) | ✅                | Int              | ❌              | —               | ✅ |
| 9 | `exang`     | int (0/1)    | ✅                | **Boolean**      | ❌              | —               | ⚠️ CSV es int 0/1, UML es Boolean (convertible) |
| 10| `oldpeak`   | float (0-6.2)| ✅                | Float            | ❌              | —               | ✅ |
| 11| `slope`     | int (0-2)    | ✅                | Int              | ❌              | —               | ✅ |
| 12| `ca`        | int (0-4)    | ✅                | Int              | ❌              | —               | ✅ |
| 13| `thal`      | int (0-3)    | ✅                | Int              | ❌              | —               | ✅ |
| 14| `target`    | int (0/1)    | ❌ **AUSENTE**    | —                | ❌              | —               | N/A — es output |

### Mapeo visual

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   DATASET CLEVELAND (heart.csv)                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  age  sex  cp  trestbps  chol  fbs  restecg  thalach  exang  │  │
│   │  oldpeak  slope  ca  thal          │ target                   │  │
│   └────────────────────────────────────┼──────────────────────────┘  │
│                    │                   │                             │
│                    ▼                   ▼                             │
│         ┌────────────────────┐   ┌──────────────┐                   │
│         │  UML: ¿DÓNDE?      │   │  UML: ¿DÓNDE? │                   │
│         └────────────────────┘   └──────────────┘                   │
│                    │                                                │
│     ┌──────────────┼──────────────────────────┐                     │
│     ▼              ▼                          ▼                     │
│  ┌──────┐   ┌──────────┐               ┌────────────┐              │
│  │age   │   │sex (0/1) │               │   target   │              │
│  │↓     │   │↓         │               │   ↓        │              │
│  │edad  │   │sexo:String│              │ probabilidad │              │
│  │Int   │   │🔴 DEBERÍA│              │ clasificacion│              │
│  │      │   │ser Int   │               └────────────┘              │
│  │PERFIL│   │PERFIL    │               PREDICCION                  │
│  └──────┘   └──────────┘                                           │
│                                                                     │
│   LECTURA (11 features):                                            │
│   cp  trestbps  chol  fbs  restecg  thalach                        │
│   exang  oldpeak  slope  ca  thal                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Discrepancias Encontradas

### 🔴 D1: age y sex están en Perfil (backend), no en Lectura (microservice)

**Problema crítico.** El modelo predictivo necesita **13 features** para hacer una predicción. Pero la clase Lectura solo tiene **11**. Las 2 faltantes (age, sex) están en Perfil, que es del backend.

**El flujo actual requiere que el microservicio:**
1. Reciba los datos de Lectura (11 features) desde el Workflow
2. Aparte, consulte el backend vía REST para obtener Perfil.edad y Perfil.sexo
3. Combine todo en un vector de 13 elementos
4. Recién ahí, llame al modelo

**Esto es frágil y lento.** El método `exportarVector()` en Lectura solo puede exportar 11 de las 13 features que el modelo necesita.

**Pregunta:** Si el modelo necesita 13 features, ¿no debería Lectura tener las 13? O bien, ¿debería haber un método `EnsambladorFeatures` que las combine?

### ⚠️ D2: sex es int (0/1) en el CSV, sexo es String en Perfil

**Inconsistencia de tipo.** En el dataset Cleveland, `sex` es 0 (female) o 1 (male). En el UML, `sexo` está tipado como `String`. 

¿Qué valores string se esperan? ¿"M"/"F"? ¿"Masculino"/"Femenino"? Si el modelo fue entrenado con 0/1, convertir a string rompe la predicción.

Si `sexo` se almacena como String en el backend para la UI, el microservicio necesitaría reconvertirlo a 0/1 antes de pasarlo al modelo. Esto es una fuente de errores.

### ⚠️ D3: fbs y exang son Boolean en UML, int (0/1) en CSV

**Menor.** Tanto `fbs` como `exang` en el CSV son enteros 0/1. En el UML son `Boolean`. La conversión es trivial (0→false, 1→true y viceversa), pero `exportarVector()` debe convertir Boolean→Int al construir el vector numérico.

**Riesgo**: Si `exportarVector()` se implementa como "devolver todos los atributos en orden" y un atributo Boolean se serializa como JSON `true`/`false`, el modelo recibirá strings, no números. Debe garantizarse la conversión a 0/1.

### 🔴 D4: target no tiene representación explícita

La variable `target` del CSV (0 = sano, 1 = enfermedad cardíaca) es lo que el modelo PREDICE. En el UML está representada implícitamente por:

| Concepto UML | Equivalente CSV | ¿Correcto? |
|-------------|-----------------|-----------|
| `Prediccion.probabilidad: Float` | Probabilidad de que target=1 | ✅ |
| `Prediccion.clasificacion: String` | "bajo"/"medio"/"alto" → umbral sobre probabilidad | ⚠️ ¿Qué umbrales? |
| `Prediccion.metadataTecnica.recall` | Recall del modelo (métrica clave) | ✅ |

**Problema:** `clasificacion` usa strings semánticos ("bajo", "medio", "alto") pero el dataset original usa target binario (0/1). ¿Cómo se mapea?

- ¿probabilidad < 0.3 → "bajo"?
- ¿0.3 ≤ probabilidad < 0.7 → "medio"?
- ¿probabilidad ≥ 0.7 → "alto"?

Estos umbrales NO están definidos en el diagrama. Son críticos para el triaje: un "alto" dispara alerta, un "bajo" quizás no.

### ⚠️ D5: El orden de `exportarVector()` no está especificado

`exportarVector()` devuelve `List~Float~`. Pero:
1. **¿En qué orden?** El modelo fue entrenado con columnas en el orden del CSV: `age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal`. El vector debe coincidir.
2. **¿Qué pasa con age y sex?** Si Lectura no los tiene, ¿recibe `exportarVector()` parámetros? ¿O se llama a otro método?
3. **¿Se incluye target en el vector?** NO — target es el output, no el input.

---

## 3. Recomendaciones

### R1: Agregar age y sex a Lectura (OPCIÓN FUERTEMENTE RECOMENDADA)

**Cambio:** Añadir dos atributos a la clase Lectura:

```diff
 class Lectura {
     <<microservice>>
     -_id: ObjectId
+    -age: Int
+    -sex: Int       // 0=femenino, 1=masculino (coincide con CSV)
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
```

**Justificación:**
1. `exportarVector()` puede generar el vector COMPLETO de 13 features en el orden correcto
2. Lectura es el feature vector — debe contener TODOS los inputs del modelo
3. El modelo predictivo necesita 13 features, no 11
4. Elimina la necesidad de que el microservicio consulte el backend por Perfil

**Pero entonces age y sex están duplicados (Perfil vs Lectura):**
- **Perfil.edad/sexo**: Para mostrar en el frontend, consulta rápida sin navegar a Evaluacion
- **Lectura.age/sex**: Para el modelo predictivo, snapshot del paciente al momento de la evaluación
- **No es duplicación mala**: Perfil tiene los datos actualizados; Lectura tiene los datos AL MOMENTO DE LA EVALUACIÓN. Si un paciente cumplió años entre evaluaciones, Perfil.edad cambia pero Lectura.age se congela. Esto es correcto para el modelo.

### R2: Cambiar Perfil.sexo a Int (o documentar el mapeo)

**Dos opciones:**

**Opción A** (recomendada): Cambiar `Perfil.sexo: String` a `Perfil.sexo: Int` para coincidir con el CSV. En el frontend se muestra como "Femenino"/"Masculino" pero se almacena como 0/1.

**Opción B**: Mantener String pero documentar el mapeo exacto en la especificación:
```
"F" o "Femenino" → 0
"M" o "Masculino" → 1
```

Y el microservicio debe convertir. Más complejo pero más legible en la API.

### R3: Forzar Boolean→Int en exportarVector()

El método `exportarVector()` DEBE garantizar que `fbs` y `exang` (Boolean en UML) se conviertan a `0` o `1` en el vector numérico, no a `true`/`false`.

Especificación:
```python
def exportarVector(self) -> List[float]:
    return [
        float(self.age),          # 1. age
        float(self.sex),          # 2. sex
        float(self.cp),           # 3. cp
        float(self.trestbps),     # 4. trestbps
        float(self.chol),         # 5. chol
        float(1 if self.fbs else 0),   # 6. fbs (Boolean→0/1)
        float(self.restecg),      # 7. restecg
        float(self.thalach),      # 8. thalach
        float(1 if self.exang else 0), # 9. exang (Boolean→0/1)
        self.oldpeak,             # 10. oldpeak (ya es float)
        float(self.slope),        # 11. slope
        float(self.ca),           # 12. ca
        float(self.thal),         # 13. thal
    ]
```

### R4: Definir umbrales de clasificación

Especificar en la capa de negocio cómo se asigna `Prediccion.clasificacion`:
```
probabilidad < 0.3  → "bajo"
0.3 ≤ probabilidad < 0.7 → "medio"
probabilidad ≥ 0.7 → "alto"
```

(Estos valores son referenciales — deben validarse clínicamente.)

### R5: El orden de exportarVector() es el orden del CSV

El orden debe ser explícitamente:
```
[age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]
```

Que coincide con el orden de las columnas del dataset Cleveland (excluyendo target). Esto garantiza que el vector generado por `exportarVector()` sea directamente consumible por el modelo entrenado.

---

## 4. Diagrama del Flujo de Datos (CSV → Modelo)

```
┌─────────────────────────────────────────────────────────────────────┐
│      FLUJO DE DATOS: DESDE EL DATASET HASTA LA PREDICCIÓN          │
└─────────────────────────────────────────────────────────────────────┘

   DATASET CLEVELAND (entrenamiento)
   ┌──────────────────────────────────────────────────────────────┐
   │  age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang │
   │  oldpeak, slope, ca, thal  ──► modelo ──► target (0/1)      │
   └──────────────────────────────────────────────────────────────┘
                                         │
           MODELO ENTRENADO              │
           ┌─────────────────────────────▼─────────────────────┐
           │  El modelo espera 13 features en ESTE orden:      │
           │  [age, sex, cp, trestbps, chol, fbs, restecg,    │
           │   thalach, exang, oldpeak, slope, ca, thal]      │
           │                                                    │
           │  Y produce: probabilidad (0-1)                     │
           └─────────────────────────────┬─────────────────────┘
                                         │
   SISTEMA EN PRODUCCIÓN                │
   ┌─────────────────────────────────────▼─────────────────────┐
   │                                                           │
   │  1. WearOS envía telemetría                               │
   │  2. Backend la agrega en Evento                           │
   │  3. Workflow dispara Evaluacion                           │
   │                                                           │
   │      ┌──────────────────────────────────────┐             │
   │      │      Microservicio crea:              │             │
   │      │                                      │             │
   │      │  Lectura {                           │             │
   │      │    age: Int         ← desde Perfil   │             │
   │      │    sex: Int         ← desde Perfil   │             │
   │      │    cp: Int          ← desde Evento   │             │
   │      │    trestbps: Int    ← desde Evento   │             │
   │      │    chol: Int        ← desde Evento   │             │
   │      │    fbs: Boolean     ← desde Evento   │             │
   │      │    restecg: Int     ← desde Evento   │             │
   │      │    thalach: Int     ← desde Evento   │             │
   │      │    exang: Boolean   ← desde Evento   │             │
   │      │    oldpeak: Float   ← desde Evento   │             │
   │      │    slope: Int       ← desde Evento   │             │
   │      │    ca: Int          ← desde Evento   │             │
   │      │    thal: Int        ← desde Evento   │             │
   │      │  }                                   │             │
   │      │                                      │             │
   │      │  exportarVector() → [63, 1, 3, 145,  │             │
   │      │    233, 1, 0, 150, 0, 2.3, 0, 0, 1] │             │
   │      │                                      │             │
   │      │         ↓                            │             │
   │      │    MODELO PREDICTIVO                 │             │
   │      │         ↓                            │             │
   │      │    Prediccion {                      │             │
   │      │      probabilidad: 0.85              │             │
   │      │      clasificacion: "alto"           │             │
   │      │    }                                 │             │
   │      └──────────────────────────────────────┘             │
   │                                                           │
   │  4. Si clasificacion == "alto" o "medio" → Triaje        │
   │  5. Si Triaje → Alerta → Médico vía Telegram             │
   │                                                           │
   └───────────────────────────────────────────────────────────┘
```

---

## 5. Resumen de Acciones Requeridas

| # | Acción | Severidad | ¿Rompe algo actual? |
|---|--------|-----------|---------------------|
| **A1** | Agregar `age: Int` y `sex: Int` a la clase `Lectura` | 🔴 Crítica | Sí — cambia la estructura de Lectura |
| **A2** | Decidir: Perfil.sexo ¿String o Int? | 🟡 Media | Depende de la decisión |
| **A3** | Especificar orden exacto de `exportarVector()` | 🔴 Crítica | Sí — sin esto, el vector no sirve |
| **A4** | Definir umbrales de clasificación (bajo/medio/alto) | 🟡 Media | Sin esto, `evaluarUmbrales()` no funciona |
| **A5** | Documentar conversión Boolean→Int en exportarVector() | 🟢 Baja | No — pero previene bugs |

### Conclusión

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   EL DIAGRAMA UML TIENE UN ERROR ESTRUCTURAL:                      │
│                                                                     │
│   Lectura tiene 11 atributos, pero el modelo predictivo necesita   │
│   13 features (age + sex del Cleveland dataset).                   │
│                                                                     │
│   age y sex existen en Perfil (backend), pero Lectura (microservi- │
│   ce) no puede generarlos porque están en el otro módulo.          │
│                                                                     │
│   SOLUCIÓN: Agregar age y sex a Lectura.                           │
│                                                                     │
│   ¿Duplicación? Sí, pero justificada:                              │
│   • Perfil tiene datos DEMOGRÁFICOS (para el frontend)             │
│   • Lectura tiene datos de EVALUACIÓN (para el modelo)             │
│   • Son conceptos diferentes, aunque compartan valores              │
│                                                                     │
│   Después de este cambio, exportarVector() producirá 13 floats     │
│   en el orden exacto que el modelo espera.                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
