import base64
import binascii
import time

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import usuario_actual
from app.core.validar import es_uuid
from app.core.limites import permitido
from app.core.push import enviar_push
from app.db import grupos as repo
from app.db import amigos as amigos_repo
from app.db import push as push_repo
from app.db import usuarios as usuarios_repo
from app.db.supabase import supabase
from app.schemas.grupos import CrearGrupo, RenombrarGrupo, AvatarGrupo, MiembrosIn, RolIn, ReaccionIn, MensajeGrupo, EditarMensajeGrupo, LeidosIn
from app.sockets.server import sio, esta_en_linea

router = APIRouter(prefix="/grupos", tags=["grupos"])


def _solo_admin(grupo_id: str, yo: str):
    if not repo.es_admin(grupo_id, yo):
        raise HTTPException(status_code=403, detail="Solo un admin puede hacer esto")


def _solo_miembro(grupo_id: str, yo: str):
    if not repo.es_miembro(grupo_id, yo):
        raise HTTPException(status_code=403, detail="No eres miembro")


async def _avisar_actualizado(grupo_id: str, extras: list = None):
    destinos = set(repo.miembros_ids(grupo_id)) | set(extras or [])
    for uid in destinos:
        await sio.emit("grupo:actualizado", {"id": grupo_id}, room=uid)


async def _avisar_nuevos(grupo, nuevos: list, quien: str):
    remitente = usuarios_repo.buscar_por_id(quien)
    nombre = remitente["usuario"] if remitente else "Alguien"
    for uid in nuevos:
        await sio.emit("grupo:nuevo", {"id": grupo["id"], "nombre": grupo["nombre"]}, room=uid)
        if not esta_en_linea(uid):
            tokens = push_repo.tokens_de(uid)
            if tokens:
                await enviar_push(tokens, grupo["nombre"], f"{nombre} te agregó al grupo", {"grupo": grupo["id"]})


@router.post("", status_code=201)
async def crear(datos: CrearGrupo, yo: str = Depends(usuario_actual)):
    amigos = set(amigos_repo.ids_amigos(yo))
    miembros = [m for m in datos.miembros if es_uuid(m) and m in amigos and m != yo]
    grupo = repo.crear(datos.nombre.strip(), yo, miembros)
    await _avisar_nuevos(grupo, miembros, yo)
    return grupo


@router.get("")
def mis_grupos(yo: str = Depends(usuario_actual)):
    return repo.grupos_de(yo)


@router.get("/{grupo_id}")
def obtener(grupo_id: str, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    grupo = repo.info(grupo_id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return grupo


@router.patch("/{grupo_id}")
async def renombrar(grupo_id: str, datos: RenombrarGrupo, yo: str = Depends(usuario_actual)):
    _solo_admin(grupo_id, yo)
    repo.actualizar(grupo_id, {"nombre": datos.nombre.strip()})
    await _avisar_actualizado(grupo_id)
    return {"ok": True}


@router.post("/{grupo_id}/avatar")
async def avatar(grupo_id: str, datos: AvatarGrupo, yo: str = Depends(usuario_actual)):
    _solo_admin(grupo_id, yo)
    try:
        crudo = base64.b64decode(datos.imagen, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Imagen inválida")
    path = f"grupos/{grupo_id}-{int(time.time())}.jpg"
    supabase.storage.from_("Avatares").upload(path, crudo, {"content-type": datos.tipo or "image/jpeg"})
    url = supabase.storage.from_("Avatares").get_public_url(path)
    repo.actualizar(grupo_id, {"avatar_url": url})
    await _avisar_actualizado(grupo_id)
    return {"avatar_url": url}


@router.post("/{grupo_id}/miembros")
async def agregar(grupo_id: str, datos: MiembrosIn, yo: str = Depends(usuario_actual)):
    _solo_admin(grupo_id, yo)
    amigos = set(amigos_repo.ids_amigos(yo))
    candidatos = [m for m in datos.miembros if es_uuid(m) and m in amigos]
    nuevos = repo.agregar_miembros(grupo_id, candidatos)
    if nuevos:
        grupo = repo.info(grupo_id)
        await _avisar_nuevos(grupo, nuevos, yo)
        await _avisar_actualizado(grupo_id)
    return {"ok": True, "agregados": len(nuevos)}


@router.delete("/{grupo_id}/miembros/{user_id}")
async def expulsar(grupo_id: str, user_id: str, yo: str = Depends(usuario_actual)):
    _solo_admin(grupo_id, yo)
    grupo = repo.info(grupo_id)
    if not grupo or user_id == grupo["creador_id"]:
        raise HTTPException(status_code=403, detail="No puedes expulsar al creador")
    repo.quitar_miembro(grupo_id, user_id)
    await _avisar_actualizado(grupo_id, extras=[user_id])
    return {"ok": True}


@router.post("/{grupo_id}/rol")
async def rol(grupo_id: str, datos: RolIn, yo: str = Depends(usuario_actual)):
    _solo_admin(grupo_id, yo)
    grupo = repo.info(grupo_id)
    if not grupo or datos.user_id == grupo["creador_id"]:
        raise HTTPException(status_code=403, detail="El creador siempre es admin")
    if not repo.es_miembro(grupo_id, datos.user_id):
        raise HTTPException(status_code=404, detail="No es miembro")
    repo.cambiar_rol(grupo_id, datos.user_id, datos.rol)
    await _avisar_actualizado(grupo_id)
    return {"ok": True}


@router.get("/{grupo_id}/historial")
def historial(grupo_id: str, antes: str = None, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    return repo.historial(grupo_id, yo, antes=antes)


@router.post("/{grupo_id}/salir")
async def salir(grupo_id: str, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    repo.salir(grupo_id, yo)
    await _avisar_actualizado(grupo_id)
    return {"ok": True}


@router.post("/{grupo_id}/mensajes")
async def enviar(grupo_id: str, datos: MensajeGrupo, yo: str = Depends(usuario_actual)):
    if not permitido(f"grupo:{yo}", maximo=120, ventana=60):
        return {"ok": False, "error": "limite"}
    _solo_miembro(grupo_id, yo)
    miembros = set(repo.miembros_ids(grupo_id))
    cifrados = [c.model_dump() for c in datos.cifrados if c.destinatario_id in miembros]
    if not cifrados:
        return {"ok": False, "error": "sin_destinatarios"}
    msg, creado = repo.guardar_mensaje(grupo_id, yo, datos.cliente_id, cifrados, respuesta_a=datos.respuesta_a)
    if creado:
        remitente = usuarios_repo.buscar_por_id(yo)
        nombre = remitente["usuario"] if remitente else "Alguien"
        grupo = repo.info(grupo_id)
        titulo = grupo["nombre"] if grupo else "Grupo"
        por_dest = {c["destinatario_id"]: c for c in cifrados}
        for uid in miembros:
            if uid == yo:
                continue
            cif = por_dest.get(uid)
            if not cif:
                continue
            carga = {
                "id": msg["id"],
                "grupo_id": grupo_id,
                "remitente_id": yo,
                "enviado_en": msg["enviado_en"],
                "respuesta_a": msg.get("respuesta_a"),
                "contenido_cifrado": cif["contenido_cifrado"],
                "nonce": cif["nonce"],
            }
            await sio.emit("grupo:mensaje", carga, room=uid)
            if not esta_en_linea(uid):
                tokens = push_repo.tokens_de(uid)
                if tokens:
                    await enviar_push(tokens, titulo, f"{nombre} envió un mensaje", {"grupo": grupo_id})
    return {"ok": True, "id": msg["id"]}


@router.post("/{grupo_id}/mensajes/leido")
async def marcar_leidos(grupo_id: str, datos: LeidosIn, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    cambios = repo.marcar_leidos(grupo_id, yo, datos.ids)
    if cambios:
        for uid in repo.miembros_ids(grupo_id):
            await sio.emit("grupo:leido", {"grupo_id": grupo_id, "lecturas": cambios}, room=uid)
    return {"ok": True, "marcados": len(cambios)}


@router.post("/{grupo_id}/mensajes/{mensaje_id}/reaccion")
async def reaccionar(grupo_id: str, mensaje_id: str, datos: ReaccionIn, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    msg = repo.mensaje_por_id(mensaje_id)
    if not msg or msg["grupo_id"] != grupo_id:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    fila = repo.reaccionar(mensaje_id, yo, datos.emoji)
    if fila:
        for uid in repo.miembros_ids(grupo_id):
            await sio.emit("grupo:reaccion", {"id": mensaje_id, "grupo_id": grupo_id, "reacciones": fila["reacciones"]}, room=uid)
    return {"ok": True}


@router.delete("/{grupo_id}/mensajes/{mensaje_id}")
async def borrar_mensaje(grupo_id: str, mensaje_id: str, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    fila = repo.borrar_mensaje(mensaje_id, yo)
    if not fila or fila["grupo_id"] != grupo_id:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    for uid in repo.miembros_ids(grupo_id):
        await sio.emit("grupo:borrado", {"id": mensaje_id, "grupo_id": grupo_id}, room=uid)
    return {"ok": True}


@router.put("/{grupo_id}/mensajes/{mensaje_id}")
async def editar_mensaje(grupo_id: str, mensaje_id: str, datos: EditarMensajeGrupo, yo: str = Depends(usuario_actual)):
    _solo_miembro(grupo_id, yo)
    miembros = set(repo.miembros_ids(grupo_id))
    cifrados = [c.model_dump() for c in datos.cifrados if c.destinatario_id in miembros]
    if not cifrados:
        return {"ok": False, "error": "sin_destinatarios"}
    msg = repo.mensaje_por_id(mensaje_id)
    if not msg or msg["grupo_id"] != grupo_id:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    fila = repo.editar_mensaje(mensaje_id, yo, cifrados)
    if not fila:
        raise HTTPException(status_code=403, detail="Solo puedes editar tus mensajes")
    por_dest = {c["destinatario_id"]: c for c in cifrados}
    for uid in miembros:
        cif = por_dest.get(uid)
        if not cif or uid == yo:
            continue
        await sio.emit("grupo:editado", {
            "id": mensaje_id,
            "grupo_id": grupo_id,
            "contenido_cifrado": cif["contenido_cifrado"],
            "nonce": cif["nonce"],
        }, room=uid)
    return {"ok": True}
