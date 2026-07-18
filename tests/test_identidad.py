import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.routers import auth, usuarios
from app.schemas.auth import RegistroIn
from app.schemas.llave import IdentidadIn


RESPALDO = {
    "cifrado": "respaldo-cifrado",
    "nonce": "nonce-respaldo",
    "salt": "salt-respaldo",
}


class IdentidadAtomicaTest(unittest.TestCase):
    def test_registro_crea_cuenta_con_respaldo(self):
        datos = RegistroIn(
            usuario="vixxer",
            contrasena="secreto",
            llave_publica="publica",
            llave_firma="firma",
            respaldo=RESPALDO,
        )
        request = MagicMock(headers={}, client=SimpleNamespace(host="127.0.0.1"))

        with (
            patch.object(auth, "permitido", return_value=True),
            patch.object(auth, "generar_codigo", return_value="CODIGO"),
            patch.object(auth, "hashear_password", return_value="hash"),
            patch.object(auth.repo, "buscar_por_usuario", return_value=None),
            patch.object(auth.repo, "buscar_por_codigo", return_value=None),
            patch.object(auth.repo, "crear", return_value={"id": "id", "usuario": "vixxer"}) as crear,
        ):
            auth.register(datos, request)

        crear.assert_called_once_with({
            "usuario": "vixxer",
            "clave_hash": "hash",
            "llave_publica": "publica",
            "llave_firma": "firma",
            "codigo": "CODIGO",
            "respaldo_cifrado": "respaldo-cifrado",
            "respaldo_nonce": "nonce-respaldo",
            "respaldo_salt": "salt-respaldo",
        })

    def test_rotacion_actualiza_identidad_en_una_consulta(self):
        datos = IdentidadIn(
            llave_publica="publica",
            llave_firma="firma",
            respaldo=RESPALDO,
        )

        with patch.object(usuarios.repo, "actualizar", return_value={"id": "id"}) as actualizar:
            respuesta = usuarios.actualizar_identidad(datos, "id")

        self.assertEqual(respuesta, {"ok": True})
        actualizar.assert_called_once_with("id", {
            "llave_publica": "publica",
            "llave_firma": "firma",
            "respaldo_cifrado": "respaldo-cifrado",
            "respaldo_nonce": "nonce-respaldo",
            "respaldo_salt": "salt-respaldo",
        })

    def test_sin_respaldo_actualiza_solo_las_llaves(self):
        datos = IdentidadIn(llave_publica="publica", llave_firma="firma")

        with patch.object(usuarios.repo, "actualizar", return_value={"id": "id"}) as actualizar:
            usuarios.actualizar_identidad(datos, "id")

        actualizar.assert_called_once_with("id", {
            "llave_publica": "publica",
            "llave_firma": "firma",
        })
