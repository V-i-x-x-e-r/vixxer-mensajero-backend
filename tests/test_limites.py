import unittest
from unittest.mock import patch

from app.core import limites


class LimitesTest(unittest.TestCase):
    def setUp(self):
        limites._ventanas.clear()

    def test_permite_hasta_el_maximo(self):
        for _ in range(3):
            self.assertTrue(limites.permitido("clave", maximo=3, ventana=60))

    def test_bloquea_al_superar_el_maximo(self):
        for _ in range(3):
            limites.permitido("clave", maximo=3, ventana=60)
        self.assertFalse(limites.permitido("clave", maximo=3, ventana=60))

    def test_claves_distintas_no_se_comparten(self):
        for _ in range(3):
            limites.permitido("uno", maximo=3, ventana=60)
        self.assertTrue(limites.permitido("dos", maximo=3, ventana=60))

    def test_la_ventana_expira_los_intentos_viejos(self):
        with patch.object(limites.time, "time", return_value=1000.0):
            for _ in range(3):
                limites.permitido("clave", maximo=3, ventana=60)
            self.assertFalse(limites.permitido("clave", maximo=3, ventana=60))
        with patch.object(limites.time, "time", return_value=1061.0):
            self.assertTrue(limites.permitido("clave", maximo=3, ventana=60))


if __name__ == "__main__":
    unittest.main()
