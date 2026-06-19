import socketio
from app.core.security import leer_token

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

@sio.event
async def connect(sid, environ, auth):
    user_id = leer_token((auth or {}).get("token", ""))
    if user_id is None:
        return False                       # rechaza la conexión: sin token válido, no entra
    await sio.save_session(sid, {"user_id": user_id})