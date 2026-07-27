import asyncio
import unittest

from app.core.cuerpo import LimiteCuerpo


def escenario(limite, cabeceras, trozos):
    recibidos = []
    leidos = []

    async def app(scope, receive, send):
        while True:
            mensaje = await receive()
            leidos.append(len(mensaje.get("body", b"")))
            if not mensaje.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    pendientes = list(trozos)

    async def receive():
        cuerpo = pendientes.pop(0) if pendientes else b""
        return {"type": "http.request", "body": cuerpo, "more_body": bool(pendientes)}

    async def send(mensaje):
        recibidos.append(mensaje)

    scope = {"type": "http", "headers": cabeceras}
    asyncio.run(LimiteCuerpo(app, limite)(scope, receive, send))
    return recibidos, leidos


class LimiteCuerpoTest(unittest.TestCase):
    def test_deja_pasar_lo_que_cabe(self):
        recibidos, leidos = escenario(100, [(b"content-length", b"10")], [b"x" * 10])
        self.assertEqual(recibidos[0]["status"], 200)
        self.assertEqual(sum(leidos), 10)

    def test_rechaza_por_content_length_sin_leer_el_cuerpo(self):
        recibidos, leidos = escenario(100, [(b"content-length", b"9999")], [b"x" * 9999])
        self.assertEqual(recibidos[0]["status"], 413)
        self.assertEqual(leidos, [])

    def test_rechaza_cuerpo_troceado_que_miente_en_la_cabecera(self):
        cabeceras = [(b"transfer-encoding", b"chunked")]
        recibidos, _ = escenario(100, cabeceras, [b"x" * 60, b"x" * 60, b"x" * 60])
        self.assertEqual(recibidos[0]["status"], 413)

    def test_rechaza_cuerpo_sin_cabecera_de_longitud(self):
        recibidos, _ = escenario(50, [], [b"x" * 80])
        self.assertEqual(recibidos[0]["status"], 413)

    def test_ignora_content_length_invalido_y_cuenta_los_bytes(self):
        cabeceras = [(b"content-length", b"diez")]
        recibidos, _ = escenario(50, cabeceras, [b"x" * 80])
        self.assertEqual(recibidos[0]["status"], 413)

    def test_no_toca_el_trafico_que_no_es_http(self):
        pasadas = []

        async def app(scope, receive, send):
            pasadas.append(scope["type"])

        async def receive():
            return {"type": "websocket.receive"}

        async def send(mensaje):
            pass

        asyncio.run(LimiteCuerpo(app, 10)({"type": "websocket"}, receive, send))
        self.assertEqual(pasadas, ["websocket"])


if __name__ == "__main__":
    unittest.main()
