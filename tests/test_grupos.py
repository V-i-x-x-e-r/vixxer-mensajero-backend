import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.db import grupos
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


class IdempotenciaGrupoTest(unittest.TestCase):
    def test_reintento_completa_cifrados_si_el_mensaje_ya_existe(self):
        previo = {"id": "mensaje"}
        cifrados = [{"destinatario_id": "destino"}]

        with (
            patch.object(grupos, "buscar_mensaje_por_cliente", return_value=previo),
            patch.object(grupos, "guardar_cifrados", return_value={"destino"}) as guardar,
        ):
            mensaje, destinatarios = grupos.guardar_mensaje("grupo", "remitente", "cliente", cifrados)

        self.assertEqual(mensaje, previo)
        self.assertEqual(destinatarios, {"destino"})
        guardar.assert_called_once_with("mensaje", cifrados)

    def test_guarda_solo_las_copias_cifradas_faltantes(self):
        consulta = MagicMock()
        consulta.eq.return_value = consulta
        consulta.execute.return_value = SimpleNamespace(data=[{"destinatario_id": "550e8400-e29b-41d4-a716-446655440000"}])
        tabla = MagicMock()
        tabla.select.return_value = consulta
        falso = MagicMock()
        falso.table.return_value = tabla
        existentes = "550e8400-e29b-41d4-a716-446655440000"
        faltante = "550e8400-e29b-41d4-a716-446655440001"
        cifrados = [
            {"destinatario_id": existentes, "contenido_cifrado": "a", "nonce": "n"},
            {"destinatario_id": faltante, "contenido_cifrado": "b", "nonce": "n"},
        ]

        with patch.object(grupos, "supabase", falso):
            nuevos = grupos.guardar_cifrados("mensaje", cifrados)

        self.assertEqual(nuevos, {faltante})
        tabla.upsert.assert_called_once_with(
            [{
                "mensaje_id": "mensaje",
                "destinatario_id": faltante,
                "contenido_cifrado": "b",
                "nonce": "n",
            }],
            on_conflict="mensaje_id,destinatario_id",
            ignore_duplicates=True,
        )

    def test_rechaza_destinatarios_duplicados(self):
        with self.assertRaises(HTTPException) as error:
            validar_cifrados(
                [cifrado("a"), cifrado("a")],
                {"a", "b"},
            )

        self.assertEqual(error.exception.status_code, 409)
