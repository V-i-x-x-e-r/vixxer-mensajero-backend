from fastapi import APIRouter, HTTPException, Depends, Request

from app.schemas.auth import RegistroIn, LoginIn, CambiarContrasenaIn
from app.core.security import hashear_password, verificar_password, crear_token
from app.core.codigo import generar_codigo
from app.core.deps import usuario_actual
from app.core.limites import permitido
from app.db import usuarios as repo

router = APIRouter(prefix="/auth", tags=["auth"])


def _ip(request: Request) -> str:
    reenviado = request.headers.get("x-forwarded-for")
    if reenviado:
        partes = [p.strip() for p in reenviado.split(",") if p.strip()]
        if partes:
            return partes[-1]
    return request.client.host if request.client else "?"


@router.post("/register", status_code=201)
def register(datos: RegistroIn, request: Request):
    if not permitido(f"register:{_ip(request)}", maximo=5, ventana=3600):
        raise HTTPException(status_code=429, detail="Demasiados intentos, espera un momento")
    if repo.buscar_por_usuario(datos.usuario):
        raise HTTPException(status_code=409, detail="Ese usuario ya existe")
    codigo = generar_codigo()
    while repo.buscar_por_codigo(codigo):
        codigo = generar_codigo()
    nuevo_usuario = {
        "usuario": datos.usuario,
        "clave_hash": hashear_password(datos.contrasena),
        "llave_publica": datos.llave_publica,
        "llave_firma": datos.llave_firma,
        "codigo": codigo,
    }
    if datos.respaldo is not None:
        nuevo_usuario.update({
            "respaldo_cifrado": datos.respaldo.cifrado,
            "respaldo_nonce": datos.respaldo.nonce,
            "respaldo_salt": datos.respaldo.salt,
        })
    nuevo = repo.crear(nuevo_usuario)
    return {"id": nuevo["id"], "usuario": nuevo["usuario"], "codigo": codigo}


@router.post("/login")
def login(datos: LoginIn, request: Request):
    if not permitido(f"login:{_ip(request)}", maximo=20, ventana=900) or not permitido(f"login:{datos.usuario.lower()}", maximo=10, ventana=900):
        raise HTTPException(status_code=429, detail="Demasiados intentos, espera un momento")
    user = repo.buscar_por_usuario(datos.usuario)
    if not user or not verificar_password(datos.contrasena, user["clave_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = crear_token(user["id"])
    return {"token": token, "usuario": {"id": user["id"], "usuario": user["usuario"]}}


@router.post("/cambiar-contrasena")
def cambiar_contrasena(datos: CambiarContrasenaIn, yo: str = Depends(usuario_actual)):
    if not permitido(f"cambiar:{yo}", maximo=5, ventana=900):
        raise HTTPException(status_code=429, detail="Demasiados intentos, espera un momento")
    user = repo.buscar_por_id(yo)
    if not user or not verificar_password(datos.actual, user["clave_hash"]):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    repo.actualizar(yo, {"clave_hash": hashear_password(datos.nueva)})
    return {"ok": True}


@router.get("/me")
def me(yo: str = Depends(usuario_actual)):
    return {"user_id": yo}
