from pydantic import BaseModel


class PushTokenIn(BaseModel):
    token: str
    plataforma: str = None
