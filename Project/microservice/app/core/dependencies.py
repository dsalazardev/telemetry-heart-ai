from fastapi import Request, Header, HTTPException


def get_services(request: Request):
    return request.app.state.services


def verify_internal_token(request: Request, authorization: str = Header(...)):
    """Verifica que el request provenga del backend o n8n autorizado."""
    expected = f"Bearer {request.app.state.settings.internal_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
