from pydantic import BaseModel, Field

from app.core.media import LIMITE_BASE64


class MediaIn(BaseModel):
    datos: str = Field(max_length=LIMITE_BASE64)
