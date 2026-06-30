import httpx

URL = "https://exp.host/--/api/v2/push/send"


async def enviar_push(tokens, titulo, cuerpo, datos=None):
    validos = [t for t in tokens if t and t.startswith("ExponentPushToken")]
    if not validos:
        return
    mensajes = [
        {
            "to": token,
            "title": titulo,
            "body": cuerpo,
            "sound": "default",
            "data": datos or {},
        }
        for token in validos
    ]
    try:
        async with httpx.AsyncClient(timeout=10) as cliente:
            await cliente.post(URL, json=mensajes)
    except Exception:
        pass
