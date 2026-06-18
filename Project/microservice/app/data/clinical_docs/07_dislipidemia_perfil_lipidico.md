---
title: "Dislipidemia y perfil lipídico: LDL, HDL, triglicéridos y riesgo"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['lipidos', 'colesterol', 'ldl', 'hdl', 'trigliceridos', 'riesgo_ascvd']
---

# Dislipidemia y perfil lipídico

## Concepto

El perfil lipídico resume componentes relevantes del riesgo aterosclerótico: colesterol total, LDL, HDL, triglicéridos y, según contexto, no-HDL, ApoB y lipoproteína(a). La dislipidemia no debe tratarse como número aislado; se integra con edad, presión, diabetes, tabaquismo y antecedentes.

## Variables clave

LDL se relaciona con acumulación de colesterol en paredes arteriales. HDL bajo puede asociarse con mayor riesgo, pero no debe simplificarse sin contexto. Triglicéridos altos junto con LDL alto o HDL bajo se asocian con mayor riesgo de depósitos grasos arteriales. Colesterol total es útil, pero menos específico que LDL/no-HDL.

## Para UCI Heart Disease

`chol` representa colesterol sérico en mg/dL. No especifica LDL ni HDL. El modelo no puede inferir calidad del perfil lipídico completo desde `chol`. Una explicación honesta debe decir que colesterol total elevado puede aumentar sospecha de riesgo, pero no reemplaza perfil lipídico completo.

## Señales de mayor riesgo

LDL alto con diabetes, hipertensión, tabaquismo, historia familiar, enfermedad cardiovascular establecida o enfermedad renal. Triglicéridos altos con obesidad abdominal o diabetes.

## Mensaje seguro

El colesterol se interpreta mejor dentro de un cálculo de riesgo cardiovascular y con perfil lipídico completo. Un valor aislado ayuda al modelo, pero no basta para decidir diagnóstico ni tratamiento.
## Fuentes clínicas oficiales consultadas
- AHA cholesterol guide: https://www.heart.org/en/health-topics/cholesterol/your-complete-guide-to-understanding-cholesterol-and-lipids
- AHA LDL HDL TG: https://www.heart.org/en/health-topics/cholesterol/hdl-good-ldl-bad-cholesterol-and-triglycerides
- AHA cholesterol levels: https://www.heart.org/en/health-topics/cholesterol/about-cholesterol/what-your-cholesterol-levels-mean
- AHA ASCVD calculator: https://professional.heart.org/en/guidelines-and-statements/ascvd-risk-calculator
