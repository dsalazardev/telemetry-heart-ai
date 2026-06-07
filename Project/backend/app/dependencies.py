from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.models.usuario import Usuario

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se proporcionó token")
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    stmt = select(Usuario).where(Usuario.id == int(payload.get("sub")))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user


async def get_current_medico(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.tipo != "medico":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol de médico")
    return user


async def get_current_paciente(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.tipo != "paciente":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol de paciente")
    return user
