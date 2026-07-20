import base64
import binascii
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.core.media import (
    LongitudRequerida,
    MediaDemasiadoGrande,
    MediaInvalida,
    guardar_cifrado,
    leer_longitud,
)
from app.core.deps import usuario_actual
from app.core.limites import permitido
from app.db.supabase import supabase
from app.db import amigos as amigos_repo
from app.schemas.media import MediaIn

router = APIRouter(prefix="/media", tags=["media"])


@router.post("")
def subir(datos: MediaIn, yo: str = Depends(usuario_actual)):
    validar_frecuencia(yo)
    try:
        crudo = base64.b64decode(datos.datos, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Datos inválidos")
    path = ruta_media(yo)
    supabase.storage.from_("Media").upload(
        path,
        crudo,
        {"content-type": "application/octet-stream"},
    )
    return {"path": path}


@router.post("/archivo")
async def subir_archivo(request: Request, yo: str = Depends(usuario_actual)):
    validar_frecuencia(yo)
    tipo = request.headers.get("content-type", "").split(";", 1)[0]
    if tipo != "application/octet-stream":
        raise HTTPException(status_code=415, detail="Tipo de contenido inválido")
    try:
        longitud = leer_longitud(request.headers.get("content-length"))
    except LongitudRequerida:
        raise HTTPException(status_code=411, detail="Falta Content-Length")
    except MediaDemasiadoGrande:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    except MediaInvalida:
        raise HTTPException(status_code=400, detail="Longitud inválida")

    temporal = NamedTemporaryFile(prefix="vixxer-", suffix=".bin", delete=False)
    temporal_path = Path(temporal.name)
    try:
        with temporal:
            await guardar_cifrado(request.stream(), temporal, longitud)
        path = ruta_media(yo)
        await run_in_threadpool(subir_temporal, path, temporal_path)
        return {"path": path}
    except MediaDemasiadoGrande:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    except MediaInvalida:
        raise HTTPException(status_code=400, detail="Archivo cifrado inválido")
    finally:
        temporal_path.unlink(missing_ok=True)


def ruta_media(usuario_id: str) -> str:
    return f"{usuario_id}/{uuid4().hex}.bin"


def validar_frecuencia(usuario_id: str):
    if not permitido(f"media:{usuario_id}", maximo=10, ventana=60):
        raise HTTPException(status_code=429, detail="Demasiadas subidas")


def subir_temporal(path: str, temporal: Path):
    with temporal.open("rb") as archivo:
        supabase.storage.from_("Media").upload(
            path,
            archivo,
            {"content-type": "application/octet-stream"},
        )


@router.get("/url")
def url(path: str, yo: str = Depends(usuario_actual)):
    dueno = path.split("/")[0]
    if dueno != yo and dueno not in amigos_repo.ids_amigos(yo):
        raise HTTPException(status_code=403, detail="Sin acceso")
    firmado = supabase.storage.from_("Media").create_signed_url(path, 3600)
    return {"url": firmado.get("signedURL") or firmado.get("signedUrl")}
