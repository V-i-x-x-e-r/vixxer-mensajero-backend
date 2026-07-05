from pydantic import BaseModel, Field
from typing import Literal


class CrearGrupo(BaseModel):
    nombre: str = Field(min_length=1, max_length=40)
    miembros: list[str] = Field(default_factory=list)


class RenombrarGrupo(BaseModel):
    nombre: str = Field(min_length=1, max_length=40)


class AvatarGrupo(BaseModel):
    imagen: str = Field(max_length=8_000_000)
    tipo: str | None = Field(default=None, max_length=64)


class MiembrosIn(BaseModel):
    miembros: list[str] = Field(min_length=1)


class RolIn(BaseModel):
    user_id: str
    rol: Literal["admin", "miembro"]


class ReaccionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=16)


class CifradoMiembro(BaseModel):
    destinatario_id: str
    contenido_cifrado: str
    nonce: str


class MensajeGrupo(BaseModel):
    cliente_id: str | None = None
    respuesta_a: str | None = None
    cifrados: list[CifradoMiembro]


class EditarMensajeGrupo(BaseModel):
    cifrados: list[CifradoMiembro] = Field(min_length=1)
