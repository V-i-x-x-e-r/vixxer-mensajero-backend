-- Id de cliente para envíos idempotentes (evita duplicados por reintento o por gateway BLE).
-- Ejecutar en el SQL Editor de Supabase.

alter table mensajes add column if not exists cliente_id text;

create unique index if not exists mensajes_cliente_id_key
  on mensajes (cliente_id)
  where cliente_id is not null;
