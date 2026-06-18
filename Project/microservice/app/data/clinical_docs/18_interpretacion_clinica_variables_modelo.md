---
title: "Interpretación clínica de variables del modelo cardiovascular"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['explicabilidad', 'shap', 'variables', 'modelo', 'clinico']
---

# Interpretación clínica de variables del modelo cardiovascular

## Propósito

Convertir variables técnicas del modelo en lenguaje clínico prudente. El objetivo es explicar, no inventar causalidad.

## Jerarquía clínica aproximada

Variables de síntoma/prueba funcional: `cp`, `exang`, `oldpeak`, `slope`, `restecg`, `thalach`. Variables de riesgo basal: `age`, `sex`, `trestbps`, `chol`, `fbs`. Variables anatómicas/históricas: `ca`, `thal`.

## Explicación correcta

"El modelo asigna mayor riesgo porque aparecen variables compatibles con carga isquémica o riesgo aterosclerótico: dolor torácico, angina con ejercicio, depresión ST y colesterol/presión elevados. Esto no confirma arteria tapada ni infarto."

## Variables faltantes

Troponina, ECG actual de 12 derivaciones, LDL/HDL/triglicéridos, tabaquismo, medicación, antecedente familiar, enfermedad renal, síntomas actuales, exploración física, saturación y duración de síntomas.

## Regla de oro

La explicación clínica debe ser más conservadora que la predicción del modelo. Si el modelo da riesgo bajo pero el paciente tiene dolor torácico con alarma, manda la clínica.
## Fuentes clínicas oficiales consultadas
- UCI Heart Disease: https://archive.ics.uci.edu/dataset/45/heart%2Bdisease
- AHA chest pain guideline: https://professional.heart.org/en/science-news/2021-guideline-for-the-evaluation-and-diagnosis-of-chest-pain
- AHA/ACC ACS 2025: https://professional.heart.org/en/science-news/2025-guideline-for-the-management-of-patients-with-acute-coronary-syndromes
