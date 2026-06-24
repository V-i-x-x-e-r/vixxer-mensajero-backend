-- Codigo de amigo: identificador aleatorio para agregar contactos sin exponer el usuario.
-- Ejecutar en el SQL Editor de Supabase.

alter table usuarios add column codigo text unique;

create index idx_usuarios_codigo on public.usuarios (codigo);
