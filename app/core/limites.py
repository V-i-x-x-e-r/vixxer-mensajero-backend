import threading
import time

_ventanas = {}
_candado = threading.Lock()
_ultima_purga = 0.0
_INTERVALO_PURGA = 60.0
_MAX_CLAVES = 50000


def _purgar(ahora: float):
    global _ultima_purga
    if ahora - _ultima_purga < _INTERVALO_PURGA:
        return
    _ultima_purga = ahora
    muertas = [clave for clave, (expira, _) in _ventanas.items() if expira <= ahora]
    for clave in muertas:
        _ventanas.pop(clave, None)
    if len(_ventanas) > _MAX_CLAVES:
        for clave in sorted(_ventanas, key=lambda k: _ventanas[k][0])[: len(_ventanas) - _MAX_CLAVES]:
            _ventanas.pop(clave, None)


def permitido(clave: str, maximo: int, ventana: int) -> bool:
    ahora = time.time()
    with _candado:
        _purgar(ahora)
        expira, marcas = _ventanas.get(clave, (0.0, []))
        marcas = [t for t in marcas if ahora - t < ventana]
        marcas.append(ahora)
        _ventanas[clave] = (ahora + ventana, marcas)
        return len(marcas) <= maximo
