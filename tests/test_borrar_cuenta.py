import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.db import usuarios as repo
from app.routers import auth
from app.schemas.auth import BorrarCuentaIn


class BorrarCuentaTest(unittest.TestCase):
    def test_la_baja_exige_la_contrasena_correcta(self):
        with (
            patch.object(auth, "permitido", return_value=True),
            patch.object(auth.repo, "buscar_por_id", return_value={"clave_hash": "hash"}),
            patch.object(auth, "verificar_password", return_value=False),
            patch.object(auth.repo, "borrar_cuenta") as borrar,
        ):
            with self.assertRaises(HTTPException) as caso:
                auth.borrar_cuenta(BorrarCuentaIn(contrasena="mala"), yo="u-1")

        self.assertEqual(400, caso.exception.status_code)
        borrar.assert_not_called()

    def test_la_baja_borra_filas_y_archivos(self):
        with (
            patch.object(auth, "permitido", return_value=True),
            patch.object(auth.repo, "buscar_por_id", return_value={"clave_hash": "hash"}),
            patch.object(auth, "verificar_password", return_value=True),
            patch.object(auth.repo, "borrar_cuenta") as borrar,
            patch.object(auth.repo, "borrar_archivos") as archivos,
        ):
            respuesta = auth.borrar_cuenta(BorrarCuentaIn(contrasena="buena"), yo="u-1")

        self.assertEqual({"ok": True}, respuesta)
        borrar.assert_called_once_with("u-1")
        archivos.assert_called_once_with("u-1")

    def test_la_baja_se_limita_por_intentos(self):
        with (
            patch.object(auth, "permitido", return_value=False),
            patch.object(auth.repo, "borrar_cuenta") as borrar,
        ):
            with self.assertRaises(HTTPException) as caso:
                auth.borrar_cuenta(BorrarCuentaIn(contrasena="x"), yo="u-1")

        self.assertEqual(429, caso.exception.status_code)
        borrar.assert_not_called()

    def test_la_cuenta_se_borra_en_una_sola_transaccion(self):
        with patch.object(repo, "supabase") as sb:
            repo.borrar_cuenta("11111111-2222-3333-4444-555555555555")

        sb.rpc.assert_called_once_with(
            "borrar_cuenta",
            {"p_usuario": "11111111-2222-3333-4444-555555555555"},
        )

    def test_un_id_invalido_no_llega_a_la_base(self):
        with patch.object(repo, "supabase") as sb:
            self.assertFalse(repo.borrar_cuenta("../../etc/passwd"))

        sb.rpc.assert_not_called()

    def test_los_archivos_se_borran_de_los_dos_buckets(self):
        uid = "11111111-2222-3333-4444-555555555555"
        almacen = MagicMock()
        almacen.list.return_value = [{"name": "uno.bin"}, {"name": "dos.bin"}]

        with patch.object(repo, "supabase") as sb:
            sb.storage.from_.return_value = almacen
            repo.borrar_archivos(uid)

        self.assertEqual(
            {"Media", "Avatares"},
            {llamada.args[0] for llamada in sb.storage.from_.call_args_list},
        )
        almacen.remove.assert_called_with([f"{uid}/uno.bin", f"{uid}/dos.bin"])
        self.assertEqual(2, almacen.remove.call_count)

    def test_un_fallo_de_almacenamiento_no_tumba_la_baja(self):
        almacen = MagicMock()
        almacen.list.side_effect = RuntimeError("storage caido")

        with patch.object(repo, "supabase") as sb:
            sb.storage.from_.return_value = almacen
            repo.borrar_archivos("11111111-2222-3333-4444-555555555555")


if __name__ == "__main__":
    unittest.main()
