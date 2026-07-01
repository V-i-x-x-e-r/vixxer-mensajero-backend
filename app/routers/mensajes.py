from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import usuario_actual
from app.core.validar import es_uuid
from app.core.push import enviar_push
from app.db import mensajes as repo
from app.db import usuarios as usuarios_repo
from app.db import amigos as amigos_repo
from app.db import push as push_repo
from app.sockets.server import sio, esta_en_linea

router = APIRouter(prefix="/mensajes", tags=["mensajes"])


class RelayEntrada(BaseModel):
    remitente_id: str
    destinatario_id: str
    contenido_cifrado: str
    nonce: str


@router.get("/historial/{otro_id}")
def historial(otro_id: str, antes: str = None, yo: str = Depends(usuario_actual)):
    return repo.conversacion(yo, otro_id, antes=antes)


@router.get("/conversaciones")
def conversaciones(yo: str = Depends(usuario_actual)):
    salida = []
    for c in repo.conversaciones(yo):
        u = usuarios_repo.buscar_por_id(c["otro_id"])
        if u:
            salida.append({**c, "usuario": u["usuario"], "avatar_url": u.get("avatar_url")})
    return salida


@router.delete("/conversacion/{otro_id}")
def borrar_conversacion(otro_id: str, yo: str = Depends(usuario_actual)):
    repo.limpiar_conversacion(yo, otro_id)
    return {"ok": True}


@router.post("/relay")
async def relay(datos: RelayEntrada, yo: str = Depends(usuario_actual)):
    remitente_id = datos.remitente_id
    destinatario_id = datos.destinatario_id
    if not es_uuid(remitente_id) or not es_uuid(destinatario_id):
        return {"ok": False, "error": "ids"}
    if destinatario_id not in amigos_repo.ids_amigos(remitente_id):
        return {"ok": False, "error": "no_amigos"}
    if amigos_repo.esta_bloqueado(destinatario_id, remitente_id):
        return {"ok": False, "error": "bloqueado"}
    fila = repo.guardar({
        "remitente_id": remitente_id,
        "destinatario_id": destinatario_id,
        "contenido_cifrado": datos.contenido_cifrado,
        "nonce": datos.nonce,
        "respuesta_a": None,
    })
    await sio.emit("mensaje:recibido", fila, room=destinatario_id)
    if not esta_en_linea(destinatario_id):
        tokens = push_repo.tokens_de(destinatario_id)
        if tokens:
            remitente = usuarios_repo.buscar_por_id(remitente_id)
            nombre = remitente["usuario"] if remitente else "Alguien"
            await enviar_push(tokens, nombre, "Te envió un mensaje", {"de": remitente_id})
    return {"ok": True, "id": fila["id"]}
