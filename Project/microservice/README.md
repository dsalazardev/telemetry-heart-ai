# Microservicio de IA — Capa de Inteligencia Artificial

## Responsabilidad Arquitectónica

Capa aislada de inteligencia artificial que aloja el modelo predictivo de riesgo cardiovascular, los algoritmos de racionalidad (metaheurísticas) para optimización del modelo, y el agente conversacional basado en RAG para proporcionar explicabilidad clínica de las predicciones.

## Alcance Funcional

- Ejecución del modelo predictivo para clasificación de riesgo cardiovascular basado en las variables fisiológicas del paciente.
- Implementación de algoritmos de racionalidad y metaheurísticas para balanceo de clases, selección de características y optimización de hiperparámetros.
- Agente conversacional con capacidades de Retrieval-Augmented Generation (RAG) que proporciona explicaciones clínicas comprensibles sobre cada predicción.
- Exposición de APIs específicas para consumo de predicciones y consultas al agente conversacional.
- Entrenamiento, validación y versionado del modelo predictivo.

## Límites del Módulo

- No gestiona persistencia de datos de pacientes; consume datos a través de la API central.
- No interactúa directamente con dispositivos IoT ni con el usuario final.
- No ejecuta reglas de negocio ni orquestación de flujos clínicos.
