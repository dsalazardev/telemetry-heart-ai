import json
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.core.security import verify_token
from app.schemas.dispositivo import TelemetriaCreate, TelemetriaRead
from app.services import telemetria_service

router = APIRouter()

# Global websocket connections map: {paciente_id: [websocket, ...]}
active_connections: Dict[int, List[WebSocket]] = {}


@router.post("", response_model=TelemetriaRead, status_code=201)
async def recibir_telemetria(data: TelemetriaCreate, db: AsyncSession = Depends(get_db)):
    if not telemetria_service.validar_telemetria(data):
        raise HTTPException(status_code=422, detail="Datos de telemetría inválidos")

    dispositivo = await telemetria_service.obtener_dispositivo(db, data.dispositivo_id)
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    telemetria = await telemetria_service.crear_telemetria(db, data)

    # Broadcast a websockets suscritos al paciente del dispositivo
    paciente_id = dispositivo.paciente_id
    if paciente_id in active_connections:
        mensaje = {
            "tipo": "telemetria",
            "fc": telemetria.frecuenciaCardiaca,
            "spo2": telemetria.spo2,
            "timestamp": telemetria.timestamp.isoformat(),
        }
        for ws in active_connections[paciente_id]:
            try:
                await ws.send_text(json.dumps(mensaje))
            except Exception:
                pass

    return telemetria


@router.websocket("/ws/telemetria/{paciente_id}")
async def websocket_telemetria(websocket: WebSocket, paciente_id: int, token: str = Query(...)):
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Token inválido")
        return

    await websocket.accept()

    if paciente_id not in active_connections:
        active_connections[paciente_id] = []
    active_connections[paciente_id].append(websocket)

    try:
        while True:
            # Mantener conexión viva, opcionalmente recibir pings
            data = await websocket.receive_text()
            # Echo o procesar según necesidad
    except WebSocketDisconnect:
        active_connections[paciente_id].remove(websocket)
        if not active_connections[paciente_id]:
            del active_connections[paciente_id]
    except Exception:
        if websocket in active_connections.get(paciente_id, []):
            active_connections[paciente_id].remove(websocket)
