import unittest

from app.core.firma import mensaje_canonico


class FirmaRelayTest(unittest.TestCase):
    def test_mantiene_el_formato_anterior_sin_respuesta(self):
        mensaje = mensaje_canonico("remitente", "destinatario", "cifrado", "nonce", "cliente")

        self.assertEqual(mensaje, "remitente|destinatario|cifrado|nonce|cliente")

    def test_incluye_la_respuesta_en_la_firma(self):
        mensaje = mensaje_canonico(
            "remitente",
            "destinatario",
            "cifrado",
            "nonce",
            "cliente",
            "550e8400-e29b-41d4-a716-446655440000",
        )

        self.assertEqual(
            mensaje,
            "remitente|destinatario|cifrado|nonce|cliente|550e8400-e29b-41d4-a716-446655440000",
        )
