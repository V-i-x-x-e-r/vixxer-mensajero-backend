import unittest

from fastapi import HTTPException

from app.routers.grupos import validar_cifrados
from app.schemas.grupos import CifradoMiembro


def cifrado(destinatario: str) -> CifradoMiembro:
    return CifradoMiembro(
        destinatario_id=destinatario,
        contenido_cifrado="cifrado",
        nonce="nonce",
    )


class CifradosDeGrupoTest(unittest.TestCase):
    def test_acepta_una_copia_por_miembro(self):
        salida = validar_cifrados(
            [cifrado("a"), cifrado("b")],
            {"a", "b"},
        )

        self.assertEqual({x["destinatario_id"] for x in salida}, {"a", "b"})

    def test_rechaza_un_miembro_faltante(self):
        with self.assertRaises(HTTPException) as error:
            validar_cifrados([cifrado("a")], {"a", "b"})

        self.assertEqual(error.exception.status_code, 409)

    def test_rechaza_destinatarios_duplicados(self):
        with self.assertRaises(HTTPException) as error:
            validar_cifrados(
                [cifrado("a"), cifrado("a")],
                {"a", "b"},
            )

        self.assertEqual(error.exception.status_code, 409)
