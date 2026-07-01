import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def verificar_firma(mensaje: str, firma_b64: str, llave_firma_b64: str) -> bool:
    if not firma_b64 or not llave_firma_b64:
        return False
    try:
        verificador = Ed25519PublicKey.from_public_bytes(base64.b64decode(llave_firma_b64))
        verificador.verify(base64.b64decode(firma_b64), mensaje.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError):
        return False
