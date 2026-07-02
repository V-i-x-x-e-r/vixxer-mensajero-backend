from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import usuario_actual
from app.core.validar import es_uuid
from app.core.limites import permitido
from app.core.push import enviar_push
from app.db import grupos as repo
from app.db import amigos as amigos_repo
from app.db import push as push_repo
from app.db import usuarios as usuarios_repo
from app.schemas.grupos import CrearGrupo, MensajeGrupo
from app.sockets.server import sio, esta_en_linea

router = APIRouter(prefix="/grupos", tags=["grupos"])


@router.post("", status_code=201)
def crear(datos: CrearGrupo, yo: str = Depends(usuario_actual)):
    amigos = set(amigos_repo.ids_amigos(yo))
    miembros = [m for m in datos.miembros if es_uuid(m) and m in amigos and m != yo]
    grupo = repo.crear(datos.nombre.strip(), yo, miembros)
    return grupo


@router.get("")
def mis_grupos(yo: str = Depends(usuario_actual)):
    return repo.grupos_de(yo)


@router.get("/{grupo_id}")
def obtener(grupo_id: str, yo: str = Depends(usuario_actual)):
    if not repo.es_miembro(grupo_id, yo):
        raise HTTPException(status_code=403, detail="No eres miembro")
    grupo = repo.info(grupo_id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return grupo


@router.get("/{grupo_id}/historial")
def historial(grupo_id: str, antes: str = None, yo: str = Depends(usuario_actual)):
    if not repo.es_miembro(grupo_id, yo):
        raise HTTPException(status_code=403, detail="No eres miembro")
    return repo.historial(grupo_id, yo, antes=antes)


@router.post("/{grupo_id}/mensajes")
async def enviar(grupo_id: str, datos: MensajeGrupo, yo: str = Depends(usuario_actual)):
    if not permitido(f"grupo:{yo}", maximo=120, ventana=60):
        return {"ok": False, "error": "limite"}
    if not repo.es_miembro(grupo_id, yo):
        raise HTTPException(status_code=403, detail="No eres miembro")
    miembros = set(repo.miembros_ids(grupo_id))
    cifrados = [c.model_dump() for c in datos.cifrados if c.destinatario_id in miembros]
    if not cifrados:
        return {"ok": False, "error": "sin_destinatarios"}
    msg, creado = repo.guardar_mensaje(grupo_id, yo, datos.cliente_id, cifrados)
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
                "contenido_cifrado": cif["contenido_cifrado"],
                "nonce": cif["nonce"],
            }
            await sio.emit("grupo:mensaje", carga, room=uid)
            if not esta_en_linea(uid):
                tokens = push_repo.tokens_de(uid)
                if tokens:
                    await enviar_push(tokens, titulo, f"{nombre} envió un mensaje", {"grupo": grupo_id})
    return {"ok": True, "id": msg["id"]}
