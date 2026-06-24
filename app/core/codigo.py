import secrets

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generar_codigo(largo: int = 8) -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(largo))


def normalizar_codigo(codigo: str) -> str:
    return "".join(c for c in codigo.upper() if c in ALFABETO)
