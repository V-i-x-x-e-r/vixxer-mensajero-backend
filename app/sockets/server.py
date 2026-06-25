import socketio

from app.core.security import leer_token
from app.db import mensajes as mensajes_repo
from app.db import usuarios as usuarios_repo

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

en_linea = set()


def esta_en_linea(user_id):
    return user_id in en_linea


@sio.event
async def connect(sid, environ, auth):
    user_id = leer_token((auth or {}).get("token", ""))
    if user_id is None:
        return False
    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, user_id)
    en_linea.add(user_id)
    for fila in mensajes_repo.marcar_entregados_de(user_id):
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if user_id:
        en_linea.discard(user_id)
        usuarios_repo.marcar_desconexion(user_id)


@sio.on("mensaje:enviar")
async def mensaje_enviar(sid, data):
    session = await sio.get_session(sid)
    remitente_id = session["user_id"]
    fila = mensajes_repo.guardar({
        "remitente_id": remitente_id,
        "destinatario_id": data["destinatarioId"],
        "contenido_cifrado": data["contenidoCifrado"],
        "nonce": data["nonce"],
        "respuesta_a": data.get("respuestaA"),
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
    session = await sio.get_session(sid)
    lector = usuarios_repo.buscar_por_id(session["user_id"])
    filas = mensajes_repo.marcar_leido(data.get("ids", []))
    if lector and not lector.get("mostrar_acuses", True):
        return
    for fila in filas:
        await sio.emit(
            "mensaje:leido",
            {"id": fila["id"], "leido_en": fila["leido_en"]},
            room=fila["remitente_id"],
        )


@sio.on("mensaje:reaccionar")
async def mensaje_reaccionar(sid, data):
    session = await sio.get_session(sid)
    usuario_id = session["user_id"]
    fila = mensajes_repo.reaccionar(data["id"], usuario_id, data["emoji"])
    if not fila:
        return
    carga = {"id": fila["id"], "reacciones": fila["reacciones"]}
    await sio.emit("mensaje:reaccion", carga, room=fila["remitente_id"])
    await sio.emit("mensaje:reaccion", carga, room=fila["destinatario_id"])
