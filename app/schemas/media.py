from pydantic import BaseModel, Field


class MediaIn(BaseModel):
    datos: str = Field(max_length=95_000_000)
