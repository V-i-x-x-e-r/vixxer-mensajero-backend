import json
import os
import time

import httpx
from jose import jwt

URL_EXPO = "https://exp.host/--/api/v2/push/send"
URL_OAUTH = "https://oauth2.googleapis.com/token"
ALCANCE_FCM = "https://www.googleapis.com/auth/firebase.messaging"

_acceso = {"token": None, "expira": 0.0}


def separar_tokens(tokens):
    expo = [t for t in tokens if t and t.startswith("ExponentPushToken")]
    fcm = [t for t in tokens if t and not t.startswith("ExponentPushToken")]
    return expo, fcm


def mensaje_fcm(token, titulo, cuerpo, datos=None):
    return {
        "message": {
            "token": token,
            "notification": {"title": titulo, "body": cuerpo},
            "data": {clave: str(valor) for clave, valor in (datos or {}).items()},
            "android": {"priority": "high"},
        }
    }


def _credenciales():
    crudo = os.getenv("FIREBASE_CREDENCIALES")
    if not crudo:
        return None
    try:
        return json.loads(crudo)
    except Exception:
        return None


async def _token_acceso(cliente, credenciales):
    ahora = time.time()
    if _acceso["token"] and ahora < _acceso["expira"] - 60:
        return _acceso["token"]
    firmado = jwt.encode(
        {
            "iss": credenciales["client_email"],
            "scope": ALCANCE_FCM,
            "aud": URL_OAUTH,
            "iat": int(ahora),
            "exp": int(ahora) + 3600,
        },
        credenciales["private_key"],
        algorithm="RS256",
    )
    r = await cliente.post(URL_OAUTH, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": firmado,
    })
    datos = r.json()
    _acceso["token"] = datos.get("access_token")
    _acceso["expira"] = ahora + float(datos.get("expires_in", 3600))
    return _acceso["token"]


async def _enviar_expo(cliente, tokens, titulo, cuerpo, datos):
    mensajes = [
        {
            "to": token,
            "title": titulo,
            "body": cuerpo,
            "sound": "default",
            "data": datos or {},
        }
        for token in tokens
    ]
    await cliente.post(URL_EXPO, json=mensajes)


async def _enviar_fcm(cliente, tokens, titulo, cuerpo, datos):
    credenciales = _credenciales()
    if not credenciales:
        return
    acceso = await _token_acceso(cliente, credenciales)
    if not acceso:
        return
    url = f"https://fcm.googleapis.com/v1/projects/{credenciales['project_id']}/messages:send"
    for token in tokens:
        try:
            await cliente.post(
                url,
                json=mensaje_fcm(token, titulo, cuerpo, datos),
                headers={"Authorization": f"Bearer {acceso}"},
            )
        except Exception:
            pass


async def enviar_push(tokens, titulo, cuerpo, datos=None):
    expo, fcm = separar_tokens(tokens)
    if not expo and not fcm:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as cliente:
            if expo:
                await _enviar_expo(cliente, expo, titulo, cuerpo, datos)
            if fcm:
                await _enviar_fcm(cliente, fcm, titulo, cuerpo, datos)
    except Exception:
        pass
