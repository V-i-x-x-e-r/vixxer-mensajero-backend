import io
import unittest

from app.core.media import (
    LIMITE_BYTES,
    LongitudRequerida,
    MediaDemasiadoGrande,
    MediaInvalida,
    guardar_cifrado,
    leer_longitud,
    validar_cifrado,
)


async def trozos(*valores: bytes):
    for valor in valores:
        yield valor


class LongitudMediaTest(unittest.TestCase):
    def test_acepta_longitud_valida(self):
        self.assertEqual(leer_longitud("128"), 128)

    def test_exige_longitud(self):
        with self.assertRaises(LongitudRequerida):
            leer_longitud(None)

    def test_rechaza_longitud_invalida(self):
        with self.assertRaises(MediaInvalida):
            leer_longitud("seis")

    def test_rechaza_archivo_demasiado_grande(self):
        with self.assertRaises(MediaDemasiadoGrande):
            leer_longitud(str(LIMITE_BYTES + 1))

    def test_valida_limite_y_cabecera_del_formato_heredado(self):
        validar_cifrado(b"VX2CH1contenido")

        with self.assertRaises(MediaInvalida):
            validar_cifrado(b"otro-contenido")

        with self.assertRaises(MediaDemasiadoGrande):
            validar_cifrado(b"VX2CH1" + b"x" * LIMITE_BYTES)


class GuardarMediaTest(unittest.IsolatedAsyncioTestCase):
    async def test_guarda_trozos_sin_materializarlos(self):
        salida = io.BytesIO()
        contenido = b"VX2CH1contenido-cifrado"

        escritos = await guardar_cifrado(
            trozos(contenido[:3], contenido[3:11], contenido[11:]),
            salida,
            len(contenido),
        )

        self.assertEqual(escritos, len(contenido))
        self.assertEqual(salida.getvalue(), contenido)

    async def test_rechaza_cabecera_invalida(self):
        contenido = b"INVALIDOcontenido"

        with self.assertRaises(MediaInvalida):
            await guardar_cifrado(
                trozos(contenido),
                io.BytesIO(),
                len(contenido),
            )

    async def test_rechaza_cuerpo_truncado(self):
        contenido = b"VX2CH1contenido"

        with self.assertRaises(MediaInvalida):
            await guardar_cifrado(
                trozos(contenido[:-1]),
                io.BytesIO(),
                len(contenido),
            )

    async def test_rechaza_mas_bytes_que_los_declarados(self):
        contenido = b"VX2CH1contenido"

        with self.assertRaises(MediaDemasiadoGrande):
            await guardar_cifrado(
                trozos(contenido),
                io.BytesIO(),
                len(contenido) - 1,
            )
