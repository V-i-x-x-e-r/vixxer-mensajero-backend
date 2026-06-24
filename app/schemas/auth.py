from pydantic import BaseModel, Field


class RegistroIn(BaseModel):
    usuario: str = Field(min_length=3, max_length=20)
    contrasena: str = Field(min_length=6, max_length=100)
    llave_publica: str


class LoginIn(BaseModel):
    usuario: str
    contrasena: str


class UsuarioOut(BaseModel):
    id: str
    usuario: str
