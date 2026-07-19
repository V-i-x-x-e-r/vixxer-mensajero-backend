from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import usuario_actual
from app.core.codigo import normalizar_codigo
from app.core.push import enviar_push
from app.db import amigos as repo
from app.db import usuarios as usuarios_repo
from app.db import mensajes as mensajes_repo
from app.db import push as push_repo
from app.schemas.amigos import SolicitarIn, AccionIn, BloquearIn
from app.sockets.server import sio, esta_en_linea


async def _avisar(uid: str, evento: str, titulo: str, cuerpo: str, datos: dict):
    await sio.emit(evento, datos, room=uid)
    if not esta_en_linea(uid):
        tokens = push_repo.tokens_de(uid)
        if tokens:
            await enviar_push(tokens, titulo, cuerpo, datos)

router = APIRouter(prefix="/amigos", tags=["amigos"])


@router.post("/solicitar")
async def solicitar(datos: SolicitarIn, yo: str = Depends(usuario_actual)):
    destino = usuarios_repo.buscar_por_codigo(normalizar_codigo(datos.codigo))
    if not destino:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    if destino["id"] == yo:
        raise HTTPException(status_code=400, detail="No puedes agregarte a ti mismo")
    if repo.esta_bloqueado(destino["id"], yo):
        raise HTTPException(status_code=403, detail="No se puede enviar la solicitud")
    if repo.buscar_solicitud(yo, destino["id"]):
        raise HTTPException(status_code=409, detail="Ya existe una solicitud")
    repo.crear_solicitud(yo, destino["id"])
    quien = usuarios_repo.buscar_por_id(yo)
    nombre = quien["usuario"] if quien else "Alguien"
    await _avisar(destino["id"], "amistad:solicitud", nombre, "Te envió una solicitud de amistad", {"solicitud": True})
    return {"ok": True}


@router.get("/solicitudes")
def solicitudes(yo: str = Depends(usuario_actual)):
    pendientes = repo.pendientes(yo)
    usuarios = usuarios_repo.por_ids([s["de_id"] for s in pendientes])
    salida = []
    for s in pendientes:
        u = usuarios.get(s["de_id"])
        if u:
            salida.append({"id": s["id"], "usuario": u["usuario"], "codigo": u.get("codigo")})
    return salida


@router.post("/aceptar")
async def aceptar(datos: AccionIn, yo: str = Depends(usuario_actual)):
    s = repo.solicitud_por_id(datos.id)
    if not s or s["para_id"] != yo:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    repo.actualizar_estado(datos.id, "aceptada")
    quien = usuarios_repo.buscar_por_id(yo)
    nombre = quien["usuario"] if quien else "Alguien"
    await _avisar(s["de_id"], "amistad:aceptada", nombre, "Aceptó tu solicitud de amistad", {"amigo": yo})
    return {"ok": True}


@router.post("/rechazar")
def rechazar(datos: AccionIn, yo: str = Depends(usuario_actual)):
    s = repo.solicitud_por_id(datos.id)
    if not s or s["para_id"] != yo:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    repo.actualizar_estado(datos.id, "rechazada")
    return {"ok": True}


@router.get("")
def lista(yo: str = Depends(usuario_actual)):
    usuarios = usuarios_repo.por_ids(repo.ids_amigos(yo))
    return [
        {"id": u["id"], "usuario": u["usuario"], "llave_publica": u["llave_publica"], "avatar_url": u.get("avatar_url")}
        for u in usuarios.values()
    ]


@router.post("/bloquear")
def bloquear(datos: BloquearIn, yo: str = Depends(usuario_actual)):
    if datos.user_id == yo:
        raise HTTPException(status_code=400, detail="No puedes bloquearte")
    repo.crear_bloqueo(yo, datos.user_id)
    return {"ok": True}


@router.get("/bloqueados")
def bloqueados(yo: str = Depends(usuario_actual)):
    usuarios = usuarios_repo.por_ids(repo.bloqueados_de(yo))
    return [
        {"id": u["id"], "usuario": u["usuario"], "avatar_url": u.get("avatar_url")}
        for u in usuarios.values()
    ]


@router.post("/desbloquear")
def desbloquear(datos: BloquearIn, yo: str = Depends(usuario_actual)):
    repo.quitar_bloqueo(yo, datos.user_id)
    return {"ok": True}


@router.delete("/{otro_id}")
def eliminar(otro_id: str, yo: str = Depends(usuario_actual)):
    repo.eliminar_amistad(yo, otro_id)
    mensajes_repo.limpiar_conversacion(yo, otro_id)
    return {"ok": True}
