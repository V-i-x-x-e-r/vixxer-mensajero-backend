import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from postgrest.exceptions import APIError

from app.db import mensajes


class IdempotenciaMensajesTest(unittest.TestCase):
    def test_busca_id_de_cliente_dentro_del_remitente(self):
        consulta = MagicMock()
        consulta.eq.return_value = consulta
        consulta.limit.return_value = consulta
        consulta.execute.return_value = SimpleNamespace(data=[{"id": "mensaje"}])
        tabla = MagicMock()
        tabla.select.return_value = consulta
        falso = MagicMock()
        falso.table.return_value = tabla

        with patch.object(mensajes, "supabase", falso):
            encontrado = mensajes.buscar_por_cliente("remitente", "cliente")

        self.assertEqual(encontrado, {"id": "mensaje"})
        consulta.eq.assert_any_call("remitente_id", "remitente")
        consulta.eq.assert_any_call("cliente_id", "cliente")

    def test_recupera_el_mensaje_si_otra_peticion_gana_la_carrera(self):
        consulta = MagicMock()
        consulta.eq.return_value = consulta
        consulta.limit.return_value = consulta
        consulta.execute.side_effect = [
            SimpleNamespace(data=[]),
            SimpleNamespace(data=[{"id": "existente"}]),
        ]
        insercion = MagicMock()
        insercion.execute.side_effect = APIError({"code": "23505"})
        tabla = MagicMock()
        tabla.select.return_value = consulta
        tabla.insert.return_value = insercion
        falso = MagicMock()
        falso.table.return_value = tabla

        with patch.object(mensajes, "supabase", falso):
            fila, creada = mensajes.guardar({
                "remitente_id": "remitente",
                "cliente_id": "cliente",
            })

        self.assertEqual(fila, {"id": "existente"})
        self.assertFalse(creada)

    def test_no_oculta_otro_error_de_base_de_datos(self):
        consulta = MagicMock()
        consulta.eq.return_value = consulta
        consulta.limit.return_value = consulta
        consulta.execute.return_value = SimpleNamespace(data=[])
        insercion = MagicMock()
        insercion.execute.side_effect = APIError({"code": "42501"})
        tabla = MagicMock()
        tabla.select.return_value = consulta
        tabla.insert.return_value = insercion
        falso = MagicMock()
        falso.table.return_value = tabla

        with patch.object(mensajes, "supabase", falso):
            with self.assertRaises(APIError):
                mensajes.guardar({
                    "remitente_id": "remitente",
                    "cliente_id": "cliente",
                })
