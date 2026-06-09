# n8n — Motor de Orquestación de Flujos de Trabajo

## Descripción

Motor de automatización y orquestación de flujos de trabajo que evalúa reglas de negocio, coordina la secuencia de evaluación clínica y actúa como sistema disparador de notificaciones basado en los eventos y alertas generadas por el ecosistema.

## Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| n8n | docker.n8n.io/n8nio/n8n | latest (ctx7-verified) |
| PostgreSQL | Aiven Cloud | remota (misma BD del backend) |
| LLM | OpenAI API | gpt-4o-mini |
| Notificaciones | Telegram Bot API | latest |

## Quick Start

```bash
# 1. Clonar .env.example y configurar credenciales
cp .env.example .env
nano .env

# 2. Generar encryption key para credenciales de n8n
openssl rand -hex 32   # Pegar en N8N_ENCRYPTION_KEY

# 3. Iniciar n8n
docker compose up -d

# 4. Abrir navegador
open http://localhost:5678

# 5. Crear workflows según AGENTS.md
```

## Flujos Implementados

### 1. THA - Asistente LLM (15 nodos)

Recibe mensajes de médicos por Telegram, usa un LLM para interpretar preguntas y generar SQL, ejecuta consultas contra PostgreSQL con filtro `medico_id` obligatorio, y responde al médico.

**Trigger**: Telegram Bot (mensajes entrantes)
**Nodos principales**: Identificar médico → Armar prompt → LLM genera SQL → Ejecutar SQL → Manejo de errores (reintento) → Formatear respuesta → Telegram Reply → Logging

### 2. THA - Schedule Pendientes (7 nodos)

Revisa cada 5 minutos si hay triajes sin atender y notifica al médico por Telegram.

**Trigger**: Schedule (`*/5 * * * *`)
**Nodos principales**: SELECT triajes pendientes → Armar alerta → Telegram → UPDATE flag → Logging

### 3. THA - Webhook Telemetría (5 nodos)

Recibe telemetría desde WearOS (o simulación), la almacena en PostgreSQL y notifica al microservicio.

**Trigger**: Webhook POST `/webhook/telemetria`
**Nodos principales**: INSERT telemetría → INSERT log → HTTP Request al microservicio → Logging

## Variables de Entorno

Ver `.env.example` para la plantilla completa con 23 variables documentadas.

## Registro de telegramChatId

Para que n8n responda a un médico, el médico debe tener su `telegramChatId` registrado en la BD:

```bash
# El médico se autentica en el backend y ejecuta:
curl -X PUT http://localhost:8000/medicos/{id} \
  -H "Authorization: Bearer {JWT}" \
  -H "Content-Type: application/json" \
  -d '{"telegramChatId": "123456789"}'
```

## Arquitectura

n8n se conecta **directamente** a la misma PostgreSQL del backend (Aiven Cloud). No tiene BD separada. Los workflows se ejecutan en contenedor Docker y persisten en volumen `n8n_data`.

## Logging

Cada acción de n8n genera un INSERT en la tabla `logs` de PostgreSQL con `tipoEvento` prefijado `n8n_`.

## Límites

- No calcula riesgo cardiovascular (eso es del microservicio N2/N3)
- No responde a usuarios sin `telegramChatId` registrado
- No permite ver datos de otros médicos (filtro `medico_id` obligatorio)

## Estado de Implementación

### ✅ Completado
- Contenedor n8n `2.23.4` saludable con PostgreSQL Aiven Cloud
- 3 credenciales configuradas (Telegram Bot, PostgreSQL, LLM)
- 3 workflows creados con estructura completa vía API REST
- Workflows exportados a JSON en `workflows/`

### ⚠️ Requiere Webhook URL Pública para Activación
Los workflows contienen triggers Telegram y Webhook que requieren una URL HTTPS pública para registrarse con servicios externos.

**Para desarrollo local:**
```bash
# Instalar ngrok
npm install -g ngrok
# Exponer n8n
ngrok http 5678
# Configurar .env
WEBHOOK_URL=https://<tu-ngrok-id>.ngrok.io/
# Reiniciar y activar
docker compose restart
```

**Para producción:** Configurar `WEBHOOK_URL=https://api.tu-dominio.com/` en `.env`.

## Documentación Completa

Ver `AGENTS.md` para la documentación completa del módulo.
