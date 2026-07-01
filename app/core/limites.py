import time
from collections import defaultdict

_ventanas = defaultdict(list)


def permitido(clave: str, maximo: int, ventana: int) -> bool:
    ahora = time.time()
    intentos = [t for t in _ventanas[clave] if ahora - t < ventana]
    intentos.append(ahora)
    _ventanas[clave] = intentos
    return len(intentos) <= maximo
