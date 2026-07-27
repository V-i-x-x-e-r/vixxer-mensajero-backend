# Vixxer Mensajero — backend

FastAPI + socket.io sobre Supabase. Guarda blobs cifrados; nunca ve el
contenido de un mensaje.

## Estilo

- PEP8 limpio, nombres en español como el resto del proyecto.
- **Sin comentarios.** El nombre de la función cuenta la historia.
- Funciones cortas, con un solo trabajo.
- Repo público: ningún secreto ni dato interno en el código.

## Antes de dar algo por terminado

```
python -m pytest tests/ -q
python -c "from app.main import asgi"
```

Ambos corren solos en CI. El segundo atrapa errores de arranque que ningún
test unitario ve.

## Reglas que no se rompen

- **El cliente de Supabase es SÍNCRONO.** Cualquier llamada bloqueante dentro
  de un handler `async` congela el event loop entero y con él a todos los
  usuarios conectados. Va envuelta en `core.asincrono.en_hilo`.
- Todo endpoint que reciba algo del cliente valida tamaño y forma antes de
  confiar. El cuerpo entero está acotado por `core.cuerpo.LimiteCuerpo`, pero
  eso es la última red, no la primera.
- Las migraciones de `sql/` son aditivas y se aplican en Supabase **antes** de
  desplegar el código que las usa. Ese paso lo hace César, no yo.

## Entorno

`Settings` exige `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `JWT_SECRET`.
En local salen del `.env` (no versionado); en CI se pasan valores ficticios.
Sin ellas, importar cualquier router falla.

Python 3.14, igual que el servidor.

## Despliegue

Mergear a `develop` despliega solo en ~60 s: el servidor de casa es un clon
git y un timer de systemd revisa cada minuto. Ver con
`journalctl -t vixxer-deploy`. Si `pip install` falla, aborta antes de
reiniciar y el proceso viejo sigue sirviendo.

La rama por defecto del repo es `main`, no `develop`. Importa porque las
tareas programadas de GitHub corren desde la rama por defecto.

`requirements.txt` no tiene versiones fijadas: hoy una publicación upstream
puede tumbar el backend sin que nadie toque el código.
