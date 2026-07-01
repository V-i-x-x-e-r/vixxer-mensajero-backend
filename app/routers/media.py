import base64
import binascii
import time

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import usuario_actual
from app.db.supabase import supabase
from app.db import amigos as amigos_repo
from app.schemas.media import MediaIn

router = APIRouter(prefix="/media", tags=["media"])


@router.post("")
def subir(datos: MediaIn, yo: str = Depends(usuario_actual)):
    try:
        crudo = base64.b64decode(datos.datos, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Datos inválidos")
    path = f"{yo}/{int(time.time() * 1000)}.bin"
    supabase.storage.from_("Media").upload(path, crudo, {"content-type": "application/octet-stream"})
    return {"path": path}


@router.get("/url")
def url(path: str, yo: str = Depends(usuario_actual)):
    dueno = path.split("/")[0]
    if dueno != yo and dueno not in amigos_repo.ids_amigos(yo):
        raise HTTPException(status_code=403, detail="Sin acceso")
    firmado = supabase.storage.from_("Media").create_signed_url(path, 86400)
    return {"url": firmado.get("signedURL") or firmado.get("signedUrl")}
