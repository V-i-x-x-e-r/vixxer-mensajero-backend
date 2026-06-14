-- Vixxer Mensajero - esquema inicial de Supabase
-- Ejecutar en Supabase SQL Editor durante la Semana 1.

create table public.usuarios (
  id uuid primary key default gen_random_uuid(),
  usuario text unique not null,
  clave_hash text not null,
  llave_publica text not null,
  creado_en timestamptz not null default now(),
  ultima_conexion timestamptz
);

create table public.mensajes (
  id uuid primary key default gen_random_uuid(),
  remitente_id uuid not null references public.usuarios(id) on delete cascade,
  destinatario_id uuid not null references public.usuarios(id) on delete cascade,
  contenido_cifrado text not null,
  nonce text not null,
  enviado_en timestamptz not null default now(),
  entregado_en timestamptz,
  leido_en timestamptz
);

create index idx_mensajes_conversacion
  on public.mensajes (remitente_id, destinatario_id, enviado_en);
