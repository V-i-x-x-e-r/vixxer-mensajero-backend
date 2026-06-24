from pydantic import BaseModel


class PreferenciasIn(BaseModel):
    mostrar_conexion: bool | None = None
    mostrar_acuses: bool | None = None
