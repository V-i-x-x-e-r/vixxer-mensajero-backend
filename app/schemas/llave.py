from pydantic import BaseModel

from app.schemas.respaldo import RespaldoIn


class LlaveIn(BaseModel):
    llave_publica: str


class FirmaIn(BaseModel):
    llave_firma: str


class IdentidadIn(BaseModel):
    llave_publica: str
    llave_firma: str
    respaldo: RespaldoIn | None = None
