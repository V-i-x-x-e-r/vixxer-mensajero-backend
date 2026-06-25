-- Responder a un mensaje. Ejecutar en el SQL Editor de Supabase.
-- Solo guarda el id del mensaje citado (no contenido): seguro para E2EE.

alter table mensajes add column respuesta_a uuid references mensajes(id);
