from starlette.types import ASGIApp, Message, Receive, Scope, Send

LIMITE_CUERPO = 96_000_000


async def _responder_413(send: Send):
    await send({
        "type": "http.response.start",
        "status": 413,
        "headers": [(b"content-type", b"application/json")],
    })
    await send({
        "type": "http.response.body",
        "body": b'{"detail":"Cuerpo demasiado grande"}',
    })


def _declarado(scope: Scope) -> int | None:
    for nombre, valor in scope.get("headers", []):
        if nombre == b"content-length":
            try:
                return int(valor)
            except ValueError:
                return None
    return None


class LimiteCuerpo:
    def __init__(self, app: ASGIApp, limite: int = LIMITE_CUERPO):
        self.app = app
        self.limite = limite

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declarado = _declarado(scope)
        if declarado is not None and declarado > self.limite:
            await _responder_413(send)
            return
        leidos = 0
        excedido = False
        iniciado = False

        async def contar() -> Message:
            nonlocal leidos, excedido
            if excedido:
                return {"type": "http.disconnect"}
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                leidos += len(mensaje.get("body", b""))
                if leidos > self.limite:
                    excedido = True
                    return {"type": "http.disconnect"}
            return mensaje

        async def silenciar(mensaje: Message):
            nonlocal iniciado
            if excedido and not iniciado:
                return
            if mensaje["type"] == "http.response.start":
                iniciado = True
            await send(mensaje)

        await self.app(scope, contar, silenciar)
        if excedido and not iniciado:
            await _responder_413(send)
