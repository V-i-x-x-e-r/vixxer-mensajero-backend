-- Reacciones por mensaje. Ejecutar en el SQL Editor de Supabase.
-- Mapa usuario_id -> emoji (una reaccion por persona por mensaje).

alter table mensajes add column reacciones jsonb not null default '{}'::jsonb;
