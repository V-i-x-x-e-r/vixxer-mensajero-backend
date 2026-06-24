from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import usuario_actual
from app.core.codigo import normalizar_codigo
from app.db import usuarios as repo

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/buscar")
def buscar(q: str = "", yo: str = Depends(usuario_actual)):
    q = q.strip()
    if len(q) < 1:
        return []
    return repo.buscar(q, yo)


@router.get("/mi-codigo")
def mi_codigo(yo: str = Depends(usuario_actual)):
    user = repo.buscar_por_id(yo)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"codigo": user["codigo"]}


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
