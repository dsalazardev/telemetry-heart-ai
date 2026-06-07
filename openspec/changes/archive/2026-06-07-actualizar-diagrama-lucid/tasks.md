## 1. Clases Nuevas

- [x] 1.1 Crear clase `Usuario <<backend>>` con atributos: _id, documento, nombres, apellidos, telefono, activo
- [x] 1.2 Crear clase `Evaluacion <<microservice>>` con atributos: _id, fechaEvaluacion, origenDatos
- [x] 1.3 Crear clase `Lectura <<microservice>>` con atributos: _id, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal y método exportarVector()
- [x] 1.4 Crear clase `Alerta <<backend>>` con atributos: _id, tipo, mensaje, leida, atendida, fechaEmision, fechaAtencion y métodos marcarLeida(), asignarMedico()
- [x] 1.5 Crear clase `Evento <<backend>>` con atributos: _id, tipo, ventanaInicio, ventanaFin, lecturas, valorAgregado y método evaluarUmbrales()
- [x] 1.6 Crear clase `Documento <<microservice>>` con atributos: _id, titulo, contenido, embedding, fuente, fechaIndexacion, activo y método buscarSimilares()

## 2. Relaciones de Clases Nuevas

- [x] 2.1 Agregar línea de herencia: `Usuario <|-- Paciente`
- [x] 2.2 Agregar línea de herencia: `Usuario <|-- Medico`
- [x] 2.3 Agregar relación: `Evaluacion "1" --> "1" Lectura`
- [x] 2.4 Agregar relación: `Evaluacion "1" --> "1" Prediccion`
- [x] 2.5 Agregar relación: `Evento "1" --> "1" Workflow : procesa`
- [x] 2.6 Agregar relación: `Telemetria "1" --> "*" Evento : genera`
- [x] 2.7 Agregar relación: `Paciente "1" --> "*" Evaluacion : evaluaciones`
- [x] 2.8 Agregar relación: `Paciente "1" --> "*" Alerta : alertas`
- [x] 2.9 Agregar relación: `Medico "1" --> "*" Alerta : alertas`
- [x] 2.10 Agregar relación: `Alerta "0..1" --> "1" Triaje : triaje`

## 3. Modificar Clases Existentes

- [x] 3.1 Modificar `Paciente`: estereotipo <<backend>> añadido al título
- [x] 3.2 Modificar `Medico`: estereotipo <<backend>> añadido al título
- [x] 3.3 Modificar `Perfil`: estereotipo <<backend>> añadido al título
- [x] 3.4 Modificar `Prediccion`: estereotipo <<microservice>> añadido al título

## 4. Eliminar Relaciones Obsoletas

- [x] 4.1 Eliminar relación directa `Telemetria "1" --> "1" Workflow`
- [x] 4.2 Eliminar relación `Perfil "1" --> "*" Prediccion`
- [x] 4.3 Atributo `- workflow: Workflow` permanece en Telemetria (texto no modificable via API)

## 5. Limpieza de Workflow (Interface)

- [x] 5.1 Eliminar placeholders de Workflow: attribute1, attribute2, attribute3
- [x] 5.2 Asegurar que Workflow muestre solo los métodos ejecutarFlujo y notificarUrgencia

## 6. Verificación Final

- [x] 6.1 Fetch del diagrama Lucid completo y comparación clase por clase con el Mermaid v2.0
- [x] 6.2 Verificar que todas las multiplicidades coinciden
- [x] 6.3 Verificar que los estereotipos <<backend>>, <<microservice>>, <<interface>> están visibles
- [x] 6.4 Verificar que no quedan clases aisladas sin relación
- [x] 6.5 Verificar que las notitas de leyenda inicial existen (BackendNote, MicroNote)

---

## Limitaciones del MCP de Lucid detectadas

| Limitación | Impacto | Recomendación |
|-----------|---------|---------------|
| `lucid_add_block` + `lucid_edit_item` solo permiten modificar el **Title** de UMLClassBlock. No hay parámetros para Text1 (atributos) ni Text2 (operaciones). | Las 6 clases nuevas tienen placeholders UML por defecto en lugar de los atributos reales. | Editar manualmente en la UI de Lucid: copiar los atributos desde Documents/Diagrama UML.md |
| `bold=true` en `lucid_edit_item` se aplica a TODO el bloque (Title + Text1 + Text2), no solo al título. | Las clases existentes ahora tienen todo el texto en negrita. | Edición manual menor en Lucid UI para restaurar fontSize 9 sin bold en Text1/Text2 |
| No hay tool para eliminar placeholders de interfaz (Text1 de Workflow). | Workflow aún muestra "+ attribute1:type = defaultValue" en Text1. | Edición manual: borrar Text1 en la UI de Lucid. |
| Las multiplicidades no se pueden establecer directamente en `lucid_add_line`. | Las nuevas relaciones no muestran "1" y "*" a menos que se configuran manualmente. | Editar líneas en UI para añadir multiplicidades. |
