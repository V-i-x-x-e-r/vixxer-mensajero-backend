from pydantic import BaseModel


class RespaldoIn(BaseModel):
    cifrado: str
    nonce: str
    salt: str
