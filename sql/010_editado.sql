-- Marca de mensaje editado. Ejecutar en el SQL Editor de Supabase.

alter table mensajes add column editado boolean not null default false;
