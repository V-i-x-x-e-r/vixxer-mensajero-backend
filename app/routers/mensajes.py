from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual
from app.db import mensajes as repo

router = APIRouter(prefix="/mensajes", tags=["mensajes"])


@router.get("/historial/{otro_id}")
def historial(otro_id: str, yo: str = Depends(usuario_actual)):
    return repo.conversacion(yo, otro_id)
