from pydantic import BaseModel, Field


class MediaIn(BaseModel):
    datos: str = Field(max_length=35_000_000)
