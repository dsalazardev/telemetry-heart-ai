# Sistema Inteligente de Triaje y Predicción Cardiovascular con Telemetría IoT

## Problema

Las enfermedades cardiovasculares representan la principal causa de mortalidad a nivel mundial. El proceso de triaje y evaluación clínica tradicional enfrenta tres barreras críticas:

1. **Saturación Cognitiva y Latencia en el Diagnóstico**: La evaluación manual de un posible infarto requiere correlacionar simultáneamente hasta 13 variables fisiológicas complejas, un análisis cognitivamente exhaustivo y excesivamente lento bajo presión en urgencias.

2. **Sesgo Algorítmico y Riesgo de Falsos Negativos**: Los historiales médicos presentan un fuerte desbalanceo de clases (mayoría de pacientes sanos). Sin técnicas de IA avanzadas, los modelos predictivos se sesgan hacia la clase mayoritaria, disparando los falsos negativos —el escenario más letal en medicina.

3. **Falta de Telemetría y Cuellos de Botella Operativos**: La captura manual de signos vitales genera retrasos. La ausencia de telemetría IoT y triaje inteligente estanca el flujo de pacientes y satura a los especialistas.

## Solución

Ecosistema que captura telemetría pasiva mediante dispositivos vestibles (Wear OS), orquesta flujos de evaluación temprana, utiliza agentes conversacionales con RAG para explicabilidad clínica y ejecuta algoritmos de racionalidad (metaheurísticas) para optimizar el modelo predictivo.

## Módulos del Ecosistema

- [Documentación del Frontend](./frontend/README.md)
- [Documentación del Backend](./backend/README.md)
- [Documentación del Microservicio de IA](./microservice/README.md)
- [Documentación del Motor de Orquestación n8n](./n8n/README.md)
- [Documentación de la Capa Wear OS](./wearos/README.md)
