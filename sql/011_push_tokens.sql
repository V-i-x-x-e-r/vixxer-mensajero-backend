-- Tokens de notificaciones push por dispositivo. Ejecutar en el SQL Editor de Supabase.

create table if not exists push_tokens (
  token text primary key,
  user_id uuid not null references usuarios(id) on delete cascade,
  plataforma text,
  creado_en timestamptz not null default now()
);

create index if not exists push_tokens_user_id_idx on push_tokens (user_id);
