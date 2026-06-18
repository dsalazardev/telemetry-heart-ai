---
title: "Reglas clínicas de triage y alertas cardiovasculares"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['triage', 'alertas', 'reglas_clinicas', 'n8n', 'langchain']
---

# Reglas clínicas de triage y alertas cardiovasculares

## Objetivo

Convertir síntomas, signos vitales y factores de riesgo en prioridad de respuesta. No son reglas diagnósticas; son reglas de seguridad.

## Emergencia

Dolor torácico actual con disnea, sudoración, náuseas, síncope o irradiación; dolor con ECG anormal; troponina elevada; presión >180 y/o >120 con síntomas neurológicos, dolor, disnea o confusión; FC muy rápida/lenta con síncope, dolor, disnea o confusión; déficit neurológico súbito; disnea en reposo; dolor torácico en paciente con antecedente de infarto/stent/bypass.

## Urgente

Dolor resuelto con múltiples factores de riesgo; palpitaciones persistentes con mareo; presión severa confirmada sin síntomas; disnea nueva de esfuerzo; edema progresivo con ortopnea; angina nueva o en empeoramiento.

## Prioritario

Hipertensión etapa 2 repetida sin síntomas graves; diabetes + colesterol alto + presión elevada; colesterol alto con historia familiar; obesidad + sedentarismo + hipertensión; riesgo modelo alto sin síntomas agudos.

## Seguimiento

Factor de riesgo aislado sin síntomas, consulta educativa o datos incompletos sin alarmas.

## Pseudocódigo

```python
if chest_pain and (dyspnea or diaphoresis or nausea or syncope or radiation):
    urgency = 'emergencia'
elif bp_systolic > 180 or bp_diastolic > 120:
    urgency = 'emergencia' if alarm_symptoms else 'urgente'
elif palpitations and (syncope or chest_pain or dyspnea):
    urgency = 'emergencia'
elif model_risk == 'alto' and no_acute_symptoms:
    urgency = 'prioritario'
else:
    urgency = 'seguimiento'
```
## Fuentes clínicas oficiales consultadas
- AHA chest pain guideline: https://professional.heart.org/en/science-news/2021-guideline-for-the-evaluation-and-diagnosis-of-chest-pain
- AHA/ACC ACS 2025: https://professional.heart.org/en/science-news/2025-guideline-for-the-management-of-patients-with-acute-coronary-syndromes
- AHA blood pressure readings: https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings
- AHA heart rate: https://www.heart.org/en/health-topics/high-blood-pressure/the-facts-about-high-blood-pressure/all-about-heart-rate-pulse
