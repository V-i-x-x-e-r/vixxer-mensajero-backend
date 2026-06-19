import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def crear_token(usuario_id: str) -> str:
    payload = {
        "sub": usuario_id,                                   # de quién es
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def leer_token(token: str) -> str | None:
    try:
        datos = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return datos["sub"]                                  # el usuario_id
    except JWTError:
        return None                                          # vencido o falsificado

def hashear_password(password: str) -> str:
    # bcrypt solo procesa los primeros 72 bytes; recortamos para evitar errores
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")

def verificar_password(password: str, hash_guardado: str) -> bool:
    pw = password.encode("utf-8")[:72]
    return bcrypt.checkpw(pw, hash_guardado.encode("utf-8"))