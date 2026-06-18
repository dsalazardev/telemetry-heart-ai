---
title: "README — Corpus clínico cardiovascular para RAG"
version: "1.0"
last_reviewed: "2026-06-17"
language: "es-CO"
clinical_scope: "cardiovascular adulto; académico; RAG clínico"
intended_use: "Contexto clínico estructurado para RAG académico. No sustituye juicio médico ni guías institucionales."
not_for: "Diagnóstico autónomo, prescripción, alta médica o manejo de urgencias sin profesional de salud."
retrieval_tags: ['readme', 'corpus', 'rag']
---


# Corpus clínico cardiovascular para RAG — Telemetry Heart AI

Este paquete contiene documentos Markdown centrados en contenido clínico cardiovascular. Está pensado para alimentar un RAG académico con material recuperable sobre dolor torácico, síndrome coronario agudo, hipertensión, lípidos, diabetes, signos vitales, arritmias, insuficiencia cardiaca, factores de riesgo y variables del dataset UCI Heart Disease.

El objetivo es que el agente explique riesgo y priorización clínica con más rigor. No uses este corpus como guía médica productiva. Para producción real se requiere revisión por médicos, protocolos institucionales, validación clínica, control de versiones y evaluación de seguridad.

## Indexación recomendada

- Chunking por encabezados Markdown.
- Tamaño de chunk sugerido: 700 a 1.200 tokens.
- Overlap: 100 a 180 tokens.
- Conservar metadatos YAML.
- Separar casos sintéticos de documentos normativos mediante metadatos.
- Priorizar tags: dolor_toracico, acs, hipertension, diabetes, lipidos, telemetria, arritmia, uci.

## Formato de respuesta recomendado

1. Prioridad clínica.
2. Razones clínicas explícitas.
3. Variables relevantes.
4. Información faltante.
5. Siguiente paso seguro.
6. Límite: no diagnóstico definitivo.

## Archivos

Incluye 25 documentos `.md` y un manifiesto JSON. Cada documento contiene fuentes oficiales al final.
