<div align="center">

# Vixxer Mensajero — Backend

**API y servidor de tiempo real para Vixxer Mensajero.**

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Framework](https://img.shields.io/badge/framework-FastAPI-009688)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## Sobre el proyecto

Backend de **Vixxer Mensajero**: autenticación, usuarios y mensajería cifrada en tiempo real. El cliente vive en [`vixxer-mensajero-mobile`](https://github.com/V-i-x-x-e-r/vixxer-mensajero-mobile).

**Stack:** Python 3.12+ · FastAPI · python-socketio · PostgreSQL (Supabase) · JWT.

### Principios

- **Cero PII innecesaria:** sin teléfono, CURP, nombre real ni email obligatorio.
- **Cero conocimiento del contenido:** el servidor solo enruta mensajes cifrados, no los puede leer.

---

## Este repo está intencionalmente casi vacío

No hay código todavía **a propósito**. En Vixxer aprendemos construyendo: la estructura
de carpetas y archivos la creas **tú**, siguiendo tu guía.

> **Empieza por tu guía personal** en `vixxer-docs` → `guias/` (abre `index.html`).
> Ahí está el qué, el porqué, el dónde y en qué orden construir.

La dupla de backend es **César + Ricardo**. Se revisan entre ustedes por Pull Request.

---

## Arranque rápido (cuando ya tengas tu estructura)

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar dependencias (tú creas requirements.txt)
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env             # llena los valores reales

# 4. Levantar el servidor en desarrollo (ejemplo con FastAPI)
uvicorn app.main:app --reload --port 8000
```

> El nombre del módulo (`app.main:app`) depende de cómo organices tu proyecto. Tu guía lo explica.

---

## Variables de entorno

Ver [`.env.example`](.env.example). Nunca subas el `.env` real.

## Base de datos

El esquema inicial de Supabase vive en [`sql/001_esquema_inicial.sql`](sql/001_esquema_inicial.sql).
En Semana 1, César y Paola lo ejecutan desde el SQL Editor de Supabase.

---

## Equipo

Backend: César Servín González · Ricardo Uriel Sierra Lira.
Documentación y guías: [`vixxer-docs`](https://github.com/V-i-x-x-e-r/vixxer-docs).

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
