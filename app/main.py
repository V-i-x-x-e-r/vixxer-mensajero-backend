import socketio
from fastapi import FastAPI

from app.sockets.server import sio
from app.routers.auth import router as auth_router

app = FastAPI(title="Vixxer Mensajero API")

app.include_router(auth_router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "0.1.0"}

@app.get("/db-ping")
def db_ping():
    from app.db.usuarios import buscar_por_usuario
    return {"ok": buscar_por_usuario("nadie") is None}

# Envuelve FastAPI + Socket.IO en una sola app ASGI.
# Se levanta con:  uvicorn app.main:asgi --reload
asgi = socketio.ASGIApp(sio, other_asgi_app=app)
