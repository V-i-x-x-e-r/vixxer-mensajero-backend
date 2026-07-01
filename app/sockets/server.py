import socketio

from app.core.security import leer_token
from app.core.validar import es_uuid
from app.db import mensajes as mensajes_repo
from app.db import usuarios as usuarios_repo
from app.db import amigos as amigos_repo
from app.db import push as push_repo
from app.core.push import enviar_push

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
    destinatario_id = data.get("destinatarioId")
    if not es_uuid(destinatario_id) or destinatario_id not in amigos_repo.ids_amigos(remitente_id):
        return {"ok": False, "error": "no_permitido"}
    if amigos_repo.esta_bloqueado(destinatario_id, remitente_id):
        return {"ok": False, "error": "bloqueado"}
    respuesta_a = data.get("respuestaA")
    fila, creado = mensajes_repo.guardar({
        "remitente_id": remitente_id,
        "destinatario_id": destinatario_id,
        "contenido_cifrado": data["contenidoCifrado"],
        "nonce": data["nonce"],
        "respuesta_a": respuesta_a if es_uuid(respuesta_a) else None,
        "cliente_id": data.get("clienteId"),
    })
    if creado:
        await sio.emit("mensaje:recibido", fila, room=destinatario_id)
        if not esta_en_linea(destinatario_id):
            tokens = push_repo.tokens_de(destinatario_id)
            if tokens:
                remitente = usuarios_repo.buscar_por_id(remitente_id)
                nombre = remitente["usuario"] if remitente else "Alguien"
                await enviar_push(tokens, nombre, "Te envió un mensaje", {"de": remitente_id})
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
    session = await sio.get_session(sid)
    fila = mensajes_repo.marcar_entregado(data["id"], session["user_id"])
    if fila:
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.on("mensaje:editar")
async def mensaje_editar(sid, data):
    session = await sio.get_session(sid)
    fila = mensajes_repo.editar(data["id"], session["user_id"], data["contenidoCifrado"], data["nonce"])
    if fila:
        await sio.emit(
            "mensaje:editado",
            {"id": fila["id"], "contenido_cifrado": fila["contenido_cifrado"], "nonce": fila["nonce"]},
            room=fila["destinatario_id"],
        )


@sio.on("mensaje:borrar")
async def mensaje_borrar(sid, data):
    session = await sio.get_session(sid)
    fila = mensajes_repo.borrar(data["id"], session["user_id"])
    if fila:
        await sio.emit("mensaje:borrado", {"id": fila["id"]}, room=fila["destinatario_id"])


@sio.on("mensaje:leido")
async def mensaje_leido(sid, data):
    session = await sio.get_session(sid)
    lector = usuarios_repo.buscar_por_id(session["user_id"])
    filas = mensajes_repo.marcar_leido(data.get("ids", []), session["user_id"])
    if lector and not lector.get("mostrar_acuses", True):
        return
    for fila in filas:
        await sio.emit(
            "mensaje:leido",
            {"id": fila["id"], "leido_en": fila["leido_en"]},
            room=fila["remitente_id"],
        )


@sio.on("entregar:pendientes")
async def entregar_pendientes(sid, data=None):
    session = await sio.get_session(sid)
    user_id = session["user_id"]
    for fila in mensajes_repo.marcar_entregados_de(user_id):
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
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
