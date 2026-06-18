---
title: "Casos clínicos sintéticos de alto riesgo cardiovascular"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['casos_sinteticos', 'alto_riesgo', 'triage', 'evaluacion']
---

# Casos clínicos sintéticos de alto riesgo cardiovascular

## Caso 1: dolor torácico opresivo con síntomas vegetativos

```yaml
synthetic_case: true
edad: 58
sexo: masculino
dolor_toracico: "opresivo, 25 minutos"
irradiacion: "brazo izquierdo y mandíbula"
disnea: true
diaforesis: true
nauseas: true
pas: 160
pad: 95
fc: 112
diabetes: true
tabaquismo: true
```

Respuesta esperada: emergencia. Motivo: dolor torácico compatible con evento cardiovascular hasta demostrar lo contrario.

## Caso 2: presión severa con déficit neurológico

```yaml
synthetic_case: true
edad: 67
pas: 210
pad: 124
cefalea_intensa: true
vision_borrosa: true
debilidad_focal: true
```

Respuesta esperada: emergencia. Motivo: presión severa con síntomas neurológicos.

## Caso 3: palpitaciones con síncope

```yaml
synthetic_case: true
edad: 43
fc_reposo: 158
palpitaciones: true
sincope: true
disnea: true
```

Respuesta esperada: emergencia. Motivo: taquicardia sintomática con síncope y disnea.

## Caso 4: dolor torácico en paciente con stent previo

```yaml
synthetic_case: true
edad: 62
antecedente_coronario: "stent hace 2 años"
dolor_toracico: "presión en reposo"
duracion_min: 15
```

Respuesta esperada: emergencia/urgente alta. Motivo: dolor en reposo con enfermedad coronaria conocida.
## Fuentes clínicas oficiales consultadas
- AHA chest pain guideline: https://professional.heart.org/en/science-news/2021-guideline-for-the-evaluation-and-diagnosis-of-chest-pain
- AHA/ACC ACS 2025: https://professional.heart.org/en/science-news/2025-guideline-for-the-management-of-patients-with-acute-coronary-syndromes
- AHA blood pressure readings: https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings
- MedlinePlus arrhythmia: https://medlineplus.gov/arrhythmia.html
