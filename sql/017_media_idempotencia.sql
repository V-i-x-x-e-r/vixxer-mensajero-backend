-- Subida binaria del cliente nativo y alcance correcto de la idempotencia.
-- Ejecutar en el SQL Editor de Supabase después de 016.

drop index if exists mensajes_cliente_id_key;

create unique index if not exists mensajes_remitente_cliente_id_key
  on mensajes (remitente_id, cliente_id)
  where cliente_id is not null;

drop index if exists mensajes_grupo_cliente_id_key;

create unique index if not exists mensajes_grupo_remitente_cliente_id_key
  on mensajes_grupo (grupo_id, remitente_id, cliente_id)
  where cliente_id is not null;
