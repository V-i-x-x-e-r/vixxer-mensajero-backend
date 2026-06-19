from fastapi import Depends, HTTPException, Header
from app.core.security import leer_token

def usuario_actual(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token")
    user_id = leer_token(authorization.replace("Bearer ", ""))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")
    return user_id     # el resto del endpoint recibe el id del usuario logueado

