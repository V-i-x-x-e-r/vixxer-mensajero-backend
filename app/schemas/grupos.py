from pydantic import BaseModel, Field


class CrearGrupo(BaseModel):
    nombre: str = Field(min_length=1, max_length=40)
    miembros: list[str] = Field(default_factory=list)


class CifradoMiembro(BaseModel):
    destinatario_id: str
    contenido_cifrado: str
    nonce: str


class MensajeGrupo(BaseModel):
    cliente_id: str | None = None
    cifrados: list[CifradoMiembro]
