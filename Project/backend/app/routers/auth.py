from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.usuario import LoginRequest, TokenResponse
from app.services.auth_service import login_user, refresh_access_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await login_user(db, data.correo, data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: dict):
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token requerido")
    result = await refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return result


@router.post("/logout")
async def logout():
    # Stateless JWT: logout es responsabilidad del cliente de descartar tokens
    return {"detail": "Logout exitoso"}
