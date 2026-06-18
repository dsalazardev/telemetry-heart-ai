from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def get_services(request: Request):
    return request.app.state.services


def verify_internal_token(
    request: Request,
    authorization: str = Security(api_key_header),
):
    """Verifica que el request provenga del backend o n8n autorizado."""
    expected = f"Bearer {request.app.state.settings.internal_token}"
    if not authorization or authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
