from pydantic import BaseModel


class MediaIn(BaseModel):
    datos: str
