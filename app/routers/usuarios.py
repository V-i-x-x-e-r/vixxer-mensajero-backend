from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import usuario_actual
from app.db import usuarios as repo

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/{user_id}/llave-publica")
def llave_publica(user_id: str, yo: str = Depends(usuario_actual)):
    # ruta protegida: A pide la llave pública de B para cifrarle a B
    user = repo.buscar_por_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user["id"], "llave_publica": user["llave_publica"]}
