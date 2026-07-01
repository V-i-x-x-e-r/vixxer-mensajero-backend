from pydantic import BaseModel, Field


class AvatarIn(BaseModel):
    imagen: str = Field(max_length=8_000_000)
    tipo: str | None = Field(default=None, max_length=64)
