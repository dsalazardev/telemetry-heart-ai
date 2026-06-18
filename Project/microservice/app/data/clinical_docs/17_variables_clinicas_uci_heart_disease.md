---
title: "Variables clínicas del dataset UCI Heart Disease"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['uci', 'dataset', 'variables_clinicas', 'heart_disease', 'modelo']
---

# Variables clínicas del dataset UCI Heart Disease

## Contexto

UCI Heart Disease contiene 76 atributos en origen, pero los experimentos publicados suelen usar 14. La base Cleveland se ha usado para distinguir presencia de enfermedad cardiaca de ausencia. La etiqueta objetivo se codifica de 0 a 4, y muchos trabajos binarizan 0 como ausencia y 1-4 como presencia.

## Variables frecuentes

| Variable | Significado clínico aproximado | Comentario RAG |
|---|---|---|
| age | Edad | Mayor edad aumenta riesgo basal. |
| sex | Sexo | Riesgo y presentación varían por sexo. |
| cp | Tipo de dolor torácico | Crítica, pero simplificada. |
| trestbps | Presión en reposo | Factor de riesgo y contexto. |
| chol | Colesterol sérico | No separa LDL/HDL. |
| fbs | Glucosa ayunas >120 mg/dL | No diagnostica diabetes formal. |
| restecg | ECG en reposo | Categoría simplificada. |
| thalach | FC máxima alcanzada | Relacionada con prueba de esfuerzo. |
| exang | Angina inducida por ejercicio | Relevante para isquemia de esfuerzo. |
| oldpeak | Depresión ST por ejercicio | Marcador de posible isquemia. |
| slope | Pendiente ST | Apoya interpretación funcional. |
| ca | Vasos mayores por fluoroscopia | Dato anatómico invasivo. |
| thal | Resultado de prueba thal | Variable histórica; cautela. |
| target/num | Presencia de enfermedad | Etiqueta, no diagnóstico por RAG. |

## Advertencia

El dataset no representa todos los pacientes reales, puede tener sesgos históricos y no reemplaza evaluación clínica. Presentarlo como diagnóstico es incorrecto.
## Fuentes clínicas oficiales consultadas
- UCI Heart Disease: https://archive.ics.uci.edu/dataset/45/heart%2Bdisease
- UCI Statlog Heart: https://archive.ics.uci.edu/ml/datasets/statlog%2B%28heart%29
- AHA chest pain guideline: https://professional.heart.org/en/science-news/2021-guideline-for-the-evaluation-and-diagnosis-of-chest-pain
