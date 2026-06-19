import socketio

from app.core.security import leer_token
from app.db import mensajes as mensajes_repo

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    user_id = leer_token((auth or {}).get("token", ""))
    if user_id is None:
        return False                       # rechaza la conexión: sin token válido, no entra
    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, user_id)     # sala personal: aquí le llegan sus mensajes


@sio.on("mensaje:enviar")
async def mensaje_enviar(sid, data):
    session = await sio.get_session(sid)
    remitente_id = session["user_id"]

    # Guardamos el blob OPACO tal cual llega. El server NUNCA lo descifra ni lo loggea.
    # Entra en camelCase (contrato); guardamos en snake_case (columnas de la tabla).
    fila = mensajes_repo.guardar({
        "remitente_id": remitente_id,
        "destinatario_id": data["destinatarioId"],
        "contenido_cifrado": data["contenidoCifrado"],
        "nonce": data["nonce"],
    })

    # Reenviar al destinatario (su sala personal). Si no está online, queda en la base.
    await sio.emit("mensaje:recibido", fila, room=data["destinatarioId"])
    return {"ok": True, "id": fila["id"]}   # ack para el remitente
