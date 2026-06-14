-- ============================================================
-- Vixxer Mensajero — Migración inicial
-- Ejecuta esto en: Supabase Dashboard > SQL Editor > New query
-- ============================================================
-- Principio: cero PII. No guardamos teléfono, email, CURP ni nombre real.
-- El servidor solo guarda blobs cifrados que NO puede leer.
-- ============================================================

create extension if not exists "pgcrypto";

-- ---------- Tabla de usuarios ----------
create table if not exists public.users (
  id            uuid primary key default gen_random_uuid(),
  username      text not null unique check (char_length(username) between 3 and 20),
  password_hash text not null,
  public_key    text not null,                 -- clave pública E2EE (base64), NO la privada
  created_at    timestamptz not null default now(),
  last_seen     timestamptz
);

create index if not exists users_username_idx on public.users (lower(username));

-- ---------- Tabla de mensajes ----------
create table if not exists public.messages (
  id                uuid primary key default gen_random_uuid(),
  sender_id         uuid not null references public.users (id) on delete cascade,
  recipient_id      uuid not null references public.users (id) on delete cascade,
  encrypted_content text not null,             -- ciphertext base64 (servidor NO lo entiende)
  nonce             text not null,             -- nonce base64
  created_at        timestamptz not null default now(),
  delivered_at      timestamptz,
  read_at           timestamptz
);

create index if not exists messages_pair_idx
  on public.messages (sender_id, recipient_id, created_at);
create index if not exists messages_recipient_idx
  on public.messages (recipient_id, created_at);

-- ---------- Row Level Security ----------
-- El backend usa la SERVICE_ROLE key (bypassea RLS), pero dejamos RLS activo
-- por defensa en profundidad: si alguien filtra la ANON key, no lee nada.
alter table public.users enable row level security;
alter table public.messages enable row level security;

-- Sin políticas permisivas = nadie con la anon key puede leer/escribir directo.
-- Todo el acceso pasa por el backend autenticado con service_role.
