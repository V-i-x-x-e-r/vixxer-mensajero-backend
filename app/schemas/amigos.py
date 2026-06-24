from pydantic import BaseModel


class SolicitarIn(BaseModel):
    codigo: str


class AccionIn(BaseModel):
    id: str


class BloquearIn(BaseModel):
    user_id: str
