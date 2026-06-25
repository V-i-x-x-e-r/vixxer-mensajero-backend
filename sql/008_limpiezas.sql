-- Borrar conversacion solo para mi. Ejecutar en el SQL Editor de Supabase.
-- Guarda hasta cuando limpio cada usuario su conversacion con otro;
-- los mensajes anteriores se ocultan solo para ese usuario.

create table limpiezas (
  usuario_id  uuid not null references usuarios(id),
  otro_id     uuid not null references usuarios(id),
  limpiado_en timestamptz not null default now(),
  primary key (usuario_id, otro_id)
);
