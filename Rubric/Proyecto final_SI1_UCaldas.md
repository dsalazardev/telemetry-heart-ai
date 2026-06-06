**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

## **UNIVERSIDAD DE CALDAS** 

_Facultad de IA e Ingenierías_ Ingeniería de Sistemas y Computación 

**PROPUESTA DE EVALUACIÓN** _Proyecto Integrador — Sistemas Inteligentes 1_ 

_Proyecto Final Progresivo por Niveles  ·  Año académico Junio -2026 LUIS FERNANDO CASTILLO O. – JORGE ALBERTO JARAMILLO G._ 

## **1. Presentación** 

La presente propuesta define la evaluación del Proyecto Integrador de la asignatura Sistemas Inteligentes 1 del programa de Ingeniería de Sistemas y Computación de la Universidad de Caldas, Facultad de Ingenierías y Arquitectura. El proyecto articula tres niveles acumulativos sobre un mismo caso de uso elegido por el grupo: automatización visual con N8n, desarrollo programático de agentes con LangChain y aplicación de una técnica del currículo de Sistemas Inteligentes 1 (búsquedas, juegos, aprendizaje por refuerzo o metaheurísticas). 

El único instrumento de entrega es la plantilla PPTX oficial del proyecto, complementada con los recursos digitales indicados (repositorio Git, videos y JSON del flujo). No existen entregas parciales: el grupo presenta todo en una única sesión de socialización al finalizar el período académico. 

## **2. Escala de Evaluación** 

La nota final es la suma de los puntos obtenidos en cada nivel entregado, con techo en 5.0 (escala UCaldas). El Nivel 1 es obligatorio; los Niveles 2 y 3 son voluntarios y acumulativos. 

|**#**|**Nivel**|**Contenido del Proyecto**|**Rango**|**Máx.**|
|---|---|---|---|---|
|1|Base|Flujo N8n funcional con documentación, video y JSON|0.0 – 3.5|**3.5**|
|2|Intermedio|Mismo caso en LangChain: código, arquitectura y<br>video|3.5 – 4.5|**4.5**|
|3|Avanzado|Técnica SI1 integrada (Búsquedas / Juegos / RL /<br>Metaheurísticas)|+ ≤ 0.5|**5.0**|



## **3. Instrumento de Evaluación: Plantilla PPTX** 

La plantilla PowerPoint es el eje central del proyecto. Contiene 12 diapositivas que el grupo debe diligenciar completamente. Cada cuadro con borde dorado discontinuo es un campo editable; el texto en gris claro son instrucciones que deben reemplazarse por el contenido real del proyecto. 

Página 1 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

|**#**|**Diapositiva**|**Contenido esperado**|**Nivel**|
|---|---|---|---|
|**1**|**Portada**|Título del proyecto, integrantes, docente y período<br>académico.|**Todos**|
|**2**|**Justificación**|Problema identificado, propuesta de solución y<br>relevancia en SI1.|**Todos**|
|**3**|**Introducción**|Contexto, objetivos y arquitectura general del sistema.|**Todos**|
|**4**|**N8n —**<br>**Pipeline**|Trigger, procesamiento, salida, captura del flujo y<br>métricas generales.|**Nivel 1 ≤ 3.5**|
|**5**|**N8n — Paso a**<br>**Paso**|Creación del flujo en 6 pasos documentados con<br>capturas.|**Nivel 1 ≤ 3.5**|
|**6**|**N8n — Video**<br>**+ JSON**|Enlace al video de creación/ejecución y bloque JSON<br>exportado.|**Nivel 1 ≤ 3.5**|
|**7**|**LangChain —**<br>**Arquitectura**|LLM, ChatPromptTemplate, Tools y Chain/Agent<br>documentados.|**Nivel 2 ≤ 4.5**|
|**8**|**LangChain —**<br>**Código y CoT**|Código Python, cadena de pensamiento y<br>persistencia/RAG.|**Nivel 2 ≤ 4.5**|
|**9**|**LangChain —**<br>**Video**|Enlace al video del sistema LangChain en tiempo real.|**Nivel 2 ≤ 4.5**|
|**1**<br>**0**|**Técnica SI1 —**<br>**Diseño**|Justificación y diseño de la estrategia<br>(Búsquedas/Juegos/RL/Meta).|**Nivel 3 = 5.0**|
|**1**<br>**1**|**Técnica SI1 —**<br>**Resultados**|Métricas obtenidas, visualización y análisis crítico.|**Nivel 3 = 5.0**|
|**1**<br>**2**|**Conclusiones**|Hallazgos por nivel, aprendizajes y trabajo futuro.|**Todos**|



**Criterio de completitud:** _Ningún campo debe quedar con el texto de instrucción original. La presentación oral dura 10 minutos de exposición + 5 minutos de demostración en vivo + 5 minutos de preguntas y respuestas individuales._ 

## **4. Dimensiones Generales de Evaluación** 

Las siguientes dimensiones son transversales a todos los niveles y se valoran en la presentación oral y en la revisión de la plantilla: 

|**Dimensión**|**¿Qué se evalúa?**|**Cómo se evidencia**|
|---|---|---|
|Funcionalidad|El sistema hace lo que declara. Se prueba con<br>datos reales del caso.|Demo en vivo + video|
|Documentación técnica|Claridad del código, README, comentarios y<br>diagramas.|Repositorio + PPTX|
|Comprensión conceptual|El grupo entiende cada componente. Verificado<br>en Q&A oral.|Presentación oral -<br>video|
|Justificación de|Por qué se eligió cada herramienta, algoritmo o|README + PPTX|



Página 2 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

|**Dimensión**|**¿Qué se evalúa?**|**Cómo se evidencia**|
|---|---|---|
|decisiones|técnica.||
|Métricas y evidencia|Se reportan métricas cuantitativas apropiadas a<br>cada nivel.|Notebook / PPTX 11|
|Originalidad|El caso de uso es propio, concreto y aporta<br>valor real.|Presentación + Q&A|



## **5. Nivel 1 — N8n (diapositivas 04, 05 y 06)** 

## **5.1 Descripción** 

N8n es una plataforma de automatización de flujos de trabajo de código abierto que permite orquestar servicios, APIs y modelos de IA mediante nodos visuales sin necesidad de programar cada paso. En el contexto de Sistemas Inteligentes 1 facilita la prototipación rápida de soluciones que integren LLM, bases de datos y APIs externas. 

## **5.2 Contenido requerido en la plantilla** 

## **Diapositiva 04 — Descripción del Pipeline** 

- Nodo trigger: tipo (Webhook, Cron, Manual, etc.) y configuración empleada. 

- Nodo(s) de procesamiento: lógica aplicada, llamadas a LLM o APIs, condicionales. 

- Nodo de salida: canal de entrega del resultado (email, Telegram, base de datos, HTTP Response). 

- Captura de pantalla del flujo completo con todos los nodos visibles. 

- Métricas generales: número de nodos activos, tipo de trigger, tiempo promedio de ejecución, tasa de éxito en pruebas. 

## **Diapositiva 05 — Paso a Paso** 

- 6 pasos de creación: acceso a N8n, creación del workflow, configuración del trigger, nodos de procesamiento, salida y activación. 

- Cada paso debe incluir descripción textual y, opcionalmente, captura de pantalla de la configuración. 

## **Diapositiva 06 — Video y JSON** 

- Enlace al video (3–8 min, narrado) mostrando creación y ejecución real. Subir a YouTube o Google Drive. 

- Bloque con el JSON exportado del flujo (N8n → Menú ⋮ → Download → JSON). El archivo debe adjuntarse también en el repositorio Git. 

## **5.3 Rúbrica** 

|**Criterio**|**Descripción**|**Nivel**|**Peso**|
|---|---|---|---|
|Funcionalidad|El workflow ejecuta la tarea sin errores<br>críticos y produce el resultado<br>esperado.|Alto|30 %|
|Diseño del pipeline|Estructura lógica trigger →<br>procesamiento → salida. Nodos N8n<br>apropiados.|Alto|25 %|



Página 3 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

|**Criterio**|**Descripción**|**Nivel**|**Peso**|
|---|---|---|---|
|Manejo de errores|Ramas de error, reintentos o<br>notificaciones ante fallos<br>contemplados.|Medio|20 %|
|Documentación (PPTX 04-06)|Diapositivas completas: capturas,<br>pasos, enlace de video y JSON<br>exportado.|Medio|15 %|
|Calidad de salida|El output es coherente, estructurado y<br>útil para el caso de uso.|Básico|10 %|
|**TOTAL NIVEL 1**||**0.0 – 3.5**|**100 %**|



## **6. Nivel 2 — LangChain (diapositivas 07, 08 y 09)** 

## **6.1 Descripción** 

LangChain es un framework Python para construir aplicaciones con modelos de lenguaje grandes. El grupo reimplementa el mismo caso de uso del Nivel 1 usando LangChain (versión ≥ 0.2), documentando cada componente en la plantilla y grabando un video de funcionamiento. 

## **6.2 Contenido requerido en la plantilla** 

## **Diapositiva 07 — Arquitectura y Componentes** 

- LLM: modelo utilizado, temperatura y parámetros relevantes. 

- ChatPromptTemplate: system message, human template y variables de entrada con ejemplo de código. 

- Tools: herramientas implementadas con justificación de cada una. 

- Chain / Agent: tipo (LLMChain, AgentExecutor, LCEL, etc.) y flujo de razonamiento. 

## **Diapositiva 08 — Código, Cadena de Pensamiento y RAG** 

- Fragmento de código Python representativo de la cadena implementada. 

- Cadena de pensamiento: estrategia usada (Zero-shot CoT, Few-shot, ReAct, etc.) con ejemplo del log. 

- Persistencia y RAG: vector store, documentos indexados y estrategia de retrieval (si aplica). Justificación si no aplica. 

## **Diapositiva 09 — Video** 

- Enlace al video (4–10 min) mostrando el sistema LangChain en ejecución real con narración de cada componente. 

## **6.3 Repositorio Git** 

- Código Python Notebook p con requirements.txt 

- README.md: descripción, diagrama de arquitectura y comparativa N8n vs LangChain. 

- Carpeta /workflow/ con el JSON del flujo N8n del Nivel 1. 

## **6.4 Rúbrica** 

|**Criterio**|**Descripción**|**Nivel**|**Peso**|
|---|---|---|---|
|Equivalencia funcional|Replica o supera las funcionalidades|Alto|25 %|



Página 4 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

|**Criterio**|**Descripción**|**Nivel**|**Peso**|
|---|---|---|---|
||del Nivel 1 sobre el mismo caso.|||
|Componentes LangChain (PPTX<br>07)|ChatPromptTemplate, LLM,<br>Chains/Agents y Tools implementados<br>y documentados.|Alto|25 %|
|Contexto y RAG (PPTX 08)|Cadena de pensamiento, memoria o<br>RAG donde aplique. Justificación si no<br>aplica.|Medio|20 %|
|Calidad del código|Código modular, README con<br>arquitectura, comparativa N8n vs<br>LangChain.|Medio|20 %|
|Video funcionando (PPTX 09)|Video con narración de cada<br>componente y demostración en tiempo<br>real.|Básico|10 %|
|**TOTAL NIVEL 2**<br>**(ACUMULADO)**||**3.5 – 4.5**|**100 %**|



## **7. Nivel 3 — Técnica de Sistemas Inteligentes 1 (diapositivas 10 y 11)** 

## **7.1 Fundamento** 

El tercer nivel conecta la ingeniería de software con los fundamentos teóricos del curso. El grupo integra al pipeline LangChain una técnica del currículo de Sistemas Inteligentes 1 que aporte capacidad de razonamiento, búsqueda o aprendizaje demostrable, y la evalúa con métricas cuantitativas estándar. 

## **7.2 Técnicas aceptadas y métricas** 

|Búsqueda Informada|Heurística admisible documentada,<br>espacio de estados definido,<br>comparativa de eficiencia vs<br>búsqueda ciega.|Nodos<br>explorados,<br>costo del<br>camino, tiempo<br>de ejecución|★★|
|---|---|---|---|
|Búsqueda No<br>Informada|Estructura del espacio de búsqueda<br>definida, implementación correcta<br>del algoritmo, análisis de<br>complejidad.|Nodos<br>explorados,<br>memoria usada,<br>completitud<br>demostrada|★★|
|Juegos / Minimax /<br>Poda α-β|Función de evaluación<br>documentada, profundidad de<br>búsqueda justificada, demostración<br>de decisiones óptimas.|Nodos<br>evaluados,<br>podas<br>realizadas, tasa<br>de victorias|★★★|
|Aprendizaje por<br>Refuerzo|Entorno definido, función de<br>recompensa justificada,<br>entrenamiento con convergencia<br>demostrable.|Recompensa<br>acumulada, tasa<br>de convergencia,<br>episodios|★★★|
|Metaheurísticas|Codificación de solución y función|Calidad de|★★★|



Página 5 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

||objetivo documentadas, parámetros<br>justificados, análisis de<br>convergencia.|solución,<br>generaciones,<br>tiempo de<br>cómputo||
|---|---|---|---|
|Combinación ≥ 2<br>técnicas|Integración coherente con sinergia<br>demostrable y mejora cuantitativa<br>respecto al Nivel 2.|Métricas de cada<br>técnica + delta<br>de mejora|★★★<br>★|
|**TOTAL NIVEL 3 (MÁX.**<br>**ACUMULADO)**|||**5.0**|



## **7.3 Contenido requerido en la plantilla** 

## **Diapositiva 10 — Diseño de la Técnica** 

- Selección justificada: ¿por qué esta técnica es la más adecuada para el caso de uso? 

- Búsqueda Informada: definición de h(n), espacio de estados, condición de meta y algoritmo (A*, Greedy, IDA*, etc.). 

- Búsqueda No Informada: estructura del grafo/árbol, algoritmo elegido (BFS, DFS, IDDFS, UCS, etc.) y análisis de complejidad. 

- Juegos / Minimax / Poda α-β: tipo de juego, función de evaluación, profundidad de búsqueda y algoritmo implementado. 

- Aprendizaje por Refuerzo: entorno (gymnasium / custom), función de recompensa, algoritmo (Q-Learning, DQN, PPO, etc.) y hiperparámetros. 

- Metaheurísticas: codificación de la solución, función objetivo, técnica (AG, PSO, SA, ACO, etc.) y parámetros principales. 

## **Diapositiva 11 — Resultados y Análisis** 

- Métricas cuantitativas (mínimo dos): nodos explorados, costo del camino, recompensa acumulada, tasa de convergencia, calidad de solución, tiempo de cómputo, etc. 

- Visualización: árbol de búsqueda, curva de aprendizaje, convergencia del algoritmo, árbol Minimax u otro gráfico pertinente. 

- Análisis crítico: integración en el pipeline LangChain, mejora cuantificable vs Nivel 2, limitaciones encontradas. 

- Propuesta de mejora futura para la técnica implementada. 

## **7.4 Rúbrica** 

|**Técnica SI1**|**Criterio general**|**Métricas**<br>**esperadas**|
|---|---|---|
|Búsqueda Informada|Heurística admisible documentada,<br>espacio de estados definido,<br>comparativa de eficiencia vs<br>búsqueda ciega.|Nodos<br>explorados,<br>costo del<br>camino, tiempo<br>de ejecución|
|Búsqueda No<br>Informada|Estructura del espacio de búsqueda<br>definida, implementación correcta<br>del algoritmo, análisis de<br>complejidad.|Nodos<br>explorados,<br>memoria usada,<br>completitud<br>demostrada|
|Juegos / Minimax /|Función de evaluación|Nodos|



Página 6 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

|**Técnica SI1**|**Criterio general**|**Métricas**<br>**esperadas**|
|---|---|---|
|Poda α-β|documentada, profundidad de<br>búsqueda justificada, demostración<br>de decisiones óptimas.|evaluados,<br>podas<br>realizadas, tasa<br>de victorias|
|Aprendizaje por<br>Refuerzo|Entorno definido, función de<br>recompensa justificada,<br>entrenamiento con convergencia<br>demostrable.|Recompensa<br>acumulada, tasa<br>de convergencia,<br>episodios|
|Metaheurísticas|Codificación de solución y función<br>objetivo documentadas, parámetros<br>justificados, análisis de<br>convergencia.|Calidad de<br>solución,<br>generaciones,<br>tiempo de<br>cómputo|
|Combinación ≥ 2<br>técnicas|Integración coherente con sinergia<br>demostrable y mejora cuantitativa<br>respecto al Nivel 2.|Métricas de cada<br>técnica + delta<br>de mejora|
|**TOTAL NIVEL 3 (MÁX.**<br>**ACUMULADO)**|||



## **8. Presentación Oral y Demostración** 

La evaluación final se realiza en una única sesión presencial o sincronica de socialización. El formato es: 

|**Momento**|**Descripción**|**Tiempo**|
|---|---|---|
|Presentación|El grupo expone las 12 diapositivas de la plantilla, demostrando<br>en vivo el sistema.|10 min|
|Demostración|Ejecución en tiempo real con un caso de prueba nuevo (no el<br>del video).|5 min|
|Preguntas|El docente formula preguntas técnicas individuales a cada<br>integrante.|5 min|



La comprensión individual es determinante: si un integrante no puede responder preguntas sobre el componente que implementó, la nota del grupo puede reducirse hasta un punto en esa dimensión. 

## **9. Integridad Académica y Uso de IA** 

El uso de herramientas de IA generativa (ChatGPT, Claude, Copilot, etc.) está permitido como apoyo. El grupo debe: 

- Declarar en el README y en la plantilla PPTX qué partes fueron asistidas por IA y de qué forma. 

- Comprender y poder explicar en detalle cualquier fragmento de código entregado durante la Q&A. 

Página 7 / 8 

**Sistemas Inteligentes 1 — Ing. de Sistemas y Computación — Universidad de Caldas  |  Propuesta de Evaluación** 

- No presentar como propio código generado íntegramente sin comprensión ni adaptación al caso real. 

## **10. Cálculo de la Nota Final** 

**Nota Final = N1 + N2 + N3  ≤ Ejemplo A — Solo N8n:** _N1 = 2.8  →  Nota final: 2.8_ **5.0 Ejemplo B — N8n + LangChain:** N1 ∈ [0.0, 3.5]   N2 ∈ [0.0, 1.0]   N3 ∈ [0.0, _N1 = 3.5 + N2 = 0.7  →  Nota final: 4.2_ 0.5] 

**Ejemplo C — Completo (A* + LangChain):** _N1 = 3.5 + N2 = 1.0 + N3 = 0.5  →  5.0_ 

## **11. Referencias** 

- N8n Documentation. https://docs.n8n.io 

- LangChain Python Docs. https://python.langchain.com/docs/ 

- Russell, S. & Norvig, P. (2022). Artificial Intelligence: A Modern Approach, 4.ª ed. Pearson. 

- Hart, P., Nilsson, N. & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. IEEE Trans. Systems Science and Cybernetics, 4(2), 100–107. 

- Sutton, R. & Barto, A. (2018). Reinforcement Learning: An Introduction, 2.ª ed. MIT Press. 

- Goldberg, D. E. (1989). Genetic Algorithms in Search, Optimization, and Machine Learning. Addison-Wesley. 

- Kennedy, J. & Eberhart, R. (1995). Particle Swarm Optimization. Proc. ICNN'95, vol. 4, 1942–1948. 

- DeepMind / OpenAI Gymnasium. https://gymnasium.farama.org 

_Facultad de IA e Ingenieria  ·  Departamento de Sistemas e Informática_ Universidad de Caldas  ·  Manizales  ·  2026 

Página 8 / 8 

