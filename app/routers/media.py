import base64
import time

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual
from app.db.supabase import supabase
from app.schemas.media import MediaIn

router = APIRouter(prefix="/media", tags=["media"])


@router.post("")
def subir(datos: MediaIn, yo: str = Depends(usuario_actual)):
    crudo = base64.b64decode(datos.datos)
    path = f"{yo}/{int(time.time() * 1000)}.bin"
    supabase.storage.from_("Media").upload(path, crudo, {"content-type": "application/octet-stream"})
    return {"path": path}


@router.get("/url")
def url(path: str, yo: str = Depends(usuario_actual)):
    firmado = supabase.storage.from_("Media").create_signed_url(path, 86400)
    return {"url": firmado.get("signedURL") or firmado.get("signedUrl")}
