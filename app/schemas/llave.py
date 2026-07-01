from pydantic import BaseModel


class LlaveIn(BaseModel):
    llave_publica: str


class FirmaIn(BaseModel):
    llave_firma: str
