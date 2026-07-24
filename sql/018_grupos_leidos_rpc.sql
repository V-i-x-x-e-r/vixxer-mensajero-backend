-- Marca leidos de grupo en un solo viaje: fusiona el usuario dentro de leido_por
-- de todos los mensajes indicados con un unico UPDATE en vez de uno por mensaje.
-- Ejecutar en el SQL Editor de Supabase despues de 017.

create or replace function marcar_leidos_grupo(
  p_grupo_id uuid,
  p_usuario_id uuid,
  p_ids uuid[],
  p_ahora text
)
returns table (id uuid, leido_por jsonb)
language sql
as $$
  update mensajes_grupo m
  set leido_por = coalesce(m.leido_por, '{}'::jsonb)
                  || jsonb_build_object(p_usuario_id::text, p_ahora)
  where m.grupo_id = p_grupo_id
    and m.id = any(p_ids)
    and m.remitente_id <> p_usuario_id
    and not (coalesce(m.leido_por, '{}'::jsonb) ? p_usuario_id::text)
  returning m.id, m.leido_por;
$$;
