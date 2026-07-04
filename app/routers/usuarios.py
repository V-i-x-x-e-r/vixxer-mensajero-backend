import base64
import binascii
import time

from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import usuario_actual
from app.core.codigo import normalizar_codigo
from app.db import usuarios as repo
from app.db import push as push_repo
from app.db.supabase import supabase
from app.schemas.preferencias import PreferenciasIn
from app.schemas.avatar import AvatarIn
from app.schemas.llave import LlaveIn, FirmaIn
from app.schemas.respaldo import RespaldoIn
from app.schemas.push import PushTokenIn
from app.sockets.server import esta_en_linea

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/mi-codigo")
def mi_codigo(yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(yo)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"usuario": user["usuario"], "codigo": user["codigo"], "avatar_url": user.get("avatar_url")}


@router.put("/llave-publica")
def actualizar_llave(datos: LlaveIn, yo: str = Depends(usuario_actual)):
    repo.actualizar(yo, {"llave_publica": datos.llave_publica})
    return {"ok": True}


@router.put("/llave-firma")
def actualizar_llave_firma(datos: FirmaIn, yo: str = Depends(usuario_actual)):
    repo.actualizar(yo, {"llave_firma": datos.llave_firma})
    return {"ok": True}


@router.put("/push-token")
def guardar_push_token(datos: PushTokenIn, yo: str = Depends(usuario_actual)):
    push_repo.guardar(yo, datos.token, datos.plataforma)
    return {"ok": True}


@router.put("/respaldo")
def guardar_respaldo(datos: RespaldoIn, yo: str = Depends(usuario_actual)):
    repo.actualizar(yo, {
        "respaldo_cifrado": datos.cifrado,
        "respaldo_nonce": datos.nonce,
        "respaldo_salt": datos.salt,
    })
    return {"ok": True}


@router.get("/respaldo")
def obtener_respaldo(yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(yo)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "cifrado": user.get("respaldo_cifrado"),
        "nonce": user.get("respaldo_nonce"),
        "salt": user.get("respaldo_salt"),
    }


@router.post("/avatar")
def subir_avatar(datos: AvatarIn, yo: str = Depends(usuario_actual)):
    try:
        crudo = base64.b64decode(datos.imagen, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Imagen inválida")
    path = f"{yo}/{int(time.time())}.jpg"
    supabase.storage.from_("Avatares").upload(path, crudo, {"content-type": datos.tipo or "image/jpeg"})
    url = supabase.storage.from_("Avatares").get_public_url(path)
    repo.actualizar(yo, {"avatar_url": url})
    return {"avatar_url": url}


@router.get("/preferencias")
def obtener_preferencias(yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(yo)
    return {
        "mostrar_conexion": user.get("mostrar_conexion", True),
        "mostrar_acuses": user.get("mostrar_acuses", True),
    }


@router.patch("/preferencias")
def actualizar_preferencias(datos: PreferenciasIn, yo: str = Depends(usuario_actual)):
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    if cambios:
        repo.actualizar(yo, cambios)
    return {"ok": True}


@router.get("/codigo/{codigo}")
def por_codigo(codigo: str, yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_codigo(normalizar_codigo(codigo))
    if not user:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return user


@router.get("/{user_id}/llave-publica")
def llave_publica(user_id: str, yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user["id"], "llave_publica": user["llave_publica"]}


@router.get("/{user_id}/presencia")
def presencia(user_id: str, yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.get("mostrar_conexion", True):
        return {"en_linea": None, "ultima_conexion": None}
    return {"en_linea": esta_en_linea(user_id), "ultima_conexion": user.get("ultima_conexion")}
