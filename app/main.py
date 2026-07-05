import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.sockets.server import sio
from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.mensajes import router as mensajes_router
from app.routers.amigos import router as amigos_router
from app.routers.media import router as media_router
from app.routers.grupos import router as grupos_router

app = FastAPI(title="Vixxer Mensajero API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(usuarios_router, prefix="/api")
app.include_router(mensajes_router, prefix="/api")
app.include_router(amigos_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(grupos_router, prefix="/api")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version")
def version():
    return {"version": "0.2.0"}


asgi = socketio.ASGIApp(sio, other_asgi_app=app)
