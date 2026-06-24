from fastapi import APIRouter, HTTPException, Depends

from app.schemas.auth import RegistroIn, LoginIn
from app.core.security import hashear_password, verificar_password, crear_token
from app.core.deps import usuario_actual
from app.db import usuarios as repo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(datos: RegistroIn):
    if repo.buscar_por_usuario(datos.usuario):
        raise HTTPException(status_code=409, detail="Ese usuario ya existe")
    nuevo = repo.crear({
        "usuario": datos.usuario,
        "clave_hash": hashear_password(datos.contrasena),
        "llave_publica": datos.llave_publica,
    })
    return {"id": nuevo["id"], "usuario": nuevo["usuario"]}


@router.post("/login")
def login(datos: LoginIn):
    user = repo.buscar_por_usuario(datos.usuario)
    if not user or not verificar_password(datos.contrasena, user["clave_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = crear_token(user["id"])
    return {"token": token, "usuario": {"id": user["id"], "usuario": user["usuario"]}}


@router.get("/me")
def me(yo: str = Depends(usuario_actual)):
    return {"user_id": yo}
