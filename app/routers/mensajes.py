from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual
from app.db import mensajes as repo
from app.db import usuarios as usuarios_repo

router = APIRouter(prefix="/mensajes", tags=["mensajes"])


@router.get("/historial/{otro_id}")
def historial(otro_id: str, yo: str = Depends(usuario_actual)):
    return repo.conversacion(yo, otro_id)


@router.get("/conversaciones")
def conversaciones(yo: str = Depends(usuario_actual)):
    salida = []
    for c in repo.conversaciones(yo):
        u = usuarios_repo.buscar_por_id(c["otro_id"])
        if u:
            salida.append({**c, "usuario": u["usuario"], "avatar_url": u.get("avatar_url")})
    return salida
