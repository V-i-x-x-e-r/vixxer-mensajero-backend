import unittest

from app.core.push import mensaje_fcm, separar_tokens


class TestSepararTokens(unittest.TestCase):
    def test_separa_expo_de_fcm(self):
        expo, fcm = separar_tokens([
            "ExponentPushToken[abc]",
            "dGok3n-fcm-crudo:APA91",
            None,
            "",
            "ExponentPushToken[xyz]",
        ])
        self.assertEqual(expo, ["ExponentPushToken[abc]", "ExponentPushToken[xyz]"])
        self.assertEqual(fcm, ["dGok3n-fcm-crudo:APA91"])

    def test_listas_vacias_sin_tokens(self):
        expo, fcm = separar_tokens([])
        self.assertEqual(expo, [])
        self.assertEqual(fcm, [])


class TestMensajeFcm(unittest.TestCase):
    def test_forma_del_mensaje(self):
        m = mensaje_fcm("tok123", "Ana", "Te envió un mensaje", {"de": "u-1"})
        self.assertEqual(m["message"]["token"], "tok123")
        self.assertEqual(m["message"]["notification"], {"title": "Ana", "body": "Te envió un mensaje"})
        self.assertEqual(m["message"]["data"], {"de": "u-1"})
        self.assertEqual(m["message"]["android"], {"priority": "high"})

    def test_datos_se_vuelven_texto(self):
        m = mensaje_fcm("tok", "T", "C", {"solicitud": True, "n": 3})
        self.assertEqual(m["message"]["data"], {"solicitud": "True", "n": "3"})

    def test_sin_datos(self):
        m = mensaje_fcm("tok", "T", "C")
        self.assertEqual(m["message"]["data"], {})


if __name__ == "__main__":
    unittest.main()
