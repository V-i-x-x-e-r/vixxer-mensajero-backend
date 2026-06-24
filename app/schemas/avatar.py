from pydantic import BaseModel


class AvatarIn(BaseModel):
    imagen: str
    tipo: str | None = None
