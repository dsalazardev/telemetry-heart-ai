## Context

El diagrama Lucidchart actual (`2547e999-8026-4161-ac86-f46c584d174c`) contiene el modelo de dominio en su versión original pre-refactor, con 12 clases UML. El diagrama Mermaid en `Documents/Diagrama UML.md` ya fue actualizado a la v2.0 con 18 clases. La exploración (`Documents/exploracion-diagrama.md`) documentó 18 discrepancias entre ambos diagramas.

## Goals / Non-Goals

**Goals:**
- El diagrama Lucidchart debe reflejar EXACTAMENTE el mismo contenido que el diagrama Mermaid v2.0
- Todas las clases, atributos, métodos, relaciones, multiplicidades y estereotipos deben coincidir
- El Lucidchart debe ser utilizable como fuente única de verdad visual para agentes autónomos

**Non-Goals:**
- Modificar el diagrama Mermaid local (`Documents/Diagrama UML.md`)
- Generar código de implementación a partir del diagrama
- Agregar nuevas clases o relaciones que no estén en el Mermaid v2.0
- Resolver problemas de diseño del dominio (eso ya se hizo en el refactor archivado)

## Decisions

### D1: Orden de operaciones en Lucid — crear antes de eliminar

Para evitar dependencias rotas en el diagrama, las nuevas clases se crean antes de modificar las relaciones de las existentes.

Orden:
1. Crear clases nuevas: Usuario, Evaluacion, Lectura, Alerta, Evento, Documento
2. Establecer relaciones de las nuevas clases
3. Modificar clases existentes (Paciente, Medico, Perfil, Prediccion, Telemetria)
4. Eliminar relaciones obsoletas
5. Aplicar estereotipos y limpieza visual

**Alternativa considerada**: Eliminar todo y recrear desde cero. Se descarta porque perdería el layout manual del diagrama actual.

### D2: Uso de la API de Lucid MCP para manipulación

Se usan las herramientas disponibles:
- `lucid_add_block` para crear nuevas clases
- `lucid_edit_item` para modificar atributos/métodos de clases existentes
- `lucid_delete_items` para eliminar relaciones y placeholders
- `lucid_fetch` para verificar el estado después de cada paso

El Lucid MCP no soporta estereotipos UML nativamente (<<backend>>, <<microservice>>). Se documenta como limitación y se resuelve agregando el texto del estereotipo en el título del bloque (ej: "Paciente <<backend>>").

### D3: Layout preservado

Se mantienen las coordenadas x,y de las clases existentes donde sea posible. Las nuevas clases se posicionan según la lectura visual del diagrama original, buscando coherencia espacial (backend a la derecha/centro, microservice a la izquierda, interface en medio entre Triaje y Adapter).

### D4: Source of truth para cada cambio

| Cambio | Fuente | Sección |
|--------|--------|---------|
| Atributos de cada clase | `Documents/Diagrama UML.md` | Clase correspondiente |
| Relaciones y multiplicidades | `Documents/Diagrama UML.md` | Relaciones (líneas 263-301) |
| Estereotipos | `Documents/Diagrama UML.md` | Leyenda + clases |
| Orden de operaciones | `Documents/exploracion-diagrama.md` | Sección 5 (comparativa) |

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| Lucid MCP no soporta estereotipos UML | Usar texto inline en el título del bloque (ej: "<<backend>>\\nPaciente"). Documentar limitación. |
| Error al eliminar relación existente (Telemetria→Workflow) rompe el diagrama visualmente | Verificar con `lucid_fetch` antes y después de eliminar. Si falla, recrear manualmente desde la UI de Lucid. |
| Multiplicidades en relaciones no se pueden modificar vía API | Se elimina la línea existente y se crea una nueva con la multiplicidad corregida. |
| Pérdida de layout por posicionamiento incorrecto de nuevas clases | Usar coordenadas basadas en el fetch inicial del diagrama. Verificar visualmente al final. |

## Open Questions

- ¿El MCP de Lucid soporta la creación de líneas de herencia (triángulo vacío) o solo asociaciones dirigidas? Según `lucid_add_line`, usa `endpoint2_style: "Generalization"`.
- ¿El Adapter debe aparecer como clase separada o como implementación directa de Workflow? En el Mermaid aparece como clase independiente con `..|>` — es la representación correcta.
- ¿Las notas de leyenda (BackendNote, MicroNote) del Mermaid deben recrearse en Lucid? Sí, pero como rectángulos de texto, no como clases UML.
