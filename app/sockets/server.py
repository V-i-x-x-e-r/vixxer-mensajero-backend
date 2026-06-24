import socketio

from app.core.security import leer_token
from app.db import mensajes as mensajes_repo

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    user_id = leer_token((auth or {}).get("token", ""))
    if user_id is None:
        return False
    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, user_id)


@sio.on("mensaje:enviar")
async def mensaje_enviar(sid, data):
    session = await sio.get_session(sid)
    remitente_id = session["user_id"]
    fila = mensajes_repo.guardar({
        "remitente_id": remitente_id,
        "destinatario_id": data["destinatarioId"],
        "contenido_cifrado": data["contenidoCifrado"],
        "nonce": data["nonce"],
    })
    await sio.emit("mensaje:recibido", fila, room=data["destinatarioId"])
    return {"ok": True, "id": fila["id"]}


@sio.on("usuario:escribiendo")
async def usuario_escribiendo(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    await sio.emit(
        "usuario:escribiendo",
        {"de": de, "activo": bool(data.get("activo"))},
        room=data["para"],
    )


@sio.on("mensaje:entregado")
async def mensaje_entregado(sid, data):
    fila = mensajes_repo.marcar_entregado(data["id"])
    if fila:
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.on("mensaje:leido")
async def mensaje_leido(sid, data):
    filas = mensajes_repo.marcar_leido(data.get("ids", []))
    for fila in filas:
        await sio.emit(
            "mensaje:leido",
            {"id": fila["id"], "leido_en": fila["leido_en"]},
            room=fila["remitente_id"],
        )
