-- Vixxer Mensajero - Esquema inicial de Supabase
-- Ejecutar en Supabase SQL Editor durante la Semana 1.

create table usuarios
(
    id              uuid primary key default gen_random_uuid(),
    usuario         text unique not null,
    clave_hash      text not null,
    llave_publica   text not null,
    ultima_conexion timestamptz,
    creado_en       timestamptz default now()
);

create table mensajes
(
    id                uuid primary key default gen_random_uuid(),
    remitente_id      uuid references usuarios(id),
    destinatario_id   uuid references usuarios(id),
    contenido_cifrado text not null,    -- blob opaco; el server NO lo entiende
    nonce             text not null,
    enviado_en        timestamptz default now(),
    entregado_en      timestamptz,
    leido_en          timestamptz
);

create index idx_mensajes_conversacion
  on public.mensajes (remitente_id, destinatario_id, enviado_en);
