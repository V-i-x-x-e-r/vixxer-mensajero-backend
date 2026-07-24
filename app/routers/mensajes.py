from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import usuario_actual
from app.core.validar import es_uuid
from app.core.limites import permitido
from app.core.firma import verificar_firma
from app.core.push import enviar_push
from app.core.asincrono import en_hilo
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
    cliente_id: str | None = None
    firma: str | None = None


@router.get("/historial/{otro_id}")
def historial(otro_id: str, antes: str = None, yo: str = Depends(usuario_actual)):
    filas = repo.conversacion(yo, otro_id, antes=antes)
    if otro_id in usuarios_repo.sin_acuses([otro_id]):
        for m in filas:
            if m["remitente_id"] == yo:
                m["leido_en"] = None
    return filas


@router.get("/conversaciones")
def conversaciones(yo: str = Depends(usuario_actual)):
    convs = repo.conversaciones(yo)
    bloqueados = set(amigos_repo.bloqueados_de(yo))
    convs = [c for c in convs if c["otro_id"] not in bloqueados]
    usuarios = usuarios_repo.por_ids([c["otro_id"] for c in convs])
    ocultan_acuses = usuarios_repo.sin_acuses([c["otro_id"] for c in convs])
    salida = []
    for c in convs:
        u = usuarios.get(c["otro_id"])
        if u:
            fila = {**c, "usuario": u["usuario"], "avatar_url": u.get("avatar_url"), "llave_publica": u["llave_publica"]}
            if c["ultimo_remitente_id"] == yo and c["otro_id"] in ocultan_acuses:
                fila["ultimo_leido_en"] = None
            salida.append(fila)
    return salida


@router.delete("/conversacion/{otro_id}")
def borrar_conversacion(otro_id: str, yo: str = Depends(usuario_actual)):
    repo.limpiar_conversacion(yo, otro_id)
    return {"ok": True}


@router.post("/relay")
async def relay(datos: RelayEntrada, yo: str = Depends(usuario_actual)):
    if not permitido(f"relay:{yo}", maximo=60, ventana=60):
        return {"ok": False, "error": "limite"}
    remitente_id = datos.remitente_id
    destinatario_id = datos.destinatario_id
    if not es_uuid(remitente_id) or not es_uuid(destinatario_id):
        return {"ok": False, "error": "ids"}
    if destinatario_id not in await en_hilo(amigos_repo.ids_amigos, remitente_id):
        return {"ok": False, "error": "no_amigos"}
    if await en_hilo(amigos_repo.esta_bloqueado, destinatario_id, remitente_id):
        return {"ok": False, "error": "bloqueado"}
    remitente = await en_hilo(usuarios_repo.buscar_por_id, remitente_id)
    mensaje = f"{remitente_id}|{destinatario_id}|{datos.contenido_cifrado}|{datos.nonce}|{datos.cliente_id or ''}"
    if not remitente or not verificar_firma(mensaje, datos.firma, remitente.get("llave_firma")):
        return {"ok": False, "error": "firma"}
    fila, creado = await en_hilo(repo.guardar, {
        "remitente_id": remitente_id,
        "destinatario_id": destinatario_id,
        "contenido_cifrado": datos.contenido_cifrado,
        "nonce": datos.nonce,
        "respuesta_a": None,
        "cliente_id": datos.cliente_id,
    })
    if creado:
        await sio.emit("mensaje:recibido", fila, room=destinatario_id)
        if not esta_en_linea(destinatario_id):
            tokens = await en_hilo(push_repo.tokens_de, destinatario_id)
            if tokens:
                nombre = remitente["usuario"]
                await enviar_push(tokens, nombre, "Te envió un mensaje", {"de": remitente_id})
    return {"ok": True, "id": fila["id"]}
