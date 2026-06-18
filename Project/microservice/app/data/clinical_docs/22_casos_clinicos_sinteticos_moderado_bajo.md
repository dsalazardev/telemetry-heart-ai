---
title: "Casos clínicos sintéticos de riesgo moderado y bajo"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['casos_sinteticos', 'riesgo_moderado', 'riesgo_bajo', 'seguimiento']
---

# Casos clínicos sintéticos de riesgo moderado y bajo

## Caso 1: hipertensión etapa 2 sin síntomas

```yaml
synthetic_case: true
edad: 49
pas: 148
pad: 94
sintomas_alarma: false
```

Respuesta esperada: prioritario. Requiere valoración médica, no emergencia automática.

## Caso 2: colesterol alto aislado

```yaml
synthetic_case: true
edad: 36
colesterol_total: 245
dolor_toracico: false
diabetes: false
pas: 118
pad: 76
```

Respuesta esperada: seguimiento/prioritario según antecedentes. Requiere perfil lipídico completo y riesgo global.

## Caso 3: palpitaciones breves sin alarma

```yaml
synthetic_case: true
edad: 28
palpitaciones: "episodios de 5 segundos"
fc_reposo: 78
sincope: false
dolor_toracico: false
disnea: false
cafeina: "alta"
```

Respuesta esperada: seguimiento con advertencias.

## Caso 4: UCI riesgo alto sin síntomas actuales

```yaml
synthetic_case: true
edad: 55
cp: 2
trestbps: 150
chol: 260
fbs: 1
exang: 1
oldpeak: 2.3
sintomas_actuales: false
modelo_riesgo: "alto"
```

Respuesta esperada: prioritario. No emergencia si no hay síntomas agudos, pero sí valoración.
## Fuentes clínicas oficiales consultadas
- CDC heart disease risk factors: https://www.cdc.gov/heart-disease/risk-factors/index.html
- AHA blood pressure readings: https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings
- AHA cholesterol guide: https://www.heart.org/en/health-topics/cholesterol/your-complete-guide-to-understanding-cholesterol-and-lipids
- UCI Heart Disease: https://archive.ics.uci.edu/dataset/45/heart%2Bdisease
