from pydantic import BaseModel, Field


class RegistroIn(BaseModel):
    usuario: str = Field(min_length=3, max_length=20)
    contrasena: str = Field(min_length=6, max_length=100)
    llave_publica: str
    llave_firma: str | None = None


class LoginIn(BaseModel):
    usuario: str
    contrasena: str


class CambiarContrasenaIn(BaseModel):
    actual: str
    nueva: str = Field(min_length=6, max_length=100)


class UsuarioOut(BaseModel):
    id: str
    usuario: str
