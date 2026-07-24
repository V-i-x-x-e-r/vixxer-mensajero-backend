import socketio

from app.core.security import leer_token
from app.core.validar import es_uuid
from app.core.limites import permitido
from app.core.asincrono import en_hilo
from app.db import mensajes as mensajes_repo
from app.db import grupos as grupos_repo
from app.db import usuarios as usuarios_repo
from app.db import amigos as amigos_repo
from app.db import push as push_repo
from app.core.push import enviar_push

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

conexiones: dict[str, set[str]] = {}


def esta_en_linea(user_id):
    return bool(conexiones.get(user_id))


@sio.event
async def connect(sid, environ, auth):
    user_id = leer_token((auth or {}).get("token", ""))
    if user_id is None:
        return False
    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, user_id)
    conexiones.setdefault(user_id, set()).add(sid)
    for fila in await en_hilo(mensajes_repo.marcar_entregados_de, user_id):
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return
    sids = conexiones.get(user_id)
    if sids is None:
        return
    sids.discard(sid)
    if not sids:
        conexiones.pop(user_id, None)
        await en_hilo(usuarios_repo.marcar_desconexion, user_id)


@sio.on("mensaje:enviar")
async def mensaje_enviar(sid, data):
    session = await sio.get_session(sid)
    remitente_id = session["user_id"]
    if not permitido(f"msg:{remitente_id}", maximo=60, ventana=60):
        return {"ok": False, "error": "limite"}
    destinatario_id = data.get("destinatarioId")
    if not es_uuid(destinatario_id) or destinatario_id not in await en_hilo(amigos_repo.ids_amigos, remitente_id):
        return {"ok": False, "error": "no_permitido"}
    if await en_hilo(amigos_repo.esta_bloqueado, destinatario_id, remitente_id):
        return {"ok": False, "error": "bloqueado"}
    respuesta_a = data.get("respuestaA")
    fila, creado = await en_hilo(mensajes_repo.guardar, {
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
            tokens = await en_hilo(push_repo.tokens_de, destinatario_id)
            if tokens:
                nombre = await en_hilo(usuarios_repo.nombre_de, remitente_id)
                await enviar_push(tokens, nombre, "Te envió un mensaje", {"de": remitente_id})
    return {"ok": True, "id": fila["id"]}


@sio.on("usuario:escribiendo")
async def usuario_escribiendo(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    para = data.get("para")
    if not es_uuid(para):
        return
    await sio.emit(
        "usuario:escribiendo",
        {"de": de, "activo": bool(data.get("activo"))},
        room=para,
    )


@sio.on("grupo:escribiendo")
async def grupo_escribiendo(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    grupo_id = data.get("grupo")
    if not es_uuid(grupo_id) or not await en_hilo(grupos_repo.es_miembro, grupo_id, de):
        return
    for uid in await en_hilo(grupos_repo.miembros_ids, grupo_id):
        if uid != de:
            await sio.emit(
                "grupo:escribiendo",
                {"grupo": grupo_id, "de": de, "activo": bool(data.get("activo"))},
                room=uid,
            )


@sio.on("mensaje:entregado")
async def mensaje_entregado(sid, data):
    session = await sio.get_session(sid)
    fila = await en_hilo(mensajes_repo.marcar_entregado, data["id"], session["user_id"])
    if fila:
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.on("mensaje:editar")
async def mensaje_editar(sid, data):
    session = await sio.get_session(sid)
    fila = await en_hilo(mensajes_repo.editar, data["id"], session["user_id"], data["contenidoCifrado"], data["nonce"])
    if fila:
        await sio.emit(
            "mensaje:editado",
            {"id": fila["id"], "contenido_cifrado": fila["contenido_cifrado"], "nonce": fila["nonce"]},
            room=fila["destinatario_id"],
        )


@sio.on("mensaje:borrar")
async def mensaje_borrar(sid, data):
    session = await sio.get_session(sid)
    fila = await en_hilo(mensajes_repo.borrar, data["id"], session["user_id"])
    if fila:
        await sio.emit("mensaje:borrado", {"id": fila["id"]}, room=fila["destinatario_id"])


@sio.on("mensaje:leido")
async def mensaje_leido(sid, data):
    session = await sio.get_session(sid)
    lector = await en_hilo(usuarios_repo.buscar_por_id, session["user_id"])
    filas = await en_hilo(mensajes_repo.marcar_leido, data.get("ids", []), session["user_id"])
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
    for fila in await en_hilo(mensajes_repo.marcar_entregados_de, user_id):
        await sio.emit(
            "mensaje:entregado",
            {"id": fila["id"], "entregado_en": fila["entregado_en"]},
            room=fila["remitente_id"],
        )


@sio.on("mensaje:reaccionar")
async def mensaje_reaccionar(sid, data):
    session = await sio.get_session(sid)
    usuario_id = session["user_id"]
    emoji = data.get("emoji")
    if not isinstance(emoji, str) or len(emoji) > 16:
        return
    fila = await en_hilo(mensajes_repo.reaccionar, data.get("id"), usuario_id, emoji)
    if not fila:
        return
    carga = {"id": fila["id"], "reacciones": fila["reacciones"]}
    await sio.emit("mensaje:reaccion", carga, room=fila["remitente_id"])
    await sio.emit("mensaje:reaccion", carga, room=fila["destinatario_id"])


@sio.on("llamada:ofrecer")
async def llamada_ofrecer(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    para = data.get("para")
    if not permitido(f"llamada:{de}", maximo=20, ventana=60):
        return {"ok": False, "error": "limite"}
    if not es_uuid(para) or para not in await en_hilo(amigos_repo.ids_amigos, de):
        return {"ok": False, "error": "no_permitido"}
    if await en_hilo(amigos_repo.esta_bloqueado, para, de):
        return {"ok": False, "error": "bloqueado"}
    remitente = await en_hilo(usuarios_repo.buscar_por_id, de)
    carga = {
        "de": de,
        "usuario": remitente["usuario"] if remitente else "",
        "sdp": data.get("sdp"),
        "video": bool(data.get("video")),
    }
    await sio.emit("llamada:ofrecer", carga, room=para)
    if not esta_en_linea(para):
        tokens = await en_hilo(push_repo.tokens_de, para)
        if tokens:
            nombre = remitente["usuario"] if remitente else "Alguien"
            await enviar_push(tokens, nombre, "Llamada entrante", {"de": de})
        return {"ok": True, "en_linea": False}
    return {"ok": True, "en_linea": True}


@sio.on("llamada:contestar")
async def llamada_contestar(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    para = data.get("para")
    if not es_uuid(para) or para not in await en_hilo(amigos_repo.ids_amigos, de):
        return
    await sio.emit("llamada:contestar", {"de": de, "sdp": data.get("sdp")}, room=para)


@sio.on("llamada:ice")
async def llamada_ice(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    para = data.get("para")
    if not es_uuid(para) or not permitido(f"ice:{de}", maximo=200, ventana=60):
        return
    await sio.emit("llamada:ice", {"de": de, "candidato": data.get("candidato")}, room=para)


@sio.on("llamada:colgar")
async def llamada_colgar(sid, data):
    session = await sio.get_session(sid)
    de = session["user_id"]
    para = data.get("para")
    if not es_uuid(para):
        return
    await sio.emit("llamada:colgar", {"de": de}, room=para)
