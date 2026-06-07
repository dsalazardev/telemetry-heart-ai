from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.models.usuario import Usuario


async def authenticate_user(db: AsyncSession, correo: str, password: str) -> Optional[Usuario]:
    stmt = select(Usuario).where(Usuario.correo == correo, Usuario.activo == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def login_user(db: AsyncSession, correo: str, password: str) -> Optional[dict]:
    user = await authenticate_user(db, correo, password)
    if not user:
        return None
    access_token = create_access_token(data={"sub": str(user.id), "tipo": user.tipo})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(refresh_token: str) -> Optional[dict]:
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    access_token = create_access_token(data={"sub": user_id, "tipo": payload.get("tipo", "unknown")})
    new_refresh = create_refresh_token(data={"sub": user_id})
    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


async def verify_device_token(token: str) -> Optional[int]:
    payload = verify_token(token)
    if not payload or payload.get("type") != "device":
        return None
    return int(payload.get("sub"))
