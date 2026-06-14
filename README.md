<div align="center">

# Vixxer Mensajero — Backend

**API REST y servidor Socket.IO para Vixxer Mensajero.**

![Status](https://img.shields.io/badge/status-en%20desarrollo-yellow)
![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Node](https://img.shields.io/badge/node-%3E%3D20-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Sprint](https://img.shields.io/badge/sprint-0-orange)

</div>

---

## Tabla de contenidos

- [Sobre el proyecto](#sobre-el-proyecto)
- [Stack técnico](#stack-técnico)
- [Estado del proyecto y roadmap](#estado-del-proyecto-y-roadmap)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Scripts disponibles](#scripts-disponibles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [API REST](#api-rest)
- [Eventos Socket.IO](#eventos-socketio)
- [Modelo de datos](#modelo-de-datos)
- [Deploy](#deploy)
- [Flujo de trabajo (Gitflow)](#flujo-de-trabajo-gitflow)
- [Convenciones](#convenciones)
- [Equipo](#equipo)
- [Licencia](#licencia)

---

## Sobre el proyecto

Backend de **Vixxer Mensajero**. Provee autenticación, persistencia de usuarios y mensajes cifrados, y comunicación bidireccional en tiempo real vía Socket.IO. El cliente vive en [`vixxer-mensajero-mobile`](https://github.com/V-i-x-x-e-r/vixxer-mensajero-mobile).

### Principios de diseño

- **Cero PII innecesaria:** no se solicita ni almacena teléfono, CURP, nombre real ni email obligatorio.
- **Cero conocimiento del contenido:** el servidor solo enruta mensajes cifrados, no los puede leer.
- **Stateless donde sea posible:** sesión por JWT, no por server-side sessions.

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Runtime | Node.js 20+ |
| Framework | Express |
| Tiempo real | Socket.IO |
| Base de datos | PostgreSQL (Supabase) |
| Auth | JWT + bcrypt |
| Validación | Zod |
| Logging | Pino |
| Tests | Jest + Supertest |
| Deploy | Railway |

---

## Estado del proyecto y roadmap

**Versión actual:** `0.1.0` (Sprint 0 — Setup)

| Versión | Sprint | Funcionalidad | Estado |
|---|---|---|---|
| 0.1.0 | Sprint 0 | Setup, scaffolding de Express | En curso |
| 0.2.0 | Sprint 1 | Conexión a Supabase, healthcheck | Pendiente |
| 0.3.0 | Sprint 2 | Endpoints de auth (register/login) | Pendiente |
| 0.4.0 | Sprint 3 | Socket.IO + envío de mensajes | Pendiente |
| 0.5.0 | Sprint 4 | Almacenamiento de mensajes cifrados + intercambio de keys públicas | Pendiente |
| 0.6.0 | Sprint 5 | Rate limiting, validaciones, hardening | Pendiente |
| **1.0.0** | Sprint 6 | **Deploy a producción + release** | Pendiente |

---

## Requisitos previos

- **Node.js** 20 o superior
- **npm** 10+
- **Git**
- Cuenta gratuita en [Supabase](https://supabase.com)
- (Opcional) [Postman](https://www.postman.com/) o [Insomnia](https://insomnia.rest/) para probar endpoints

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/V-i-x-x-e-r/vixxer-mensajero-backend.git
cd vixxer-mensajero-backend

# 2. Cambiar a la rama de integración
git checkout develop

# 3. Instalar dependencias
npm install

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales (ver siguiente sección)

# 5. Correr migraciones de base de datos
npm run db:migrate

# 6. Iniciar en modo desarrollo (con hot reload)
npm run dev
```

El servidor corre por defecto en `http://localhost:3000`.

Para verificar que está funcionando:

```bash
curl http://localhost:3000/health
# {"status":"ok","timestamp":"..."}
```

---

## Variables de entorno

Revisa [`.env.example`](.env.example) para la lista completa.

| Variable | Descripción | Default |
|---|---|---|
| `PORT` | Puerto del servidor | `3000` |
| `NODE_ENV` | Entorno (`development`, `production`) | `development` |
| `SUPABASE_URL` | URL de tu proyecto en Supabase | — |
| `SUPABASE_ANON_KEY` | Clave anónima de Supabase | — |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio (privada) | — |
| `JWT_SECRET` | Secreto para firmar tokens JWT | — |
| `JWT_EXPIRES_IN` | Duración de los tokens | `7d` |
| `CORS_ORIGIN` | Orígenes permitidos (separados por coma) | — |
| `LOG_LEVEL` | Nivel de logs (`debug`, `info`, `warn`, `error`) | `info` |

> **Importante:** nunca subas el archivo `.env` real al repositorio. Solo `.env.example` con valores placeholder.

### Cómo generar un JWT_SECRET seguro

```bash
# En Linux/Mac
openssl rand -base64 64

# En Windows (PowerShell)
[Convert]::ToBase64String((1..64 | ForEach-Object {Get-Random -Maximum 256}))
```

---

## Scripts disponibles

| Comando | Descripción |
|---|---|
| `npm run dev` | Inicia el servidor con hot reload (nodemon) |
| `npm start` | Inicia el servidor en modo producción |
| `npm run db:migrate` | Aplica migraciones de base de datos |
| `npm run db:seed` | Carga datos de prueba |
| `npm run lint` | Corre el linter (ESLint) |
| `npm run format` | Formatea el código con Prettier |
| `npm test` | Corre los tests con Jest |
| `npm run test:watch` | Tests en modo watch |

---

## Estructura del proyecto

```
vixxer-mensajero-backend/
├── .github/
│   └── pull_request_template.md
├── src/
│   ├── config/                   # Configuración (env, supabase, logger)
│   ├── routes/                   # Definición de endpoints
│   ├── controllers/              # Lógica de cada ruta
│   ├── middlewares/              # Auth, validación, error handling, CORS
│   ├── models/                   # Acceso a datos (Supabase)
│   ├── sockets/                  # Handlers de Socket.IO
│   ├── services/                 # Lógica de negocio
│   ├── validators/               # Esquemas Zod
│   ├── utils/                    # Helpers (crypto, dates, etc.)
│   └── server.js                 # Entry point
├── tests/                        # Tests unitarios y de integración
├── migrations/                   # SQL migrations
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

---

## API REST

> **Base URL:** `http://localhost:3000/api`

### Autenticación

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/auth/register` | Registro sin CURP/teléfono | No |
| POST | `/auth/login` | Login con username/password | No |
| POST | `/auth/logout` | Cerrar sesión | Sí |
| GET | `/auth/me` | Datos del usuario autenticado | Sí |

### Usuarios

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/users/search?q=...` | Buscar usuarios por username | Sí |
| GET | `/users/:id/public-key` | Obtener clave pública de un usuario | Sí |
| PATCH | `/users/me` | Actualizar perfil propio | Sí |

### Mensajes

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/messages/:userId` | Historial con otro usuario | Sí |
| DELETE | `/messages/:id` | Eliminar mensaje propio | Sí |

### Salud

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck del servidor |

---

## Eventos Socket.IO

> Los clientes deben autenticarse con JWT al conectarse (vía `auth` en el handshake).

### Cliente → Servidor

| Evento | Payload | Descripción |
|---|---|---|
| `message:send` | `{ recipientId, encryptedContent, nonce }` | Enviar mensaje cifrado |
| `message:read` | `{ messageId }` | Marcar como leído |
| `typing:start` | `{ recipientId }` | Indicar que está escribiendo |
| `typing:stop` | `{ recipientId }` | Dejar de indicar |

### Servidor → Cliente

| Evento | Payload | Descripción |
|---|---|---|
| `message:received` | `{ messageId, senderId, encryptedContent, nonce, timestamp }` | Nuevo mensaje |
| `message:delivered` | `{ messageId }` | Confirmación de entrega |
| `message:read` | `{ messageId }` | Confirmación de lectura |
| `user:online` | `{ userId }` | Usuario se conectó |
| `user:offline` | `{ userId, lastSeen }` | Usuario se desconectó |
| `typing:start` | `{ userId }` | Otro usuario está escribiendo |
| `typing:stop` | `{ userId }` | Otro usuario dejó de escribir |

---

## Modelo de datos

### Tabla `users`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | uuid | Identificador único |
| `username` | text | Nombre de usuario único (3-20 caracteres) |
| `password_hash` | text | Hash bcrypt de la contraseña |
| `public_key` | text | Clave pública para E2EE |
| `created_at` | timestamptz | Fecha de creación |
| `last_seen` | timestamptz | Última conexión |

### Tabla `messages`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | uuid | Identificador único |
| `sender_id` | uuid | FK a `users.id` |
| `recipient_id` | uuid | FK a `users.id` |
| `encrypted_content` | text | Contenido cifrado (base64) |
| `nonce` | text | Nonce de cifrado (base64) |
| `created_at` | timestamptz | Fecha de envío |
| `delivered_at` | timestamptz | Fecha de entrega |
| `read_at` | timestamptz | Fecha de lectura |

---

## Deploy

El backend se despliega en **Railway**. Cada push a `main` dispara un deploy automático.

```bash
# Build local para verificar
npm run build

# Probar la build de producción
NODE_ENV=production npm start
```

### Configuración en Railway

1. Conectar el repo desde el dashboard de Railway
2. Configurar las variables de entorno (mismas que `.env`, pero con valores de producción)
3. Railway detecta automáticamente que es Node.js y corre `npm start`

---

## Flujo de trabajo (Gitflow)

Mismo flujo que el cliente. Resumen:

- `main` → releases estables
- `develop` → integración
- `feature/*`, `fix/*`, `hotfix/*`, `release/*` → ramas temporales

Documentación completa en [`vixxer-docs/gitflow.md`](https://github.com/V-i-x-x-e-r/vixxer-docs).

---

## Convenciones

### Conventional Commits

```
feat(auth): implementar endpoint de registro
fix(socket): manejar desconexion abrupta
docs(api): documentar endpoint de mensajes
refactor(db): extraer queries a modelo de mensaje
```

### Estilo de código

- 2 espacios de indentación
- Comillas simples
- Punto y coma al final
- ESLint + Prettier configurados
- Imports ordenados: node modules → internos → relativos

---

## Equipo

| Rol | Nombre | Área |
|---|---|---|
| Captain / Backend | César Servín González | Arquitectura, infra, PO |
| Backend | Ricardo Uriel Sierra Lira | API + Socket.IO |
| Frontend | Paola Ornelas Galván | Cliente móvil |
| Frontend | Raúl Leyva Carral | Cliente móvil |

---

## Licencia

MIT. Ver [`LICENSE`](LICENSE) para más detalles.

---

<div align="center">

**Vixxer Mensajero Backend** — Hecho por estudiantes de la Universidad de Guanajuato.

</div>