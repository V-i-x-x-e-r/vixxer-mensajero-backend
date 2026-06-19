import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.sockets.server import sio
from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router

app = FastAPI(title="Vixxer Mensajero API")

# CORS: permite que clientes web (la página de prueba, el front) llamen a la API.
# Sin esto, un fetch desde file:// o desde otro origen falla con "Failed to fetch".
# Usamos credentials=False porque el token va en el body/header, no en cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(usuarios_router, prefix="/api")

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
