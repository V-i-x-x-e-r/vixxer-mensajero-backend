from typing import AsyncIterable, BinaryIO


MAGIA = b"VX2CH1"
LIMITE_BYTES = 70_000_000
LIMITE_BASE64 = ((LIMITE_BYTES + 2) // 3) * 4


class MediaInvalida(Exception):
    pass


class MediaDemasiadoGrande(Exception):
    pass


class LongitudRequerida(Exception):
    pass


def leer_longitud(valor: str | None) -> int:
    if valor is None:
        raise LongitudRequerida()
    try:
        longitud = int(valor)
    except ValueError as error:
        raise MediaInvalida() from error
    if longitud <= len(MAGIA):
        raise MediaInvalida()
    if longitud > LIMITE_BYTES:
        raise MediaDemasiadoGrande()
    return longitud


def validar_cifrado(contenido: bytes):
    if len(contenido) > LIMITE_BYTES:
        raise MediaDemasiadoGrande()
    if len(contenido) <= len(MAGIA) or not contenido.startswith(MAGIA):
        raise MediaInvalida()


async def guardar_cifrado(
    trozos: AsyncIterable[bytes],
    destino: BinaryIO,
    longitud: int,
) -> int:
    escritos = 0
    cabecera = bytearray()
    async for trozo in trozos:
        if not trozo:
            continue
        escritos += len(trozo)
        if escritos > longitud or escritos > LIMITE_BYTES:
            raise MediaDemasiadoGrande()
        faltan = len(MAGIA) - len(cabecera)
        if faltan > 0:
            cabecera.extend(trozo[:faltan])
        destino.write(trozo)
    if escritos != longitud or bytes(cabecera) != MAGIA:
        raise MediaInvalida()
    return escritos
